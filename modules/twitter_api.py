import contextlib
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel
from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType, ChatType
from pyrogram.types import Message

from defs.fix_twitter_api import (
    fetch_tweet,
    get_twitter_status,
    twitter_link,
    twitter_media,
    fetch_user,
    get_twitter_user,
    twitter_user_link,
    twitter_medias,
)
from init import bot
from models.apis.fxtwitter.model import FixTweetMedia


class Reply(BaseModel):
    cid: int
    mid: Optional[int] = None


async def send_single_tweet(reply: Reply, media: FixTweetMedia, text: str, button):
    if media.type == "photo":
        await bot.send_photo(
            reply.cid,
            media.url,
            caption=text,
            reply_markup=button,
            reply_to_message_id=reply.mid,
        )
    elif media.type == "video":
        await bot.send_video(
            reply.cid,
            media.url,
            caption=text,
            reply_markup=button,
            reply_to_message_id=reply.mid,
        )
    elif media.type == "gif":
        await bot.send_animation(
            reply.cid,
            media.url,
            quote=True,
            caption=text,
            reply_markup=button,
            reply_to_message_id=reply.mid,
        )
    else:
        await bot.reply_document(
            reply.cid,
            media.url,
            quote=True,
            caption=text,
            reply_markup=button,
            reply_to_message_id=reply.mid,
        )


async def process_status(reply: Reply, status: str):
    try:
        status = int(status)
    except ValueError:
        return
    tweet = await fetch_tweet(status)
    if not tweet:
        return
    text = get_twitter_status(tweet)
    button = twitter_link(tweet)
    medias = twitter_medias(tweet)
    if len(medias) == 1:
        media = medias[0]
        await send_single_tweet(reply, media, text, button)
        return
    media_lists = twitter_media(medias, text)
    if media_lists:
        await bot.send_media_group(
            reply.cid,
            media_lists,
            reply_to_message_id=reply.mid,
        )
    else:
        await bot.send_message(
            reply.cid,
            text,
            reply_markup=button,
            reply_to_message_id=reply.mid,
        )


async def process_user(reply: Reply, username: str):
    user = await fetch_user(username)
    if not user:
        return
    text = get_twitter_user(user)
    button = twitter_user_link(user)
    await bot.send_photo(
        reply.cid,
        user.icon,
        caption=text,
        reply_markup=button,
        reply_to_message_id=reply.mid,
    )


async def process_url(url: str, reply: Reply):
    url = urlparse(url)
    if url.hostname and url.hostname in [
        "twitter.com",
        "vxtwitter.com",
        "fxtwitter.com",
        "x.com",
    ]:
        if url.path.find("status") >= 0:
            status_id = str(
                url.path[url.path.find("status") + 7 :].split("/")[0]
            ).split("?")[0]
            try:
                await process_status(reply, status_id)
            except Exception as e:
                print(e)
        elif url.path == "/":
            return
        else:
            # 解析用户
            uid = url.path.replace("/", "")
            try:
                await process_user(reply, uid)
            except Exception as e:
                print(e)


@bot.on_message(filters.incoming & filters.text & filters.regex(r"twitter.com/"))
async def twitter_share(_: Client, message: Message):
    if not message.text:
        return
    if (
        message.sender_chat
        and message.forward_from_chat
        and message.sender_chat.id == message.forward_from_chat.id
    ):
        # 过滤绑定频道的转发
        return
    mid = message.id
    if message.text.startswith("del") and message.chat.type == ChatType.CHANNEL:
        with contextlib.suppress(Exception):
            await message.delete()
            mid = None
    reply = Reply(cid=message.chat.id, mid=mid)
    for num in range(len(message.entities)):
        entity = message.entities[num]
        if entity.type == MessageEntityType.URL:
            url = message.text[entity.offset : entity.offset + entity.length]
        elif entity.type == MessageEntityType.TEXT_LINK:
            url = entity.url
        else:
            continue
        await process_url(url, reply)
    raise ContinuePropagation
