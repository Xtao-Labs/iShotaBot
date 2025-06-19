from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import ParseMode
from pyrogram.types import Message

from defs.fuck_or_not import run_chat_completion
from init import bot


@bot.on_message(filters.incoming & filters.command(["fuck", f"fuck@{bot.me.username}"]))
async def fuck_or_not(_: Client, message: Message):
    data = None
    if message.photo:
        data = await message.download(in_memory=True)
    elif message.reply_to_message and message.reply_to_message.photo:
        data = await message.reply_to_message.download(in_memory=True)
    if data:
        try:
            d = await run_chat_completion(data.getvalue())
            await message.reply(
                f"<b>{d.text} ({d.rating}/10)</b>\n"
                f"<blockquote>{d.explanation}</blockquote>",
                parse_mode=ParseMode.HTML,
                quote=True,
            )
        except Exception as e:
            await message.reply(f"模型请求失败：{str(e)}", quote=True)
    raise ContinuePropagation
