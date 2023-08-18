import time
from enum import Enum
from typing import Optional

from bilibili_api.favorite_list import FavoriteList
from pydantic import BaseModel, ValidationError
from pyrogram.types import Message

from defs.bilibili import credential, create_video, create_audio
from defs.bilibili_download import go_download, go_upload, audio_download
from defs.glover import bilifav_id, bilifav_channel
from models.models.bilifav import BiliFav
from models.services.bilifav import BiliFavAction
from init import logger

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


async def process_video(data: Media, m: Message):
    """处理视频"""
    video = create_video(data.bvid)
    await go_download(video, 0, m, task=False)
    msg = await go_upload(video, 0, m, push_id=bilifav_channel)
    if not msg:
        raise BilibiliFavException
    video_db = BiliFav(
        id=data.id,
        bv_id=data.bvid.lower(),
        type=data.type.value,
        title=data.title,
        cover=data.cover,
        message_id=msg.id,
        file_id=msg.video.file_id,
        timestamp=int(time.time()),
    )
    await BiliFavAction.add_bili_fav(video_db)


async def process_audio(data: Media, m: Message):
    """处理音频"""
    audio = create_audio(f"au{data.id}")
    msg = await audio_download(audio, m, push_id=bilifav_channel)
    if not msg:
        raise BilibiliFavException
    audio_db = BiliFav(
        id=data.id,
        bv_id=data.bvid.lower(),
        type=data.type.value,
        title=data.title,
        cover=data.cover,
        message_id=msg.id,
        file_id=msg.audio.file_id,
        timestamp=int(time.time()),
    )
    await BiliFavAction.add_bili_fav(audio_db)


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
        if await BiliFavAction.get_by_bv_id(data.bvid):
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
