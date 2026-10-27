from pyrogram import Client, ContinuePropagation, filters
from pyrogram.types import Message

from defs.luxun import process_pic
from init import bot


@bot.on_message(filters.incoming & filters.regex(r"^鲁迅说过"))
async def luxun_say(_: Client, message: Message):
    args = message.text[4:]
    if not args:
        await message.reply("烦了，不说了")
        raise ContinuePropagation
    content = args.strip()
    if content.startswith(",") or content.startswith("，"):
        content = content[1:]
    if len(content) > 20:
        await message.reply("太长了, 鲁迅说不完!")
    else:
        if len(content) >= 12:
            content = content[:12] + "\n" + content[12:]
        picture = process_pic(content)
        await message.reply_photo(picture)
    raise ContinuePropagation
