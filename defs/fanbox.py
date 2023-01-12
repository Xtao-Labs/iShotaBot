import re
from typing import Tuple, Optional, Union

from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from headers import FANBOX_HEADERS
from models.apis.fanbox import User as FanboxUser, Post as FanboxPost

from init import request, bot


FANBOX_USER_API = "https://api.fanbox.cc/creator.get"
FANBOX_POST_API = "https://api.fanbox.cc/post.info"


async def get_fanbox_user(username: str) -> FanboxUser:
    params = {
        "creatorId": username,
    }
    req = await request.get(FANBOX_USER_API, params=params, headers=FANBOX_HEADERS)
    assert req.status_code == 200
    return FanboxUser(**(req.json()["body"]))


async def get_fanbox_post(post_id: str) -> FanboxPost:
    params = {
        "postId": post_id,
    }
    req = await request.get(FANBOX_POST_API, params=params, headers=FANBOX_HEADERS)
    assert req.status_code == 200
    return FanboxPost(**(req.json()["body"]))


def parse_username_and_post(url: str) -> Tuple[Optional[str], Optional[str]]:
    # https://www.fanbox.cc/@username/posts/post_id
    username, post_id = None, None
    if username_temp := re.findall(r"fanbox.cc/@(.+?)/", url):
        username = username_temp[0]
    elif username_temp := re.findall(r"//(.+?).fanbox.cc", url):
        if username_temp[0] != "www":
            username = username_temp[0]
    for i in url.split("/posts/")[1:]:
        if post_id_temp := re.findall(r"(\d+)", i):
            post_id = post_id_temp[0]
            break
    return username, post_id


async def check_kemono_party(model: Union[FanboxPost, FanboxUser]) -> bool:
    req = await request.get(model.kemono_url)
    return req.status_code == 200


async def gen_post_button(post: FanboxPost) -> InlineKeyboardMarkup:
    l1 = [
        InlineKeyboardButton(text="Source", url=post.url),
        InlineKeyboardButton(text="Author", url=post.user_url),
    ]
    if post.coverImageUrl:
        l1.insert(1, InlineKeyboardButton(text="Origin", url=post.coverImageUrl))
    l2 = [
        InlineKeyboardButton(text="Kemono", url=post.kemono_url),
    ]
    data = [l1, l2] if await check_kemono_party(post) else [l1]
    return InlineKeyboardMarkup(data)


async def gen_user_button(user: FanboxUser) -> InlineKeyboardMarkup:
    l1 = [
        InlineKeyboardButton(text="Author", url=user.url),
    ]
    if user.coverImageUrl:
        l1.insert(0, InlineKeyboardButton(text="Origin", url=user.coverImageUrl))
    l2 = [
        InlineKeyboardButton(text="Kemono", url=user.kemono_url),
    ]
    data = [l1, l2] if await check_kemono_party(user) else [l1]
    return InlineKeyboardMarkup(data)


async def parse_fanbox_post(url: str, message: Message):
    _, post_id = parse_username_and_post(url)
    if not post_id:
        return
    try:
        post: FanboxPost = await get_fanbox_post(post_id)
    except AssertionError:
        return
    if post.coverImageUrl:
        group = message.chat.type == ChatType.SUPERGROUP
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=post.coverImageUrl,
            caption=post.text,
            parse_mode=ParseMode.HTML,
            reply_markup=await gen_post_button(post),
            reply_to_message_id=message.id,
            has_spoiler=group,
        )
    else:
        await message.reply_text(
            post.text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=await gen_post_button(post),
            quote=True,
        )


async def parse_fanbox_user(url: str, message: Message) -> None:
    username, _ = parse_username_and_post(url)
    if not username:
        return
    try:
        user: FanboxUser = await get_fanbox_user(username)
    except AssertionError:
        return
    if user.coverImageUrl:
        group = message.chat.type == ChatType.SUPERGROUP
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=user.coverImageUrl,
            caption=user.text,
            parse_mode=ParseMode.HTML,
            reply_markup=await gen_user_button(user),
            reply_to_message_id=message.id,
            has_spoiler=group and user.hasAdultContent,
        )
    else:
        await message.reply_text(
            user.text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=await gen_user_button(user),
            quote=True,
        )


async def parse_fanbox_url(url: str, message: Message) -> None:
    if "/posts/" in url:
        await parse_fanbox_post(url, message)
    else:
        await parse_fanbox_user(url, message)
