import re

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message

from init import bot
from defs.ask import how_many, what_time, how_long, hif, handle_pers, who


@bot.on_message(filters.incoming & filters.regex(r"^问"))
async def ask(_: Client, message: Message):
    msg = message
    if not message.text:
        raise ContinuePropagation
    message = message.text.strip()[1:]
    handled = False
    if re.findall("几|多少", message):
        handled = True
        message = await how_many(message)
    if re.findall("什么时候|啥时候", message):
        handled = True
        message = await what_time(message)
    if re.findall("多久|多长时间", message):
        handled = True
        message = await how_long(message)
    if re.findall(r"(.)不\1", message):
        handled = True
        message = await hif(message)

    message = await handle_pers(message)

    if re.findall("谁", message):
        handled = True
        message = await who(message, msg.chat.id)
    if handled:
        await msg.reply(message)
    raise ContinuePropagation
