from pyrogram import filters, Client
from pyrogram.types import Message

from init import bot, logger

from cashews import cache
from defs.weather_graph import OUTPUT_PATH, gen, WeatherGraphError
from scheduler import scheduler

CACHE_KEY = "weather_graph:file_id"


@bot.on_message(
    filters.incoming
    & filters.command(["weather_graph", f"weather_graph@{bot.me.username}"])
)
async def weather_graph_command(_: "Client", message: "Message"):
    if file_id := await cache.get(CACHE_KEY):
        await message.reply_video(file_id, quote=True)
        return
    if OUTPUT_PATH.exists():
        reply = await message.reply_video(OUTPUT_PATH, quote=True)
        await cache.set(CACHE_KEY, reply.video.file_id, expire=3600)
    else:
        reply = await message.reply("正在生成中...")
        try:
            await gen()
            r1 = await message.reply_video(OUTPUT_PATH, quote=True)
            await cache.set(CACHE_KEY, r1.video.file_id, expire=3600)
            await reply.delete()
        except WeatherGraphError as e:
            await reply.edit(f"生成失败：{e.error}")


# @scheduler.scheduled_job("interval", hours=1, id="weather_graph_refresh")
async def weather_graph_refresh():
    try:
        await gen()
    except WeatherGraphError as e:
        logger.exception("Weather Graph Refresh failed", exc_info=e)
