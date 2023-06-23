from pyrogram import Client, filters
from pyrogram.types import Message, Chat

from init import bot


def mention_chat(chat: Chat) -> str:
    return (
        f'<a href="https://t.me/{chat.username}">{chat.title}</a>'
        if chat.username
        else chat.title
    )


def get_dc(message: Message):
    dc = 0
    mention = "他"
    if message.reply_to_message:
        if message.reply_to_message.sender_chat:
            mention = mention_chat(message.reply_to_message.sender_chat)
            dc = message.reply_to_message.sender_chat.dc_id
        elif message.reply_to_message.from_user:
            mention = message.reply_to_message.from_user.mention
            dc = message.reply_to_message.from_user.dc_id
    elif message.from_user:
        mention = message.from_user.mention
        dc = message.from_user.dc_id
    elif message.sender_chat:
        mention = mention_chat(message.sender_chat)
        dc = message.sender_chat.dc_id
    return dc, mention


@bot.on_message(filters.incoming & filters.command(["dc", f"dc@{bot.me.username}"]))
async def dc_command(_: Client, message: Message):
    geo_dic = {
        "1": "美国-佛罗里达州-迈阿密",
        "2": "荷兰-阿姆斯特丹",
        "3": "美国-佛罗里达州-迈阿密",
        "4": "荷兰-阿姆斯特丹",
        "5": "新加坡",
    }
    dc, mention = get_dc(message)
    if dc:
        text = f"{mention}所在数据中心为: <b>DC{dc}</b>\n该数据中心位于 <b>{geo_dic[str(dc)]}</b>"
    else:
        text = f"{mention}需要先<b>设置头像并且对我可见。</b>"
    await message.reply(text)
