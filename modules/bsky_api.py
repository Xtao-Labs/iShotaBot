import contextlib
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel
from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType, ChatType
from pyrogram.types import Message

from defs.bsky import Timeline
from init import bot


class Reply(BaseModel):
    cid: int
    mid: Optional[int] = None


async def process_url(url: str, reply: Reply, override_hidden: bool):
    url = urlparse(url)
    if url.hostname and url.hostname in ["bsky.app"]:
        if url.path.find("profile") < 0:
            return
        author_handle = str(url.path[url.path.find("profile") + 8 :].split("/")[0])
        if url.path.find("post") >= 0:
            status_id = str(url.path[url.path.find("post") + 5 :].split("/")[0]).split(
                "?"
            )[0]
            try:
                post = await Timeline.fetch_post(author_handle, status_id)
                await Timeline.send_to_user(reply, post, override_hidden)
            except Exception as e:
                print(e)
        elif url.path == f"/profile/{author_handle}":
            # 解析用户
            try:
                user = await Timeline.fetch_user(author_handle)
                await Timeline.send_user(reply, user)
            except Exception as e:
                print(e)


@bot.on_message(filters.incoming & filters.text & filters.regex(r"bsky.app/"))
async def bsky_share(_: Client, message: Message):
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
    if text.startswith("~"):
        return
    override_hidden = False
    if "no" in text or "不隐藏" in text:
        override_hidden = True
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
        await process_url(url, reply, override_hidden)
    raise ContinuePropagation
