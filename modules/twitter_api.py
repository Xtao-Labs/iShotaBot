import contextlib

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType, ChatType
from pyrogram.types import Message

from defs.fix_twitter_api import Reply, process_url
from init import bot


@bot.on_message(filters.incoming & filters.text & filters.regex(r"(x|twitter).com/"))
async def twitter_share(_: Client, message: Message):
    text = message.text
    if not text:
        return
    if (
        message.sender_chat
        and message.forward_from_chat
        and message.sender_chat.id == message.forward_from_chat.id
    ):
        # 过滤绑定频道的转发
        return
    if text.startswith("~") or text.endswith("~"):
        return
    mid = message.id
    if text.startswith("del") and message.chat.type == ChatType.CHANNEL:
        with contextlib.suppress(Exception):
            await message.delete()
            mid = None
    reply = Reply(cid=message.chat.id, mid=mid)
    for num in range(len(message.entities)):
        entity = message.entities[num]
        if entity.type == MessageEntityType.URL:
            url = text[entity.offset : entity.offset + entity.length]
        elif entity.type == MessageEntityType.TEXT_LINK:
            url = entity.url
        else:
            continue
        await process_url(url, reply)
    raise ContinuePropagation
