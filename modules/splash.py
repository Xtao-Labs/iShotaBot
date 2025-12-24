from pyrogram import Client, filters
from pyrogram.types import Message, InlineQuery

from defs.glover import admin
from defs.splash import update_splash, get_inline_results
from init import bot
from scheduler import scheduler


@bot.on_message(
    filters.incoming & filters.user(admin) & filters.command(["splash_update"])
)
async def splash_update(_: Client, message: Message):
    """
    更新 splash
    """
    await update_splash()
    await message.reply("更新成功", quote=True)


# @scheduler.scheduled_job("interval", minutes=30, id="splash_update")
async def splash_update_job() -> None:
    await update_splash()


@bot.on_inline_query(filters.regex(r"^m$"))
async def splash_query(_: Client, inline_query: InlineQuery):
    results = await get_inline_results()
    if not results:
        await inline_query.answer(
            results=[],
            switch_pm_text="暂无启动图数据",
            switch_pm_parameter="start",
            cache_time=0,
        )
    else:
        await inline_query.answer(
            results=results,
            switch_pm_text=f"共 {len(results)} 张启动图",
            switch_pm_parameter="start",
            cache_time=0,
        )
    inline_query.stop_propagation()
