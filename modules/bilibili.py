import re
from io import BytesIO

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message

from defs.bilibili import (
    b23_extract,
    video_info_get,
    binfo_image_create,
    get_dynamic_screenshot_pc,
    check_and_refresh_credential,
)
from defs.button import gen_button, Button
from defs.glover import bili_auth_user, bili_auth_chat
from init import bot
from scheduler import scheduler


@bot.on_message(
    filters.incoming
    & filters.text
    & filters.regex(r"av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})|b23.tv")
    & ~(
        filters.command(["download", "bilibili_fav"])
        & (filters.user(bili_auth_user) | filters.chat(bili_auth_chat))
    )
)
async def bili_resolve(_: Client, message: Message):
    """
    解析 bilibili 链接
    """
    if "b23.tv" in message.text:
        message.text = await b23_extract(message.text)
    p = re.compile(r"av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})")
    video_number = p.search(message.text)
    if video_number:
        video_number = video_number[0]
    video_info = await video_info_get(video_number) if video_number else None
    if video_info:
        image = await binfo_image_create(video_info)
        buttons = [Button(0, "Link", "https://b23.tv/" + video_info["bvid"])]
        if (message.from_user and message.from_user.id in bili_auth_user) or (
            message.chat and message.chat.id in bili_auth_chat
        ):
            buttons.append(Button(1, "Download", "download_" + video_info["bvid"]))
        await message.reply_photo(
            image,
            quote=True,
            reply_markup=gen_button(buttons),
        )
    raise ContinuePropagation


@bot.on_message(
    filters.incoming & filters.text & filters.regex(r"t.bilibili.com/([0-9]*)")
)
async def bili_dynamic(_: Client, message: Message):
    # sourcery skip: use-named-expression
    p = re.compile(r"t.bilibili.com/([0-9]*)")
    dynamic_number = p.search(message.text)
    if dynamic_number:
        dynamic_id = dynamic_number[1]
        image = await get_dynamic_screenshot_pc(dynamic_id)
        if image:
            # 将bytes结果转化为字节流
            photo = BytesIO(image)
            photo.name = "screenshot.png"
            await message.reply_photo(
                photo,
                quote=True,
                reply_markup=gen_button(
                    [Button(0, "Link", f"https://t.bilibili.com/{dynamic_id}")]
                ),
            )
    raise ContinuePropagation


@scheduler.scheduled_job("interval", hours=1, id="bili_cookie_refresh")
async def bili_cookie_refresh():
    await check_and_refresh_credential()
