import time
from enum import Enum
from typing import Optional

from bilibili_api.audio import Audio
from bilibili_api.favorite_list import FavoriteList
from bilibili_api.video import Video
from pydantic import BaseModel, ValidationError
from pyrogram.types import Message

from defs.bilibili import credential, create_video, create_audio
from defs.bilibili_download import (
    go_download,
    go_upload,
    audio_download,
    gen_video_caption,
    gen_audio_caption,
)
from defs.glover import bilifav_id, bilifav_channel
from models.models.bilifav import BiliFav
from models.services.bilifav import BiliFavAction
from init import logger, bot

fav = FavoriteList(media_id=bilifav_id, credential=credential)


class BilibiliFavException(Exception):
    pass


class MediaType(int, Enum):
    video = 2
    audio = 12


class Media(BaseModel):
    id: int
    bvid: str
    type: MediaType
    title: str
    cover: Optional[str]
    """ 封面 """
    intro: Optional[str]
    """ 简介 """


async def process_video_from_cache(video: Video, video_db: BiliFav):
    info = await video.get_info()
    caption = gen_video_caption(video, info)
    msg = await bot.send_video(
        bilifav_channel,
        video_db.file_id,
        caption=caption,
    )
    video_db.message_id = msg.id
    video_db.timestamp = int(time.time())
    await BiliFavAction.update_bili_fav(video_db)


async def process_video(data: Media, m: Message):
    """处理视频"""
    video = create_video(data.bvid)
    if video_db := await BiliFavAction.get_by_bv_id(data.bvid):
        await process_video_from_cache(video, video_db)
        return
    await go_download(video, 0, m, task=False)
    msg = await go_upload(video, 0, m, push_id=bilifav_channel)
    if not msg:
        raise BilibiliFavException


async def process_audio_from_cache(audio: Audio, audio_db: BiliFav):
    info = await audio.get_info()
    caption = gen_audio_caption(audio, info)
    msg = await bot.send_audio(
        bilifav_channel,
        audio_db.file_id,
        caption=caption,
    )
    audio_db.message_id = msg.id
    audio_db.timestamp = int(time.time())
    await BiliFavAction.update_bili_fav(audio_db)


async def process_audio(data: Media, m: Message):
    """处理音频"""
    audio = create_audio(f"au{data.id}")
    if audio_db := await BiliFavAction.get_by_bv_id(data.bvid):
        await process_audio_from_cache(audio, audio_db)
        return
    msg = await audio_download(audio, m, push_id=bilifav_channel)
    if not msg:
        raise BilibiliFavException


async def check_update(m: Message):
    """检查收藏夹是否更新"""
    logger.info("Check bilibili favorite list")
    try:
        info = await fav.get_content()
    except Exception as e:
        logger.exception("Check bilibili favorite list failed")
        await m.edit(f"获取收藏夹信息失败：{e}")
        return
    for media in info.get("medias", [])[::-1]:
        try:
            data = Media(**media)
        except ValidationError as _:
            logger.exception("Validate media failed")
            continue
        if await BiliFavAction.get_by_bv_id(data.bvid, fav=True):
            continue
        if await BiliFavAction.get_by_id(data.id, fav=True):
            continue
        n = await m.reply(f"处理 {data.type.name} {data.bvid} 中...")
        try:
            if data.type == MediaType.video:
                await process_video(data, n)
            elif data.type == MediaType.audio:
                await process_audio(data, n)
        except BilibiliFavException:
            continue
    await m.edit("收藏夹数据获取完毕")
    logger.info("Check bilibili favorite list success")
