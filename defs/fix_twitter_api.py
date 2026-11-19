from urllib.parse import urlparse

from pydantic import BaseModel
from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    ReplyParameters,
)

from defs.media_cache import get_media_stream, get_media_streams
from init import bot, logs
from models.apis.fxtwitter.client import FixTwitterError, fix_twitter_client
from models.apis.fxtwitter.model import FixTweet, FixTweetMedia, User


def twitter_link(tweet: FixTweet):
    origin = tweet.retweet_or_quoted
    button = [
        [
            InlineKeyboardButton(
                text="Source",
                url=tweet.url,
            ),
            InlineKeyboardButton(text="Author", url=tweet.author.url),
        ]
    ]
    if origin:
        button[0].insert(1, InlineKeyboardButton(text="RSource", url=origin.url))
    return InlineKeyboardMarkup(button)


def twitter_user_link(user: User):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Author", url=user.url)]])


def twitter_medias(tweet: FixTweet):
    tweet_media_lists = []
    if tweet.medias:
        tweet_media_lists.extend(tweet.medias)
    if tweet.retweet_or_quoted:
        tweet_media_lists.extend(tweet.retweet_or_quoted.medias)
    return tweet_media_lists


async def twitter_media(tweet_media_lists: list[FixTweetMedia], text: str):
    selected = tweet_media_lists[:10]
    urls: list[str] = []
    for media in selected:
        if media.type in ("photo", "video", "gif"):
            urls.append(media.url)
            if media.type in ("video", "gif") and media.thumbnail_url:
                urls.append(media.thumbnail_url)
    unique_urls = list(dict.fromkeys(urls))
    streams = dict(zip(unique_urls, await get_media_streams(unique_urls)))

    media_lists = []
    for idx, media in enumerate(selected):
        if media.type == "photo":
            media_lists.append(
                InputMediaPhoto(
                    streams[media.url],
                    caption=text if idx == 0 else "",
                    parse_mode=ParseMode.HTML,
                )
            )
        elif media.type == "gif":
            media_lists.append(
                InputMediaDocument(
                    streams[media.url],
                    caption=text if idx == 0 else "",
                    parse_mode=ParseMode.HTML,
                )
            )
        elif media.type == "video" or media.type == "gif":
            thumb = streams.get(media.thumbnail_url) if media.thumbnail_url else None
            media_lists.append(
                InputMediaVideo(
                    streams[media.url],
                    video_cover=thumb,
                    duration=int(media.duration),
                    caption=text if idx == 0 else "",
                    parse_mode=ParseMode.HTML,
                    width=media.width,
                    height=media.height,
                )
            )
    return media_lists


def get_twitter_user(user: User):
    user_name = user.name
    user_username = user.screen_name
    text = (
        f"<b>Twitter User Info</b>\n\n"
        f"Name: <code>{user_name}</code>\n"
        f'Username: <a href="https://twitter.com/{user_username}">@{user_username}</a>\n'
        f"Bio: <code>{user.description}</code>\n"
        f"Joined: <code>{user.created.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
        f"📤 {user.tweets} ❤️{user.likes} "
        f"粉丝 {user.followers} 关注 {user.following}"
    )
    return text


def get_twitter_status(tweet: FixTweet):
    text = tweet.text or "暂 无 内 容"
    text = f"<code>{text}</code>"
    final_text = f"<b>Twitter Status Info</b>\n\n{text}\n\n"
    if tweet.retweet_or_quoted:
        roq = tweet.retweet_or_quoted
        final_text += (
            f"<code>RT: {roq.text or '暂 无 内 容'}</code>\n\n"
            f"{roq.author.one_line} 发表于 {roq.created.strftime('%Y-%m-%d %H:%M:%S')}"
            f"\n👁 {roq.views}  👍 {roq.likes}   🔁 {roq.reposts}\n"
            f"{tweet.author.one_line} 转于 {tweet.created.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"👁 {tweet.views}  👍 {tweet.likes}   🔁 {tweet.reposts}"
        )
    else:
        final_text += (
            f"{tweet.author.one_line} 发表于 {tweet.created.strftime('%Y-%m-%d %H:%M:%S')}"
            f"\n👁 {tweet.views}  👍 {tweet.likes}   🔁 {tweet.reposts}"
        )
    return final_text


async def fetch_tweet(tweet_id: int) -> FixTweet | None:
    try:
        return await fix_twitter_client.tweet_detail(tweet_id)
    except FixTwitterError as e:
        logs.error(f"Twitter Error: {e}")
        return None


async def fetch_user(username: str) -> User | None:
    try:
        user = await fix_twitter_client.user_by_screen_name(username)
    except FixTwitterError as e:
        logs.error(f"Twitter Error: {e}")
        return None
    return user


class Reply(BaseModel):
    cid: int
    mid: int | None = None


async def send_single_tweet(reply: Reply, media: FixTweetMedia, text: str, button):
    stream = await get_media_stream(media.url)
    if media.type == "photo":
        await bot.send_photo(
            reply.cid,
            stream,
            caption=text,
            reply_markup=button,
            reply_parameters=ReplyParameters(message_id=reply.mid),
        )
    elif media.type == "video":
        thumb = (
            await get_media_stream(media.thumbnail_url) if media.thumbnail_url else None
        )
        await bot.send_video(
            reply.cid,
            stream,
            thumb=thumb,
            caption=text,
            reply_markup=button,
            reply_parameters=ReplyParameters(message_id=reply.mid),
            width=media.width,
            height=media.height,
        )
    elif media.type == "gif":
        await bot.send_animation(
            reply.cid,
            stream,
            caption=text,
            reply_markup=button,
            reply_parameters=ReplyParameters(message_id=reply.mid),
        )
    else:
        await bot.reply_document(
            reply.cid,
            stream,
            caption=text,
            reply_markup=button,
            reply_parameters=ReplyParameters(message_id=reply.mid),
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
    media_lists = await twitter_media(medias, text)
    if media_lists:
        await bot.send_media_group(
            reply.cid,
            media_lists,
            reply_parameters=ReplyParameters(message_id=reply.mid),
        )
    else:
        await bot.send_message(
            reply.cid,
            text,
            reply_parameters=ReplyParameters(message_id=reply.mid),
            reply_markup=button,
        )


async def process_user(reply: Reply, username: str):
    user = await fetch_user(username)
    if not user:
        return
    text = get_twitter_user(user)
    button = twitter_user_link(user)
    stream = await get_media_stream(user.icon)
    await bot.send_photo(
        reply.cid,
        stream,
        caption=text,
        reply_markup=button,
        reply_parameters=ReplyParameters(message_id=reply.mid),
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
