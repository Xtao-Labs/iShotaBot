from typing import Optional, List

from pyrogram.enums import ParseMode
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaAnimation,
)

from init import logs
from models.apis.fxtwitter.client import fix_twitter_client, FixTwitterError
from models.apis.fxtwitter.model import User, FixTweet, FixTweetMedia


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


def twitter_media(tweet_media_lists: List[FixTweetMedia], text: str):
    media_lists = []
    for idx, media in enumerate(tweet_media_lists):
        if len(media_lists) > 10:
            break
        if media.type == "photo":
            media_lists.append(
                InputMediaPhoto(
                    media.media_url,
                    caption=text if idx == 0 else None,
                    parse_mode=ParseMode.HTML,
                )
            )
        elif media.type == "gif":
            media_lists.append(
                InputMediaAnimation(
                    media.media_url,
                    caption=text if idx == 0 else None,
                    parse_mode=ParseMode.HTML,
                )
            )
        else:
            media_lists.append(
                InputMediaVideo(
                    media.media_url,
                    caption=text if idx == 0 else None,
                    parse_mode=ParseMode.HTML,
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
    final_text = "<b>Twitter Status Info</b>\n\n" f"{text}\n\n"
    if tweet.retweet_or_quoted:
        roq = tweet.retweet_or_quoted
        final_text += (
            f'<code>RT: {roq.text or "暂 无 内 容"}</code>\n\n'
            f'{roq.author.one_line} 发表于 {roq.created.strftime("%Y-%m-%d %H:%M:%S")}'
            f"\n👁 {roq.views}  👍 {roq.likes}   🔁 {roq.retweets}\n"
            f'{tweet.author.one_line} 转于 {tweet.created.strftime("%Y-%m-%d %H:%M:%S")}\n'
            f"👁 {tweet.views}  👍 {tweet.likes}   🔁 {tweet.retweets}"
        )
    else:
        final_text += (
            f'{tweet.author.one_line} 发表于 {tweet.created.strftime("%Y-%m-%d %H:%M:%S")}'
            f"\n👁 {tweet.views}  👍 {tweet.likes}   🔁 {tweet.retweets}"
        )
    return final_text


async def fetch_tweet(tweet_id: int) -> Optional[FixTweet]:
    try:
        return await fix_twitter_client.tweet_detail(tweet_id)
    except FixTwitterError as e:
        logs.error(f"Twitter Error: {e}")
        return None


async def fetch_user(username: str) -> Optional[User]:
    try:
        user = await fix_twitter_client.user_by_screen_name(username)
    except FixTwitterError as e:
        logs.error(f"Twitter Error: {e}")
        return None
    return user
