import re

from pyrogram import filters, Client, ContinuePropagation
from pyrogram.types import Message, CallbackQuery

from defs.bilibili import b23_extract, create_video, create_audio
from defs.bilibili_download import go_download, audio_download
from defs.glover import bili_auth_user, bilifav_channel_username, bili_auth_chat
from init import bot
from models.services.bilifav import BiliFavAction


@bot.on_message(
    filters.incoming
    & filters.text
    & (filters.user(bili_auth_user) | filters.chat(bili_auth_chat))
    & filters.command(["download"])
)
async def bili_download_resolve(_: Client, message: Message):
    if "b23.tv" in message.text:
        message.text = await b23_extract(message.text)
    p = re.compile(r"av(\d{1,12})|BV(\w{10})|b23.tv")
    video_number = p.search(message.text)
    if video_number:
        video_number = video_number[0]
    else:
        await message.reply("未找到视频 BV 号或 AV 号")
        raise ContinuePropagation
    p_ = re.compile(r"p=(\d{1,3})")
    p_num = p_.search(message.text)
    p_num = int(p_num[0][2:]) if p_num else 0
    video = create_video(video_number)
    if video_db := await BiliFavAction.get_by_bv_id(video.get_bvid()):
        await message.reply_video(
            video_db.file_id,
            caption=f"详细信息：https://t.me/{bilifav_channel_username}/{video_db.message_id}"
            if video_db.message_id
            else None,
            quote=True,
        )
        raise ContinuePropagation
    m = await message.reply("开始获取视频数据", quote=True)
    bot.loop.create_task(go_download(video, p_num, m))


@bot.on_message(filters.incoming & filters.text & filters.regex(r"audio/au(\d{1,12})"))
async def bili_audio_download_resolve(_: Client, message: Message):
    p = re.compile(r"au(\d{1,12})")
    audio_number = p.search(message.text)
    if audio_number:
        audio_number = audio_number[0]
    else:
        raise ContinuePropagation
    audio = create_audio(audio_number)
    if audio_db := await BiliFavAction.get_by_id(audio.get_auid()):
        await message.reply_audio(
            audio_db.file_id,
            caption=f"详细信息：https://t.me/{bilifav_channel_username}/{audio_db.message_id}"
            if audio_db.message_id
            else None,
            quote=True,
        )
        raise ContinuePropagation
    m = await message.reply("开始获取音频数据", quote=True)
    bot.loop.create_task(audio_download(audio, m))


@bot.on_callback_query(filters.regex(r"^download_(.*)$"))
async def bili_download_resolve_cb(_: Client, callback_query: CallbackQuery):
    if not callback_query.from_user:
        await callback_query.answer("请私聊机器人")
        return
    if (
        callback_query.message.chat.id not in bili_auth_chat
        and callback_query.from_user.id not in bili_auth_user
    ):
        await callback_query.answer("你没有权限")
        return
    video_number = callback_query.matches[0].group(1)
    video = create_video(video_number)
    if video_db := await BiliFavAction.get_by_bv_id(video.get_bvid()):
        await callback_query.answer("找到缓存")
        caption = (
            f"详细信息：https://t.me/{bilifav_channel_username}/{video_db.message_id}"
            if video_db.message_id
            else None
        )
        await callback_query.message.reply_video(
            video_db.file_id,
            caption=caption,
            quote=True,
        )
        raise ContinuePropagation
    m = await callback_query.message.reply("开始获取视频数据", quote=True)
    bot.loop.create_task(go_download(video, 0, m))
    await callback_query.answer("开始下载")
