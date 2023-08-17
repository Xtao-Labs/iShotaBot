import re

from pyrogram import filters, Client, ContinuePropagation
from pyrogram.types import Message

from defs.bilibili import b23_extract, video_info_get, create_video
from defs.bilibili_download import go_download
from defs.glover import bili_auth_user
from init import bot


@bot.on_message(
    filters.incoming
    & filters.private
    & filters.user(bili_auth_user)
    & filters.command(["download"])
)
async def bili_download_resolve(_: Client, message: Message):
    if "b23.tv" in message.text:
        message.text = await b23_extract(message.text)
    p = re.compile(r"av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})")
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
    m = await message.reply("开始获取视频数据", quote=True)
    bot.loop.create_task(go_download(video, p_num, m))
