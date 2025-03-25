from pyrogram import Client, filters
from pyrogram.types import Message

from defs.geo import get_geo_data_from_message
from init import bot


@bot.on_message(filters.incoming & filters.command(["geo", f"geo@{bot.me.username}"]))
async def geo_command(_: Client, message: Message):
    if len(message.command) <= 1:
        await message.reply("没有找到要查询的中国 经纬度/地址 ...")
        return
    lat, lon, formatted_address = await get_geo_data_from_message(message)
    if lat is None or lon is None or formatted_address is None:
        await message.reply("无法解析地址或经纬度 ...")
        return
    msg = await message.reply_location(
        longitude=float(lat), latitude=float(lon), quote=True
    )
    await msg.reply(
        f"坐标：`{lat},{lon}`\n地址：<b>{formatted_address}</b>", quote=True
    )
