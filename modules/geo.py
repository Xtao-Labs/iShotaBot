import contextlib
from urllib.parse import quote

from pyrogram import Client, filters
from pyrogram.types import Message

from defs.glover import amap_key
from init import request, bot

REQUEST_URL = f"https://restapi.amap.com/v3/geocode/geo?key={amap_key}&"


@bot.on_message(
    filters.incoming & filters.command(["geo", f"geo@{bot.me.username}"])
)
async def geo_command(_: Client, message: Message):
    if len(message.command) <= 1:
        await message.reply("没有找到要查询的中国 经纬度/地址 ...")
        return
    mode, lat, lon = "address", 0, 0  # noqa
    with contextlib.suppress(ValueError, IndexError):
        lat, lon = float(message.command[1]), float(message.command[2])
        mode = "location"
    if mode == "location":
        try:
            geo = (
                await request.get(
                    f"{REQUEST_URL.replace('/geo?', '/regeo?')}location={lat},{lon}"
                )
            ).json()
            formatted_address = geo["regeocode"]["formatted_address"]
            assert isinstance(formatted_address, str)
        except (KeyError, AssertionError):
            await message.reply(f"无法解析经纬度 {lat}, {lon}", quote=True)
            return
    else:
        try:
            geo = (
                await request.get(
                    f"{REQUEST_URL}address={quote(' '.join(message.command[1:]).strip())}"
                )
            ).json()
            formatted_address = geo["geocodes"][0]["formatted_address"]
            lat, lon = geo["geocodes"][0]["location"].split(",")
        except (KeyError, IndexError, ValueError):
            await message.reply(
                f"无法解析地址 {' '.join(message.command[1:]).strip()}", quote=True
            )
            return
    msg = await message.reply_location(
        longitude=float(lat), latitude=float(lon), quote=True
    )
    await msg.reply(f"坐标：`{lat},{lon}`\n地址：<b>{formatted_address}</b>", quote=True)
