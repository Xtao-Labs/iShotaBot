from urllib.parse import urlparse

from defs.whois import get_whois_info, format_whois_result

from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from init import bot


async def get_rep_text(url: str, need_format: bool = True):
    url = urlparse(url)
    if url.hostname or url.path:
        url = url.hostname or url.path
        data = await get_whois_info(url)
        if data:
            if need_format:
                return format_whois_result(data)
            else:
                return data.get("meta_data", "暂无原始信息")


async def get_rep_text_from_msg(message: Message):
    if not message:
        return
    if not message.entities:
        return
    for num in range(0, len(message.entities)):
        if message.entities[num].type is MessageEntityType.URL:
            url = message.text[
                message.entities[num].offset : message.entities[num].offset
                + message.entities[num].length
            ]
            if t := await get_rep_text(url):
                return t


@bot.on_message(
    filters.incoming & filters.command(["whois", f"whois@{bot.me.username}"])
)
async def whois_command(_: Client, message: Message):
    msg = await message.reply("正在查询中...")
    reply = message.reply_to_message
    rep_text = await get_rep_text_from_msg(reply) or ""
    text = await get_rep_text_from_msg(message) or ""
    if not text:
        url = message.text[6:]
        if t := await get_rep_text(url):
            text = t
    if rep_text == "" and text == "":
        await msg.edit("没有找到要查询的域名...")
    elif rep_text != "" and text != "":
        await msg.edit(
            f"{rep_text}\n================\n{text}", disable_web_page_preview=True
        )
    else:
        await msg.edit(f"{rep_text}{text}", disable_web_page_preview=True)


@bot.on_message(
    filters.incoming & filters.command(["whois_raw", f"whois_raw@{bot.me.username}"])
)
async def whois_raw_command(_: Client, message: Message):
    msg = await message.reply("正在查询中...")
    url = message.text[10:]
    text = None
    if t := await get_rep_text(url, need_format=False):
        text = f"<blockquote expandable>{t}</blockquote>"
    if not text:
        text = "没有找到要查询的域名..."
    await msg.edit(text, disable_web_page_preview=True)


@bot.on_inline_query(filters.regex("^whois"))
async def whois_inline(_: Client, inline_query: InlineQuery):
    url = inline_query.query[6:]
    text = await get_rep_text(url)
    results = [
        InlineQueryResultArticle(
            title="查询数据成功" if text else "查询数据失败",
            description=url,
            input_message_content=InputTextMessageContent(
                message_text=text or "没有找到要查询的域名..."
            ),
        )
    ]
    await inline_query.answer(
        results=results,
        cache_time=0,
    )
