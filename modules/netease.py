from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message
from defs.netease import start_download, get_music_id


@Client.on_message(filters.incoming & ~filters.edited)
async def netease_handler(client: Client, message: Message):
    if not message.text:
        raise ContinuePropagation
    data = get_music_id(message.text)
    if not data:
        raise ContinuePropagation
    reply = await message.reply("[ned]")
    await start_download(reply, message, data, True)
    raise ContinuePropagation
