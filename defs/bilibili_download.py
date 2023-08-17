import contextlib
import os
import time
from asyncio import create_subprocess_shell, subprocess, Lock
from typing import Tuple, Dict, Union

import aiofiles
from bilibili_api import HEADERS
from bilibili_api.video import Video, VideoDownloadURLDataDetecter, VideoQuality
from httpx import AsyncClient, Response
from pyrogram.types import Message

from defs.request import cache_dir
from init import bot, logger

FFMPEG_PATH = "ffmpeg"
LOCK = Lock()
EDIT_TEMP_SECONDS = 10.0
MESSAGE_MAP: Dict[int, float] = {}
UPLOAD_MESSAGE_MAP: Dict[int, int] = {}


class BilibiliDownloaderError(Exception):
    """Bilibili 下载器错误"""

    MSG = "Bilibili 下载器错误"

    def __init__(self, msg: str = None):
        self.MSG = msg or self.MSG


class FileTooBig(BilibiliDownloaderError):
    """文件过大，超过2GB"""

    MSG = "文件过大，超过2GB"


class FileNoSize(BilibiliDownloaderError):
    """文件大小未知"""

    MSG = "文件大小未知"


class FFmpegError(BilibiliDownloaderError):
    """FFmpeg 转换失败"""

    MSG = "FFmpeg 转换失败"


def should_edit(m: Message) -> bool:
    if m.id in MESSAGE_MAP:
        last_time = MESSAGE_MAP[m.id]
        if last_time + EDIT_TEMP_SECONDS < time.time():
            return True
    else:
        return True
    return False


def format_bytes(size: Union[int, float]) -> str:
    """格式化文件大小"""
    power = 1024
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    if n > 4:
        n = 4
    return f"{round(size, 2)} {power_labels[n]}B"


def format_seconds(seconds: Union[int, float]) -> str:
    """格式化秒数"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    s = round(s, 2)
    text = ""
    if h > 0:
        text += f" {h} 小时"
    if m > 0:
        text += f" {m} 分钟"
    if s > 0:
        text += f" {s} 秒"
    return text.strip()


async def safe_edit(m: Message, text: str):
    try:
        await m.edit_text(text)
    except Exception:
        pass


async def fail_edit(m: Message, text: str):
    try:
        await m.edit_text(text)
    except Exception:
        with contextlib.suppress(Exception):
            await m.reply(text, quote=True)


async def execute(command: str) -> Tuple[str, int]:
    process = await create_subprocess_shell(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    try:
        result = str(stdout.decode().strip()) + str(stderr.decode().strip())
    except UnicodeDecodeError:
        result = str(stdout.decode("gbk").strip()) + str(stderr.decode("gbk").strip())
    return result, process.returncode


def safe_remove(path: str):
    if os.path.exists(path):
        os.remove(path)


async def message_edit(
    length: int,
    total_downloaded: int,
    temp_downloaded: int,
    chunk_time: float,
    m: Message,
    t: str,
):
    speed = temp_downloaded / (chunk_time if chunk_time > 0 else 1)
    text = (
        f"{t}进度\n\n"
        f"{format_bytes(total_downloaded)} / {format_bytes(length)} "
        f"({round(total_downloaded / length * 100.0, 2)}%)\n\n"
        f"传输区间速度：{format_bytes(speed)}/s\n"
        f"预计剩余时间：{format_seconds((length - total_downloaded) / speed)}"
    )
    await safe_edit(m, text)


async def download_url(url: str, out: str, m: Message, start: str):
    async with AsyncClient(headers=HEADERS, timeout=60) as sess:
        async with sess.stream("GET", url) as resp:
            logger.info(f"Downloading {start}")
            resp: Response
            length = resp.headers.get("content-length")
            if not length:
                raise FileNoSize
            length = int(length)
            if length > 1.9 * 1024 * 1024 * 1024:
                raise FileTooBig
            total_downloaded = 0
            temp_downloaded = 0
            MESSAGE_MAP[m.id] = time.time() - EDIT_TEMP_SECONDS
            async with aiofiles.open(out, "wb") as f:
                async for chunk in resp.aiter_bytes(1024):
                    if not chunk:
                        break
                    chunk_len = len(chunk)
                    total_downloaded += chunk_len
                    temp_downloaded += chunk_len
                    async with LOCK:
                        _should_edit = should_edit(m)
                        if _should_edit:
                            now = time.time()
                            chunk_time = now - MESSAGE_MAP[m.id]
                            MESSAGE_MAP[m.id] = now
                    if _should_edit:
                        bot.loop.create_task(
                            message_edit(
                                length,
                                total_downloaded,
                                temp_downloaded,
                                chunk_time,
                                m,
                                f"{start}下载",
                            )
                        )
                        temp_downloaded = 0
                    await f.write(chunk)


async def go_download(v: Video, p_num: int, m: Message):
    video_path = cache_dir / f"{v.get_aid()}_{p_num}.mp4"
    safe_remove(video_path)
    flv_temp_path = cache_dir / f"{v.get_aid()}_{p_num}_temp.flv"
    video_temp_path = cache_dir / f"{v.get_aid()}_{p_num}_video.m4s"
    audio_temp_path = cache_dir / f"{v.get_aid()}_{p_num}_audio.m4s"
    # 有 MP4 流 / FLV 流两种可能
    try:
        # 获取视频下载链接
        download_url_data = await v.get_download_url(p_num)
        # 解析视频下载信息
        detector = VideoDownloadURLDataDetecter(data=download_url_data)
        streams = detector.detect_best_streams(
            video_max_quality=VideoQuality._1080P_60,  # noqa
        )
        if not streams:
            raise BilibiliDownloaderError("无法获取下载链接")
        if detector.check_flv_stream():
            # FLV 流下载
            await download_url(streams[0].url, flv_temp_path, m, "视频 FLV ")
            # 转换文件格式
            _, result = await execute(f"{FFMPEG_PATH} -i {flv_temp_path} {video_path}")
        else:
            if len(streams) < 2:
                raise BilibiliDownloaderError("获取下载链接异常")
            # MP4 流下载
            await download_url(streams[0].url, video_temp_path, m, "视频 m4s ")
            await download_url(streams[1].url, audio_temp_path, m, "音频 m4s ")
            # 混流
            logger.info("Merging video and audio")
            _, result = await execute(
                f'{FFMPEG_PATH} -i "{video_temp_path}" -i "{audio_temp_path}" '
                f"-c:v copy -c:a copy -strict experimental "
                f'-y "{video_path}"'
            )
        if result != 0:
            raise FFmpegError
        bot.loop.create_task(go_upload(v, p_num, m))
    except BilibiliDownloaderError as e:
        await fail_edit(m, e.MSG)
    except Exception as e:
        logger.exception("Downloading video failed")
        await fail_edit(m, f"下载失败：{e}")
    finally:
        # 删除临时文件
        safe_remove(flv_temp_path)
        safe_remove(video_temp_path)
        safe_remove(audio_temp_path)


async def go_upload_progress(current: int, total: int, m: Message):
    if current == 0:
        return
    async with LOCK:
        _should_edit = should_edit(m)
        if _should_edit:
            now = time.time()
            chunk_time = now - MESSAGE_MAP[m.id]
            MESSAGE_MAP[m.id] = now
    if _should_edit:
        t = UPLOAD_MESSAGE_MAP[m.id] if m.id in UPLOAD_MESSAGE_MAP else 0
        UPLOAD_MESSAGE_MAP[m.id] = current
        chunk = current - t
        chunk = chunk if chunk > 0 else 0
        await message_edit(total, current, chunk, chunk_time, m, "上传")


async def go_upload(v: Video, p_num: int, m: Message):
    video_path = cache_dir / f"{v.get_aid()}_{p_num}.mp4"
    if not video_path.exists():
        await fail_edit(m, "视频文件不存在")
        return
    try:
        logger.info(f"Uploading {video_path}")
        await bot.send_video(
            chat_id=m.chat.id,
            video=str(video_path),
            supports_streaming=True,
            progress=go_upload_progress,
            progress_args=(m,),
        )
        logger.info(f"Upload {video_path} success")
    except Exception as e:
        logger.exception("Uploading video failed")
        await fail_edit(m, f"上传失败：{e}")
        return
    finally:
        safe_remove(video_path)
        if m.id in MESSAGE_MAP:
            del MESSAGE_MAP[m.id]
        if m.id in UPLOAD_MESSAGE_MAP:
            del UPLOAD_MESSAGE_MAP[m.id]
    with contextlib.suppress(Exception):
        await m.delete()
