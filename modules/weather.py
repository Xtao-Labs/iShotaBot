import traceback

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from defs.geo import get_geo_data_from_message, get_geo_data_from_text
from defs.weather import Weather
from init import bot


@bot.on_message(filters.incoming & filters.command(["weather"]))
async def weather_command(_: Client, message: Message):
    if len(message.command) <= 1:
        await message.reply("没有找到要查询的中国 经纬度/地址 ...")
        return
    lat, lon, formatted_address = await get_geo_data_from_message(message)
    if lat is None or lon is None or formatted_address is None:
        await message.reply("无法解析地址或经纬度 ...")
        return
    try:
        photo, text = await Weather.get_weather_photo(formatted_address, lat, lon)
        await message.reply_photo(photo, caption=text, quote=True)
    except Exception as exc:
        traceback.print_exc()
        await message.reply("获取天气信息失败 ...", quote=True)


@bot.on_message(filters.incoming & filters.command(["weather_api"]))
async def weather_api_command(_: Client, message: Message):
    if len(message.command) <= 1:
        await message.reply("没有找到要查询的中国 经纬度/地址 ...")
        return
    lat, lon, formatted_address = await get_geo_data_from_message(message)
    if lat is None or lon is None or formatted_address is None:
        await message.reply("无法解析地址或经纬度 ...")
        return
    try:
        text = await Weather.get_weather_text(formatted_address, lat, lon)
        await message.reply_text(text, quote=True)
    except Exception as exc:
        traceback.print_exc()
        await message.reply("获取天气信息失败 ...", quote=True)


@bot.on_inline_query(filters.regex("^weather"))
async def weather_api_inline(_: Client, inline_query: InlineQuery):
    url = inline_query.query[8:]
    lat, lon, formatted_address = await get_geo_data_from_text(url)
    if lat is None or lon is None or formatted_address is None:
        text = None
    else:
        try:
            text = await Weather.get_weather_text(formatted_address, lat, lon)
        except Exception as exc:
            traceback.print_exc()
            text = None
    results = [
        InlineQueryResultArticle(
            title="查询 天气 数据成功" if text else "查询 天气 数据失败",
            description=url,
            input_message_content=InputTextMessageContent(
                message_text=text or "没有找到要查询的中国 经纬度/地址 ..."
            ),
        )
    ]
    await inline_query.answer(
        results=results,
        cache_time=0,
    )
