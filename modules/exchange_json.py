from pyrogram import Client, ContinuePropagation, filters
from pyrogram.types import Message

from defs.exchange_json import process_data
from defs.glover import exchange_channel
from init import bot


@bot.on_message(filters.incoming & filters.text & filters.chat(exchange_channel))
async def exchange_json(_: Client, message: Message):
    await process_data(message.text)
    raise ContinuePropagation
