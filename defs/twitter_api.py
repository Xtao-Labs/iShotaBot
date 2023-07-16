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
from models.apis.twitter.client import twitter_client, TwitterError
from models.apis.twitter.model import User, Tweet, MediaItem


def twitter_link(tweet: Tweet):
    origin = tweet.retweet_or_quoted
    button = [
        [
            InlineKeyboardButton(
                text="Source",
                url=tweet.url,
            ),
            InlineKeyboardButton(text="Author", url=tweet.user.url),
        ]
    ]
    if origin:
        button[0].insert(1, InlineKeyboardButton(text="RSource", url=origin.url))
    return InlineKeyboardMarkup(button)


def twitter_user_link(user: User):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Author", url=user.url)]])


def twitter_medias(tweet: Tweet):
    tweet_media_lists = []
    if tweet.extended_entities:
        tweet_media_lists.extend(tweet.extended_entities.media)
    if tweet.retweet and tweet.retweet.extended_entities:
        tweet_media_lists.extend(tweet.retweet.extended_entities.media)
    if tweet.quoted and tweet.quoted.extended_entities:
        tweet_media_lists.extend(tweet.quoted.extended_entities.media)
    return tweet_media_lists


def twitter_media(tweet_media_lists: List[MediaItem], text: str):
    media_lists = []
    for idx, media in enumerate(tweet_media_lists):
        if len(media_lists) >= 10:
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
    verified = "💎" if user.verified else ""
    protected = "🔒" if user.protected else ""
    text = (
        f"<b>Twitter User Info</b>\n\n"
        f"Name: {verified}{protected}<code>{user_name}</code>\n"
        f'Username: <a href="https://twitter.com/{user_username}">@{user_username}</a>\n'
        f"Bio: <code>{user.description}</code>\n"
        f"Joined: <code>{user.created.strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
        f"📤 {user.statuses_count} ❤️{user.favourites_count} "
        f"粉丝 {user.followers_count} 关注 {user.friends_count}"
    )
    return text


def get_twitter_status(tweet: Tweet):
    text = tweet.full_text or "暂 无 内 容"
    text = f"<code>{text}</code>"
    final_text = "<b>Twitter Status Info</b>\n\n" f"{text}\n\n"
    if tweet.retweet_or_quoted:
        roq = tweet.retweet_or_quoted
        final_text += (
            f'<code>RT: {roq.full_text or "暂 无 内 容"}</code>\n\n'
            f'{roq.user.one_line} 发表于 {roq.created.strftime("%Y-%m-%d %H:%M:%S")}'
            f"\n👍 {roq.favorite_count}   🔁 {roq.retweet_count}\n"
            f'{tweet.user.one_line} 转于 {tweet.created.strftime("%Y-%m-%d %H:%M:%S")}\n'
            f"👍 {tweet.favorite_count}   🔁 {tweet.retweet_count}"
        )
    else:
        final_text += (
            f'{tweet.user.one_line} 发表于 {tweet.created.strftime("%Y-%m-%d %H:%M:%S")}'
            f"\n👍 {tweet.favorite_count}   🔁 {tweet.retweet_count}"
        )
    return final_text


async def fetch_tweet(tweet_id: int) -> Optional[Tweet]:
    try:
        tweet = await twitter_client.tweet_detail(tweet_id)
        for t in tweet:
            if t.id_str == str(tweet_id):
                return t
        return tweet[0]
    except TwitterError as e:
        logs.error(f"Twitter Error: {e}")
        return None


async def fetch_user(username: str) -> Optional[User]:
    try:
        user = await twitter_client.user_by_screen_name(username)
    except TwitterError as e:
        logs.error(f"Twitter Error: {e}")
        return None
    return user
