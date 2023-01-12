from pyrogram import Client, filters
from pyrogram.types import Message

from defs.guess import guess_str
from init import user_me


@Client.on_message(
    filters.incoming & filters.command(["guess", f"guess@{user_me.username}"])
)
async def guess_command(_: Client, message: Message):
    msg = await message.reply("正在查询中...")
    if len(message.text.split()) == 1:
        text = ""
        if reply := message.reply_to_message:
            text = await guess_str(reply.text)
        if text == "":
            text = "没有匹配到拼音首字母缩写"
        await msg.edit(text)
    else:
        rep_text = ""
        if reply := message.reply_to_message:
            rep_text += await guess_str(reply.text)
        text = await guess_str(message.text[7:])
        if not rep_text and not text:
            await msg.edit("没有匹配到拼音首字母缩写")
        elif not rep_text:
            await msg.edit(f"{text}")
        else:
            await msg.edit(f"{rep_text}{text}")
