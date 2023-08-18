import re
import time

from pyrogram import filters, Client, ContinuePropagation
from pyrogram.types import Message, CallbackQuery

from defs.bilibili import b23_extract, create_video, create_audio
from defs.bilibili_download import go_download, go_upload, audio_download
from defs.bilibili_fav import check_update
from defs.glover import admin, bilifav_channel
from init import bot, logger
from models.models.bilifav import BiliFav
from models.services.bilifav import BiliFavAction


async def process_audio(video_number: str, message: Message):
    id_ = int(video_number[2:])
    if await BiliFavAction.get_by_id(id_):
        await message.reply("该音频已经存在")
        raise ContinuePropagation
    audio = create_audio(video_number)
    info = await audio.get_info()
    m = await message.reply("开始获取音频数据", quote=True)
    msg = await audio_download(audio, m, push_id=bilifav_channel)
    if not msg:
        raise ContinuePropagation
    audio_db = BiliFav(
        id=id_,
        bv_id=info.get("bvid", "").lower(),
        type=12,
        title=info.get("title", ""),
        cover=info.get("cover", ""),
        message_id=msg.id,
        file_id=msg.audio.file_id,
        timestamp=int(time.time()),
    )
    await BiliFavAction.add_bili_fav(audio_db)


async def process_video(video_number: str, p_num: int, message: Message):
    video = create_video(video_number)
    if await BiliFavAction.get_by_bv_id(video.get_bvid()):
        await message.edit("该视频已经存在")
        raise ContinuePropagation
    info = await video.get_info()
    id_ = info.get("aid", 0)
    if not id_:
        await message.edit("未找到视频 AV 号")
        raise ContinuePropagation
    m = await message.reply("开始获取视频数据", quote=True)
    await go_download(video, p_num, m, task=False)
    msg = await go_upload(video, p_num, m, push_id=bilifav_channel)
    if not msg:
        raise ContinuePropagation
    audio_db = BiliFav(
        id=id_,
        bv_id=info.get("bvid", "").lower(),
        type=2,
        title=info.get("title", ""),
        cover=info.get("pic", ""),
        message_id=msg.id,
        file_id=msg.video.file_id,
        timestamp=int(time.time()),
    )
    await BiliFavAction.add_bili_fav(audio_db)


@bot.on_message(
    filters.incoming
    & filters.text
    & filters.user(admin)
    & filters.command(["bilibili_fav"])
)
async def bilibili_fav_parse(_: Client, message: Message):
    if len(message.command) <= 1:
        m = await message.reply("正在获取收藏夹数据", quote=True)
        await check_update(m)
        return
    if "b23.tv" in message.text:
        message.text = await b23_extract(message.text)
    p = re.compile(r"av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})|au(\d{1,12})")
    video_number = p.search(message.text)
    if video_number:
        video_number = video_number[0]
    else:
        await message.reply("未找到视频 BV 号、 AV 或 AU 号")
        raise ContinuePropagation
    p_ = re.compile(r"p=(\d{1,3})")
    p_num = p_.search(message.text)
    p_num = int(p_num[0][2:]) if p_num else 0
    m = await message.reply("开始获取数据", quote=True)
    try:
        if video_number.startswith("au"):
            await process_audio(video_number, m)
        else:
            await process_video(video_number, p_num, m)
    except ContinuePropagation:
        raise ContinuePropagation
    except Exception as e:
        logger.exception("Processing bilibili favorite single push failed")
        await m.edit(f"处理失败: {e}")
    await m.edit("处理完成")
    raise ContinuePropagation
