from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message
from defs.asoulcnki import check_text, random_text
from init import user_me


@Client.on_message(filters.incoming & ~filters.edited &
                   filters.command(["查重", f"查重@{user_me.username}"]))
async def asoulcnki_process(client: Client, message: Message):
    text = message.reply_to_message.text if message.reply_to_message else " ".join(message.text.split(" ")[1:])
    if not text:
        await message.reply("请输入文本。")
        raise ContinuePropagation
    if len(text) >= 1000:
        await message.reply('文本过长，长度须在10-1000之间', quote=True)
        raise ContinuePropagation
    elif len(text) <= 10:
        await message.reply('文本过短，长度须在10-1000之间', quote=True)
        raise ContinuePropagation
    image, text = await check_text(text)
    if image:
        await message.reply_photo(image, quote=True, caption=text)
    else:
        if text:
            await message.reply(text, quote=True)
        else:
            await message.reply('出错了，请稍后再试', quote=True)
    raise ContinuePropagation


@Client.on_message(filters.incoming & ~filters.edited &
                   filters.command(["小作文", f"小作文@{user_me.username}"]))
async def asoulcnki_random(client: Client, message: Message):
    text = message.reply_to_message.text if message.reply_to_message else " ".join(message.text.split(" ")[1:])
    if not text:
        text = ""
    image, text = await random_text(text)
    if image:
        await message.reply_photo(image, quote=True, caption=text)
    else:
        if text:
            await message.reply(text, quote=True)
        else:
            await message.reply('出错了，请稍后再试', quote=True)
    raise ContinuePropagation
