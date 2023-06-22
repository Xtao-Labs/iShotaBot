from pyrogram import Client, filters
from pyrogram.types import Message

from defs.splash import update_splash
from scheduler import scheduler


@Client.on_message(
    filters.incoming & filters.command(["splash_update"])
)
async def splash_update(_: Client, message: Message):
    """
    更新 splash
    """
    await update_splash()
    await message.reply("更新成功", quote=True)


@scheduler.scheduled_job("interval", minutes=30, id="splash_update")
async def splash_update_job() -> None:
    await update_splash()
