import os
from io import BytesIO
from typing import List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from pyrogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaDocument, \
    InputMediaAnimation, InputMediaVideo, Message

from init import request, bot


class LofterItem:
    def __init__(self, url, title):
        self.url = url
        self.file = None
        self.text = title

    async def init(self):
        file = await request.get(self.url, timeout=30)
        file = BytesIO(file.content)
        file.name = os.path.basename(self.url).split('?')[0]
        self.file = file

    async def reply_to(self, message: Message, static: bool = False):
        if not self.file:
            await self.init()
        if static:
            await message.reply_document(self.file, caption=self.text, quote=True, reply_markup=gen_button(self.url))
        elif self.file.name.endswith('.gif'):
            await message.reply_animation(self.file, caption=self.text, quote=True, reply_markup=gen_button(self.url))
        elif self.file.name.endswith('.mp4'):
            await message.reply_video(self.file, caption=self.text, quote=True, reply_markup=gen_button(self.url))
        else:
            await message.reply_photo(self.file, caption=self.text, quote=True, reply_markup=gen_button(self.url))

    async def export(self, static: bool = False, first: bool = False):
        if not self.file:
            await self.init()
        if static:
            return InputMediaDocument(self.file, caption=self.text if first else None)
        elif self.file.name.endswith('.gif'):
            return InputMediaAnimation(self.file, caption=self.text if first else None)
        elif self.file.name.endswith('.mp4'):
            return InputMediaVideo(self.file, caption=self.text if first else None)
        else:
            return InputMediaPhoto(self.file, caption=self.text if first else None)


def gen_button(url):
    data = urlparse(url)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Source", url=url),
        InlineKeyboardButton(text="Author", url=f"https://{data.hostname}")]])


async def input_media(img: List[LofterItem], static: bool = False):
    return [(await img[ff].export(static, ff == 0)) for ff in range(len(img))]


async def get_loft(url: str) -> List[LofterItem]:
    res = await request.get(url)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    title = soup.findAll("div", {"class": "text"})[-1].getText()
    links = soup.findAll("a", {"class": "imgclasstag"})
    return [LofterItem(i.get("bigimgsrc"), title) for i in links]
