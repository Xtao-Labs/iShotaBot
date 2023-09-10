from urllib.parse import urlparse

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType
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


async def send_single_tweet(message: Message, media: FixTweetMedia, text: str, button):
    if media.type == "photo":
        await message.reply_photo(
            media.url,
            quote=True,
            caption=text,
            reply_markup=button,
        )
    elif media.type == "video":
        await message.reply_video(
            media.url,
            quote=True,
            caption=text,
            reply_markup=button,
        )
    elif media.type == "gif":
        await message.reply_animation(
            media.url,
            quote=True,
            caption=text,
            reply_markup=button,
        )
    else:
        await message.reply_document(
            media.url,
            quote=True,
            caption=text,
            reply_markup=button,
        )


async def process_status(message: Message, status: str):
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
        await send_single_tweet(message, media, text, button)
        return
    media_lists = twitter_media(medias, text)
    if media_lists:
        await message.reply_media_group(media_lists, quote=True)
    else:
        await message.reply(text, quote=True, reply_markup=button)


async def process_user(message: Message, username: str):
    user = await fetch_user(username)
    if not user:
        return
    text = get_twitter_user(user)
    button = twitter_user_link(user)
    await message.reply_photo(
        user.icon,
        caption=text,
        quote=True,
        reply_markup=button,
    )


async def process_url(url: str, message: Message):
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
                await process_status(message, status_id)
            except Exception as e:
                print(e)
        elif url.path == "/":
            return
        else:
            # 解析用户
            uid = url.path.replace("/", "")
            try:
                await process_user(message, uid)
            except Exception as e:
                print(e)


@bot.on_message(filters.incoming & filters.text & filters.regex(r"twitter.com/"))
async def twitter_share(_: Client, message: Message):
    if not message.text:
        return
    for num in range(len(message.entities)):
        entity = message.entities[num]
        if entity.type == MessageEntityType.URL:
            url = message.text[entity.offset : entity.offset + entity.length]
        elif entity.type == MessageEntityType.TEXT_LINK:
            url = entity.url
        else:
            continue
        await process_url(url, message)
    raise ContinuePropagation
