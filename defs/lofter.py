import contextlib
import os
import re

from io import BytesIO
from typing import List
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from pyrogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaDocument, \
    InputMediaAnimation, Message

from defs.glover import lofter_channel_username
from models.lofter import LofterPost as LofterPostModel
from init import request


class LofterItem:
    def __init__(self, url, audio_link, title: str, origin_url, username, name, comment, tags):
        self.url = url
        self.audio_link = f"https://music.163.com/#/song?id={audio_link}"
        self.only_text = url is None
        self.file = None
        self.origin_url = origin_url
        self.post_id = origin_url.split("/post/")[1].split("?")[0]
        self.username = username
        self.text = f"<b>Lofter Status Info</b>\n\n" \
                    f"<code>{title.strip()}</code>\n\n" \
                    f"✍️ <a href=\"https://{username}.lofter.com/\">{name}</a>\n" \
                    f"{tags}\n" \
                    f"{comment}"

    async def check_exists(self):
        if await LofterPostModel.get_by_post_id(self.post_id):
            self.text += f"\n📄 此图集已被<a href=\"https://t.me/{lofter_channel_username}\">此频道</a>收录"

    async def init(self):
        await self.check_exists()
        if self.only_text:
            return
        file = await request.get(self.url, timeout=30)
        file = BytesIO(file.content)
        file.name = os.path.basename(self.url).split('?')[0]
        self.file = file

    async def reply_to(self, message: Message, static: bool = False):
        if not self.file:
            await self.init()
        if static:
            await message.reply_document(self.file, caption=self.text, quote=True,
                                         reply_markup=lofter_link(self.url, self.origin_url, self.username))
        elif self.only_text:
            await message.reply_text(self.text, quote=True, disable_web_page_preview=True,
                                     reply_markup=lofter_link(self.audio_link, self.origin_url, self.username))
        elif self.file.name.endswith('.gif'):
            await message.reply_animation(self.file, caption=self.text, quote=True,
                                          reply_markup=lofter_link(self.url, self.origin_url, self.username))
        else:
            await message.reply_photo(self.file, caption=self.text, quote=True,
                                      reply_markup=lofter_link(self.url, self.origin_url, self.username))

    async def export(self, static: bool = False, first: bool = False):
        if not self.file:
            await self.init()
        if static:
            return InputMediaDocument(self.file, caption=self.text if first else None)
        elif self.file.name.endswith('.gif'):
            return InputMediaAnimation(self.file, caption=self.text if first else None)
        else:
            return InputMediaPhoto(self.file, caption=self.text if first else None)


async def input_media(img: List[LofterItem], static: bool = False):
    return [(await img[ff].export(static, ff == 0)) for ff in range(len(img))]


async def get_loft(url: str) -> List[LofterItem]:
    res = await request.get(url)
    assert res.status_code == 200
    username, avatar, name, bio, soup = parse_loft_user(url, res.text)
    try:
        title = soup.findAll("div", {"class": "text"})[-1].getText().strip()
    except IndexError:
        title = ""
    links = soup.findAll("a", {"class": "imgclasstag"})
    audio_link = None
    audio = soup.find("div", {"class": "img"})
    if audio and audio.getText().strip():
        title = f"分享音乐：{audio.getText().strip()}\n\n{title}" if title else f"分享音乐：{audio.getText().strip()}"
        audio_link = re.findall(r"%26id%3D(.*?)%26", audio.findAll("div")[1].get("onclick"))[0]
    comment = soup.findAll("h3", {"class": "nctitle"})
    comment_text = "".join(f"{i.getText()}  " for i in comment)
    if "(" not in comment_text:
        comment_text = ""
    tags = soup.find("meta", {"name": "Keywords"}).get("content")
    tags_text = "".join(f"#{i} " for i in tags.split(","))
    return [LofterItem(i.get("bigimgsrc"), audio_link, title, url, username, name, comment_text, tags_text)
            for i in links] if links else [
        LofterItem(None, audio_link, title, url, username, name, comment_text, tags_text)]


def parse_loft_user(url: str, content: str):
    username = urlparse(url).hostname.split(".")[0]
    soup = BeautifulSoup(content, "lxml")
    name, bio, avatar = "未知用户", "", None  # noqa
    with contextlib.suppress(Exception):
        name = soup.find("title").getText().split("-")[-1].strip()
    with contextlib.suppress(Exception):
        bio = " - ".join(soup.find("meta", {"name": "Description"}).get("content").split(" - ")[1:])
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
    text = f"<b>Lofter User Info</b>\n\n" \
           f"Name: <code>{name}</code>\n" \
           f"Username: <a href=\"https://{username}.lofter.com\">{username}</a>\n" \
           f"Bio: <code{bio}</code>"
    return text, avatar, username, status_link


def lofter_link(url, origin, username):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Source", url=origin),
                                  InlineKeyboardButton(text="Origin", url=url),
                                  InlineKeyboardButton(text="Author", url=f"https://{username}.lofter.com")]]) if url \
        else InlineKeyboardMarkup([[InlineKeyboardButton(text="Source", url=origin),
                                    InlineKeyboardButton(text="Author", url=f"https://{username}.lofter.com")]])


def lofter_user_link(username, status_link):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Author", url=f"https://{username}.lofter.com"),
                                  InlineKeyboardButton(text="Status", url=status_link)]]) if status_link else \
        InlineKeyboardMarkup([[InlineKeyboardButton(text="Author", url=f"https://{username}.lofter.com")]])
