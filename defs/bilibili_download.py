import contextlib
import os
import time
from asyncio import create_subprocess_shell, subprocess, Lock
from io import BytesIO
from typing import Tuple, Dict, Union, Optional

import aiofiles
from bilibili_api import HEADERS
from bilibili_api.audio import Audio
from bilibili_api.video import Video, VideoDownloadURLDataDetecter, VideoQuality
from httpx import AsyncClient, Response
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from defs.request import cache_dir
from init import bot, logger, request
from models.models.bilifav import BiliFav
from models.services.bilifav import BiliFavAction

FFMPEG_PATH = "ffmpeg"
FFPROBE_PATH = "ffprobe"
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
            if resp.status_code != 200:
                raise BilibiliDownloaderError("下载链接异常，请尝试重新下载")
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


async def get_video_duration(path: str) -> float:
    """获取视频时长"""
    video_duration, code = await execute(
        f"{FFPROBE_PATH} -v error -select_streams v:0 -show_entries format=duration "
        f"-of default=noprint_wrappers=1:nokey=1 {path}"
    )
    if code != 0:
        raise FFmpegError("视频时长获取失败")
    return round(float(video_duration.split("[")[0].strip()), 2)


async def get_video_height_width(path: str) -> Tuple[int, int]:
    """获取视频高度和宽度"""
    result, code = await execute(
        f"{FFPROBE_PATH} -v error -select_streams v:0 -show_entries stream=width,height "
        f"-of csv=s=x:p=0 {path}"
    )
    if code != 0:
        raise FFmpegError("视频宽高度获取失败")
    video_width, video_height = result.split("[")[0].split("x")
    return int(video_height), int(video_width)


async def take_screenshot(info: Dict) -> Optional[BytesIO]:
    """获取视频封面"""
    try:
        pic_get = (await request.get(info["pic"])).content
        pic = BytesIO(pic_get)
        pic.name = "screenshot.jpg"
        return pic
    except Exception:
        logger.exception("获取视频封面失败")
        return None


def gen_audio_caption(a: Audio, info: Dict) -> str:
    intro = info.get("intro", "")
    if intro:
        text = f"<b>{info['title']}</b>\n\n{intro}\n\nhttps://www.bilibili.com/audio/au{a.get_auid()}"
        if len(text) > 800:
            text = f"<b>{info['title']}</b>\n\n简介过长，无法显示\n\nhttps://www.bilibili.com/audio/au{a.get_auid()}"
    else:
        text = (
            f"<b>{info['title']}</b>\n\nhttps://www.bilibili.com/audio/au{a.get_auid()}"
        )
    return text


async def audio_download(
    a: Audio, m: Message, push_id: int = None
) -> Optional[Message]:
    try:
        info = await a.get_info()
        download_url_data = await a.get_download_url()
        async with AsyncClient(headers=HEADERS, timeout=60) as client:
            r = await client.get(download_url_data["cdns"][0])
            media = BytesIO(r.content)
            ext = download_url_data["cdns"][0].split("?")[0].split(".")[-1]
            if ext:
                media.name = f"{info['title']}.{ext}"
            else:
                media.name = f"{info['title']}.mp3"
            media.seek(0)
            if info.get("cover"):
                r_ = await client.get(info.get("cover"))
                thumb = BytesIO(r_.content)
                thumb.seek(0)
            else:
                thumb = None
        caption = gen_audio_caption(a, info)
        msg = await bot.send_audio(
            chat_id=push_id or m.chat.id,
            audio=media,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=m.reply_to_message_id if not push_id else None,
            thumb=thumb,
            title=info.get("title"),
            duration=info.get("duration"),
            performer=info.get("author"),
        )
        if info.get("id") and (not await BiliFavAction.get_by_id(info.get("id"))):
            audio_db = BiliFav(
                id=info.get("id", 0),
                bv_id=info.get("bvid").lower(),
                type=12,
                title=info.get("title", ""),
                cover=info.get("cover", ""),
                message_id=msg.id if push_id else 0,
                file_id=msg.audio.file_id,
                timestamp=int(time.time()),
            )
            await BiliFavAction.add_bili_fav(audio_db)
    except BilibiliDownloaderError as e:
        await fail_edit(m, e.MSG)
        return
    except Exception as e:
        logger.exception("Downloading audio failed")
        await fail_edit(m, f"下载/上传失败：{e}")
        return
    with contextlib.suppress(Exception):
        await m.delete()
    return msg


async def go_download(v: Video, p_num: int, m: Message, task: bool = True):
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
            _, result = await execute(f'{FFMPEG_PATH} -i "{flv_temp_path}" "{video_path}"')
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
                f"-c:v copy -c:a copy -movflags +faststart "
                f'-y "{video_path}"'
            )
        if result != 0:
            raise FFmpegError
        if task:
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


def gen_video_caption(v: Video, info: Dict) -> str:
    caption = (
        f"<b>{info['title']}</b>\n\n{info['desc']}\n\nhttps://b23.tv/{v.get_bvid()}"
    )
    if len(caption) > 800:
        caption = (
            f"<b>{info['title']}</b>\n\n简介过长，无法显示\n\nhttps://b23.tv/{v.get_bvid()}"
        )
    return caption


async def go_upload(
    v: Video, p_num: int, m: Message, push_id: int = None
) -> Optional[Message]:
    video_path = cache_dir / f"{v.get_aid()}_{p_num}.mp4"
    if not video_path.exists():
        await fail_edit(m, "视频文件不存在")
        return
    try:
        video_duration = await get_video_duration(video_path)
        video_height, video_width = await get_video_height_width(video_path)
        try:
            info = await v.get_info()
            video_jpg = await take_screenshot(info)
            caption = gen_video_caption(v, info)
        except Exception:
            info = None
            video_jpg = None
            caption = f"https://b23.tv/{v.get_bvid()}"
        logger.info(f"Uploading {video_path}")
        msg = await bot.send_video(
            chat_id=push_id or m.chat.id,
            video=str(video_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            duration=int(video_duration),
            width=video_width,
            height=video_height,
            thumb=video_jpg,
            supports_streaming=True,
            progress=go_upload_progress,
            progress_args=(m,),
            reply_to_message_id=m.reply_to_message_id if not push_id else None,
        )
        if (
            (not await BiliFavAction.get_by_bv_id(v.get_bvid()))
            and info is not None
            and info.get("aid")
        ):
            video_db = BiliFav(
                id=info.get("aid", 0),
                bv_id=info.get("bvid").lower(),
                type=2,
                title=info.get("title", ""),
                cover=info.get("pic", ""),
                message_id=msg.id if push_id else 0,
                file_id=msg.video.file_id,
                timestamp=int(time.time()),
            )
            await BiliFavAction.add_bili_fav(video_db)
        logger.info(f"Upload {video_path} success")
    except BilibiliDownloaderError as e:
        await fail_edit(m, e.MSG)
        return
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
    return msg
