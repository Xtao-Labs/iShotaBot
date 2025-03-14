from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message

from defs.glover import exchange_channel
from defs.exchange_json import process_data
from init import bot


@bot.on_message(filters.incoming & filters.text & filters.chat(exchange_channel))
async def exchange_json(_: Client, message: Message):
    await process_data(message.text)
    raise ContinuePropagation
