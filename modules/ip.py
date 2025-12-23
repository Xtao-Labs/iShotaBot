from urllib.parse import urlparse

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from defs.ip import ip_info
from init import request, bot


async def get_rep_text(url: str):
    url = urlparse(url)
    if url.hostname or url.path:
        url = url.hostname or url.path
        ipinfo_json = (
            await request.get(
                "http://ip-api.com/json/"
                + url
                + "?fields=status,message,country,regionName,city,"
                "lat,lon,isp,"
                "org,as,mobile,proxy,hosting,query"
            )
        ).json()
        if ipinfo_json["status"] == "success":
            return ip_info(url, ipinfo_json)


async def get_rep_text_from_msg(message: Message):
    if not message:
        return
    if not message.entities:
        return
    for num in range(0, len(message.entities)):
        url = message.text[
            message.entities[num].offset : message.entities[num].offset
            + message.entities[num].length
        ]
        if t := await get_rep_text(url):
            return t


@bot.on_message(filters.incoming & filters.command(["ip"]))
async def ip_command(_: Client, message: Message):
    msg = await message.reply("正在查询中...")
    reply = message.reply_to_message
    rep_text = await get_rep_text_from_msg(reply) or ""
    text = await get_rep_text_from_msg(message) or ""
    if not text:
        url = message.text[4:]
        if t := await get_rep_text(url):
            text = t
    if rep_text == "" and text == "":
        await msg.edit("没有找到要查询的 ip/域名 ...")
    elif rep_text != "" and text != "":
        await msg.edit(
            f"{rep_text}\n================\n{text}", disable_web_page_preview=True
        )
    else:
        await msg.edit(f"{rep_text}{text}", disable_web_page_preview=True)


@bot.on_inline_query(filters.regex("^ip"))
async def ip_inline(_: Client, inline_query: InlineQuery):
    url = inline_query.query[3:]
    text = await get_rep_text(url)
    results = [
        InlineQueryResultArticle(
            title="查询 IP 数据成功" if text else "查询 IP 数据失败",
            description=url,
            input_message_content=InputTextMessageContent(
                message_text=text or "没有找到要查询的 ip/域名 ..."
            ),
            # reply_markup=InlineKeyboardMarkup(
            #     [[InlineKeyboardButton(text="重试", callback_data="dc")]]
            # ),
        )
    ]
    await inline_query.answer(
        results=results,
        cache_time=0,
    )
