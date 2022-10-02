from urllib.parse import urlparse

from bs4 import BeautifulSoup
from pyrogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

from init import request


def gen_button(url):
    data = urlparse(url)
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(text="Source", url=url),
        InlineKeyboardButton(text="Author", url=f"https://{data.hostname}")]])


def input_media(img, text):
    return [InputMediaPhoto(img[ff], caption=text if ff == 0 else None) for ff in range(len(img))]


async def get_loft(url: str):
    res = await request.get(url)
    assert res.status_code == 200
    soup = BeautifulSoup(res.text, "lxml")
    links = soup.findAll("a", {"class": "imgclasstag"})
    img = [i.get("bigimgsrc") for i in links]
    title = soup.findAll("div", {"class": "text"})[-1].getText()
    return img, title
