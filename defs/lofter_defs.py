import contextlib

from typing import List, Tuple
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from pyrogram.types import (
    InputMediaPhoto,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaDocument,
    InputMediaAnimation,
    Message,
)

from defs.glover import lofter_channel_username
from models.services.lofter import LofterPost as LofterPostModel
from init import request

from lofter.client.lofter import LofterClient

client = LofterClient()


class LofterItem:
    def __init__(
        self,
        url,
        title: str,
        origin_url: str,
        username: str,
        name: str,
        comment: str,
        tags: List[str],
        audio_link: str = None,
    ):
        self.url = url
        self.audio_link = f"https://music.163.com/#/song?id={audio_link}"
        self.only_text = url is None
        self.file = url
        self.origin_url = origin_url
        self.post_id = origin_url.split("/post/")[1].split("?")[0]
        self.username = username
        tags_text = "".join(f"#{i} " for i in tags)
        self.text = (
            f"<b>Lofter Status Info</b>\n\n"
            f"<code>{title.strip()}</code>\n\n"
            f'✍️ <a href="https://{username}.lofter.com/">{name}</a>\n'
            f"{tags_text}\n"
            f"{comment}"
        )

    async def check_exists(self):
        if await LofterPostModel.get_by_post_id(self.post_id):
            self.text += f'\n📄 此图集已被<a href="https://t.me/{lofter_channel_username}">此频道</a>收录'

    async def reply_to(self, message: Message, static: bool = False):
        if static:
            await message.reply_document(
                self.file,
                caption=self.text,
                quote=True,
                reply_markup=lofter_link(self.url, self.origin_url, self.username),
            )
        elif self.only_text:
            await message.reply_text(
                self.text,
                quote=True,
                disable_web_page_preview=True,
                reply_markup=lofter_link(
                    self.audio_link, self.origin_url, self.username
                ),
            )
        elif self.file.endswith(".gif"):
            await message.reply_animation(
                self.file,
                caption=self.text,
                quote=True,
                reply_markup=lofter_link(self.url, self.origin_url, self.username),
            )
        else:
            await message.reply_photo(
                self.file,
                caption=self.text,
                quote=True,
                reply_markup=lofter_link(self.url, self.origin_url, self.username),
            )

    async def export(self, static: bool = False, first: bool = False):
        if static:
            return InputMediaDocument(self.file, caption=self.text if first else None)
        elif self.file.endswith(".gif"):
            return InputMediaAnimation(self.file, caption=self.text if first else None)
        else:
            return InputMediaPhoto(self.file, caption=self.text if first else None)


async def input_media(img: List[LofterItem], static: bool = False):
    return [(await img[ff].export(static, ff == 0)) for ff in range(len(img))]


def get_username_and_post_id(url: str) -> Tuple[str, str]:
    try:
        u = urlparse(url)
        username = u.hostname.split(".")[0]
        post_id = url.split("/post/")[1].split("?")[0]
    except Exception:
        username, post_id = "", ""
    return username, post_id


async def get_loft(url: str) -> List[LofterItem]:
    username, post_id = get_username_and_post_id(url)
    if not username or not post_id:
        return []
    post = await client.get_post_detail_web(username, post_id)
    user = post.blogInfo
    post_view = post.postData.postView
    comment = BeautifulSoup(post_view.digest, "lxml").getText()
    data = []
    if post_view.photoPostView:
        for p in post_view.photoPostView.photoLinks:
            data.append(
                LofterItem(
                    p.format_url,
                    post_view.title,
                    url,
                    username,
                    user.name,
                    comment,
                    post_view.tagList,
                )
            )
    if post_view.videoPostView:
        v = post_view.videoPostView.videoInfo
        data.append(
            LofterItem(
                v.url,
                post_view.title,
                url,
                username,
                user.name,
                comment,
                post_view.tagList,
            )
        )
    return data


def parse_loft_user(url: str, content: str):
    username = urlparse(url).hostname.split(".")[0]
    soup = BeautifulSoup(content, "lxml")
    name, bio, avatar = "未知用户", "", None  # noqa
    with contextlib.suppress(Exception):
        name = soup.find("title").getText().split("-")[-1].strip()
    with contextlib.suppress(Exception):
        bio = " - ".join(
            soup.find("meta", {"name": "Description"}).get("content").split(" - ")[1:]
        )
    with contextlib.suppress(Exception):
        avatar = soup.find("link", {"rel": "shortcut icon"}).get("href").split("?")[0]
    if user := soup.find("div", {"class": "selfinfo"}):
        name = user.find("h1").getText()
        bio = user.find("div", {"class": "text"}).getText()
        return username, avatar, name, bio, soup
    if user := soup.find("div", {"class": "g-hdc box"}):
        name = user.find("h1").getText()
        bio = user.find("p", {"class": "cont"}).getText()
        return username, avatar, name, bio, soup
    return username, avatar, name, bio, soup


async def get_loft_user(url: str):
    res = await request.get(url)
    assert res.status_code == 200
    username, avatar, name, bio, soup = parse_loft_user(url, res.text)
    status_link = None
    for i in soup.findAll("a"):
        url = i.get("href")
        if url and "lofter.com/post/" in url:
            status_link = url
            break
    text = (
        f"<b>Lofter User Info</b>\n\n"
        f"Name: <code>{name}</code>\n"
        f'Username: <a href="https://{username}.lofter.com">{username}</a>\n'
        f"Bio: <code{bio}</code>"
    )
    return text, avatar, username, status_link


def lofter_link(url, origin, username):
    return (
        InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="Source", url=origin),
                    InlineKeyboardButton(text="Origin", url=url),
                    InlineKeyboardButton(
                        text="Author", url=f"https://{username}.lofter.com"
                    ),
                ]
            ]
        )
        if url
        else InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="Source", url=origin),
                    InlineKeyboardButton(
                        text="Author", url=f"https://{username}.lofter.com"
                    ),
                ]
            ]
        )
    )


def lofter_user_link(username, status_link):
    return (
        InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Author", url=f"https://{username}.lofter.com"
                    ),
                    InlineKeyboardButton(text="Status", url=status_link),
                ]
            ]
        )
        if status_link
        else InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Author", url=f"https://{username}.lofter.com"
                    )
                ]
            ]
        )
    )
