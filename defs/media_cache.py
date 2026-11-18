"""图片 / 视频中转缓存工具（纯内存，不落盘）。

为 `defs.fix_twitter_api` 与 `defs.bsky` 提供统一的多媒体下载入口：

1. 复用 `init.py` 中已创建的 ``httpx.AsyncClient``（``request``），不引入额外 HTTP 依赖；
2. 下载结果以 ``bytes`` 形式保存在内存缓存中，并以 ``BytesIO`` 交给 pyrogram 发送，
   全程不产生任何本地文件；
3. 单个文件超过 50MB 时立即抛出 :class:`MediaTooLargeError` 并中止下载；
4. 内置请求超时、指数退避重试与统一异常封装；
5. 缓存以 URL 为键，带 TTL 与 LRU 容量上限，重复请求相同 URL 时直接命中缓存。

示例::

    from defs.media_cache import get_media_stream

    stream = await get_media_stream("https://example.com/a.jpg")
    await bot.send_photo(chat_id, stream)
"""

import asyncio
import os
import time
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import unquote, urlparse

import httpx

from init import logs, request

MAX_MEDIA_SIZE = 50 * 1024 * 1024
"""单个媒体文件允许的最大字节数（50MB）。"""

DEFAULT_TTL = 60 * 60.0
"""缓存条目默认存活时间（秒）。"""

DEFAULT_MAX_CACHE_BYTES = 256 * 1024 * 1024
"""缓存允许占用的最大内存（256MB），超出后按 LRU 淘汰。"""

DEFAULT_TIMEOUT = 60.0
"""单次 HTTP 请求的超时时间（秒）。"""

DEFAULT_MAX_ATTEMPTS = 3
"""单个文件的最大请求次数（包含首次请求）。"""

RETRY_BACKOFF = 1.0
"""首次重试前的等待时间（秒），之后按指数递增。"""

_RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

_CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/avif": ".avif",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "video/x-matroska": ".mkv",
}

_MEDIA_EXTENSIONS = frozenset(_CONTENT_TYPE_EXTENSIONS.values()) | {".jpeg", ".m4v"}


class MediaCacheError(Exception):
    """媒体中转缓存的基础异常。"""


class MediaTooLargeError(MediaCacheError):
    """媒体文件超过允许的最大大小时抛出。"""

    def __init__(self, url: str, size: int | None, max_size: int):
        self.url = url
        self.size = size
        self.max_size = max_size
        size_text = "未知" if size is None else f"{size} 字节"
        super().__init__(
            f"媒体文件过大（{size_text} > {max_size} 字节），已终止请求: {url}"
        )


class MediaFetchError(MediaCacheError):
    """媒体下载或响应解析失败时抛出。"""


class _RetryableStatusError(Exception):
    """内部使用：可重试的 HTTP 状态码。"""

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")


@dataclass(frozen=True, slots=True)
class MediaFile:
    """内存中的媒体文件快照，缓存与调用方共享同一份不可变数据。"""

    url: str
    filename: str
    content_type: str
    data: bytes

    @property
    def size(self) -> int:
        """文件字节数。"""
        return len(self.data)

    def open(self) -> BytesIO:
        """返回一个全新的内存流，可安全交给 pyrogram 使用。

        pyrogram 上传内存文件时依赖 ``.name`` 推断文件名与类型，
        因此这里为每个流单独设置名称，缓存的 ``bytes`` 本身不会被修改。
        """
        stream = BytesIO(self.data)
        stream.name = self.filename
        return stream


@dataclass(frozen=True, slots=True)
class MediaCacheInfo:
    """缓存运行状态快照，便于观察命中与内存占用情况。"""

    entries: int
    total_bytes: int
    hits: int
    misses: int
    evictions: int
    max_cache_bytes: int
    ttl: float


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    data: bytes
    filename: str
    content_type: str
    expires_at: float

    def to_media(self, url: str) -> MediaFile:
        return MediaFile(
            url=url,
            filename=self.filename,
            content_type=self.content_type,
            data=self.data,
        )


def _parse_content_length(value: str | None) -> int | None:
    """解析 Content-Length，非法或缺失时返回 None。"""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _guess_filename(url: str, content_type: str, fallback: str = "media") -> str:
    """根据 URL 与 Content-Type 推断带扩展名的文件名。"""
    path = unquote(urlparse(url).path or "")
    name = os.path.basename(path)
    stem, ext = os.path.splitext(name)
    if not stem:
        stem = fallback
    if ext.lower() not in _MEDIA_EXTENSIONS:
        ext = _CONTENT_TYPE_EXTENSIONS.get(content_type, "")
    stem = stem.replace("/", "_").replace("\\", "_")[:80] or fallback
    return f"{stem}{ext}"


class MediaCache:
    """基于 URL 的内存媒体缓存，支持 TTL、LRU 淘汰与并发去重。"""

    def __init__(
        self,
        *,
        ttl: float = DEFAULT_TTL,
        max_cache_bytes: int = DEFAULT_MAX_CACHE_BYTES,
        max_size: int = MAX_MEDIA_SIZE,
        timeout: float = DEFAULT_TIMEOUT,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ):
        self.ttl = ttl
        self.max_cache_bytes = max_cache_bytes
        self.max_size = max_size
        self.timeout = timeout
        self.max_attempts = max_attempts

        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._locks: dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()
        self._total_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def get(
        self,
        url: str,
        *,
        filename: str | None = None,
        ttl: float | None = None,
        max_size: int | None = None,
        timeout: float | None = None,
    ) -> MediaFile:
        """获取 URL 对应的媒体文件，命中缓存时不会发起网络请求。

        Args:
            url: 媒体资源地址。
            filename: 自定义文件名；默认根据 URL 与响应类型推断。
            ttl: 本次写入缓存的存活时间，默认使用实例配置。
            max_size: 单文件大小上限，默认 50MB。
            timeout: 单次请求超时时间，默认 60 秒。

        Raises:
            MediaTooLargeError: 文件超过 ``max_size``（默认 50MB）。
            MediaFetchError: 请求失败、重试耗尽或响应为空。
        """
        if not url:
            raise MediaFetchError("媒体 URL 不能为空")

        limit = self.max_size if max_size is None else max_size
        request_timeout = self.timeout if timeout is None else timeout
        cache_ttl = self.ttl if ttl is None else ttl

        # 第一次查询只做快速命中判断，未命中时先不计数，避免并发场景重复统计
        cached = await self._lookup(url, limit, count_miss=False)
        if cached is not None:
            return cached

        lock = await self._acquire_lock(url)
        try:
            async with lock:
                # 双重检查：并发请求同一 URL 时，后到者等待并直接复用结果
                cached = await self._lookup(url, limit, count_miss=True)
                if cached is not None:
                    return cached

                media = await self._download(
                    url,
                    filename=filename,
                    max_size=limit,
                    timeout=request_timeout,
                )
                await self._store(media, cache_ttl)
                return media
        finally:
            await self._release_lock(url, lock)

    async def clear(self) -> None:
        """清空缓存内容（保留正在进行的下载锁）。"""
        async with self._lock:
            self._entries.clear()
            self._total_bytes = 0

    async def info(self) -> MediaCacheInfo:
        """返回当前缓存状态快照。"""
        async with self._lock:
            return MediaCacheInfo(
                entries=len(self._entries),
                total_bytes=self._total_bytes,
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                max_cache_bytes=self.max_cache_bytes,
                ttl=self.ttl,
            )

    async def _lookup(
        self, url: str, max_size: int, *, count_miss: bool
    ) -> MediaFile | None:
        """查询缓存；命中时计数，过期条目会被移除。"""
        async with self._lock:
            entry = self._entries.get(url)
            if entry is None:
                if count_miss:
                    self._misses += 1
                return None

            if entry.expires_at <= time.monotonic():
                self._remove(url)
                if count_miss:
                    self._misses += 1
                return None

            if len(entry.data) > max_size:
                self._hits += 1
                raise MediaTooLargeError(url, len(entry.data), max_size)

            self._entries.move_to_end(url)
            self._hits += 1
            return entry.to_media(url)

    async def _store(self, media: MediaFile, ttl: float) -> None:
        """写入缓存并按总内存上限做 LRU 淘汰。"""
        if ttl <= 0:
            return

        async with self._lock:
            existing = self._entries.pop(media.url, None)
            if existing is not None:
                self._total_bytes -= len(existing.data)

            self._entries[media.url] = _CacheEntry(
                data=media.data,
                filename=media.filename,
                content_type=media.content_type,
                expires_at=time.monotonic() + ttl,
            )
            self._total_bytes += len(media.data)

            while self._total_bytes > self.max_cache_bytes and len(self._entries) > 1:
                _, evicted = self._entries.popitem(last=False)
                self._total_bytes -= len(evicted.data)
                self._evictions += 1

    def _remove(self, url: str) -> None:
        """移除指定缓存条目（调用方需持有 ``_lock``）。"""
        entry = self._entries.pop(url, None)
        if entry is not None:
            self._total_bytes -= len(entry.data)

    async def _acquire_lock(self, url: str) -> asyncio.Lock:
        """获取（或创建）URL 级别的下载锁，用于合并并发请求。"""
        async with self._lock:
            lock = self._locks.get(url)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[url] = lock
            return lock

    async def _release_lock(self, url: str, lock: asyncio.Lock) -> None:
        """下载结束后回收 URL 锁，避免字典无限增长。"""
        async with self._lock:
            if not lock.locked() and self._locks.get(url) is lock:
                del self._locks[url]

    async def _download(
        self,
        url: str,
        *,
        filename: str | None,
        max_size: int,
        timeout: float,
    ) -> MediaFile:
        """流式下载媒体内容，带超时、大小限制与指数退避重试。"""
        last_error: BaseException | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                async with request.stream(
                    "GET",
                    url,
                    timeout=timeout,
                    follow_redirects=True,
                    headers={"Accept": "image/*,video/*,*/*;q=0.8"},
                ) as response:
                    status = response.status_code
                    if status in _RETRY_STATUS_CODES:
                        raise _RetryableStatusError(status)
                    if status >= 400:
                        raise MediaFetchError(f"请求失败（HTTP {status}）: {url}")

                    declared_size = _parse_content_length(
                        response.headers.get("content-length")
                    )
                    if declared_size is not None and declared_size > max_size:
                        raise MediaTooLargeError(url, declared_size, max_size)

                    content_type = (
                        response.headers.get("content-type", "")
                        .split(";")[0]
                        .strip()
                        .lower()
                    )

                    buffer = bytearray()
                    async for chunk in response.aiter_bytes():
                        buffer.extend(chunk)
                        if len(buffer) > max_size:
                            raise MediaTooLargeError(url, len(buffer), max_size)
            except (MediaTooLargeError, MediaFetchError):
                raise
            except _RetryableStatusError as exc:
                last_error = exc
            except httpx.TransportError as exc:
                # 包含超时、连接失败、读取中断等可重试的网络异常
                last_error = exc
            except httpx.HTTPError as exc:
                raise MediaFetchError(f"请求异常: {exc}（{url}）") from exc
            else:
                if not buffer:
                    raise MediaFetchError(f"响应内容为空: {url}")
                if content_type and not content_type.startswith(("image/", "video/")):
                    logs.warning(
                        "媒体类型非图片/视频（%s），仍按二进制中转: %s",
                        content_type,
                        url,
                    )
                return MediaFile(
                    url=url,
                    filename=filename or _guess_filename(url, content_type),
                    content_type=content_type,
                    data=bytes(buffer),
                )

            if attempt < self.max_attempts:
                delay = RETRY_BACKOFF * (2 ** (attempt - 1))
                logs.warning(
                    "媒体下载失败，将在 %.1f 秒后重试（第 %d/%d 次）: %s",
                    delay,
                    attempt,
                    self.max_attempts,
                    url,
                )
                await asyncio.sleep(delay)

        raise MediaFetchError(
            f"重试 {self.max_attempts} 次后仍然失败: {url}"
        ) from last_error


media_cache = MediaCache()
"""默认的全局缓存实例。"""


async def get_media(
    url: str,
    *,
    filename: str | None = None,
    ttl: float | None = None,
    max_size: int | None = None,
    timeout: float | None = None,
) -> MediaFile:
    """统一入口：获取媒体文件（优先读取内存缓存）。

    参数与 :meth:`MediaCache.get` 一致。
    """
    return await media_cache.get(
        url,
        filename=filename,
        ttl=ttl,
        max_size=max_size,
        timeout=timeout,
    )


async def get_media_stream(
    url: str,
    *,
    filename: str | None = None,
    ttl: float | None = None,
    max_size: int | None = None,
    timeout: float | None = None,
) -> BytesIO:
    """统一入口：获取可直接交给 pyrogram 的媒体内存流。"""
    media = await get_media(
        url,
        filename=filename,
        ttl=ttl,
        max_size=max_size,
        timeout=timeout,
    )
    return media.open()


async def get_media_streams(
    urls: Sequence[str],
    *,
    ttl: float | None = None,
    max_size: int | None = None,
    timeout: float | None = None,
) -> list[BytesIO]:
    """统一入口：并发获取多个媒体流，返回顺序与传入的 ``urls`` 一致。"""
    streams = await asyncio.gather(
        *(
            get_media_stream(
                url,
                ttl=ttl,
                max_size=max_size,
                timeout=timeout,
            )
            for url in urls
        )
    )
    return list(streams)


async def media_cache_info() -> MediaCacheInfo:
    """返回全局缓存的状态快照，便于确认缓存命中情况。"""
    return await media_cache.info()


async def clear_media_cache() -> None:
    """清空全局媒体缓存。"""
    await media_cache.clear()
