from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    Chat,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChosenInlineResult,
    CallbackQuery,
)
from pyrogram.utils import unpack_inline_message_id

from init import bot

geo_dic = {
    "1": "美国-佛罗里达州-迈阿密",
    "2": "荷兰-阿姆斯特丹",
    "3": "美国-佛罗里达州-迈阿密",
    "4": "荷兰-阿姆斯特丹",
    "5": "新加坡",
}


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
    dc, mention = get_dc(message)
    if dc:
        text = f"{mention}所在数据中心为: <b>DC{dc}</b>\n该数据中心位于 <b>{geo_dic[str(dc)]}</b>"
    else:
        text = f"{mention}需要先<b>设置头像并且对我可见。</b>"
    await message.reply(text)


@bot.on_inline_query(filters.regex(r"^dc$"))
async def dc_query(_: Client, inline_query: InlineQuery):
    results = [
        InlineQueryResultArticle(
            title="查询 dc",
            input_message_content=InputTextMessageContent(message_text="加载中，请等待。。。"),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="重试", callback_data="dc")]]
            ),
        )
    ]
    await inline_query.answer(
        results=results,
        switch_pm_text="发送后查询",
        switch_pm_parameter="start",
        cache_time=0,
    )
    inline_query.stop_propagation()


def get_dc_text(dc: int):
    return f"此会话所在数据中心为: <b>DC{dc}</b>\n" f"该数据中心位于 <b>{geo_dic[str(dc)]}</b>"


@bot.on_chosen_inline_result()
async def dc_choose_callback(_: Client, chosen_inline_result: ChosenInlineResult):
    if chosen_inline_result.query != "dc":
        chosen_inline_result.continue_propagation()
    mid = chosen_inline_result.inline_message_id
    if not mid:
        return
    unpacked = unpack_inline_message_id(mid)
    dc = unpacked.dc_id
    await bot.edit_inline_text(mid, get_dc_text(dc))


@bot.on_callback_query(filters.regex(r"^dc$"))
async def dc_callback(_: Client, callback_query: CallbackQuery):
    mid = callback_query.inline_message_id
    if not mid:
        await callback_query.answer("数据错误", show_alert=True)
        callback_query.continue_propagation()
    unpacked = unpack_inline_message_id(mid)
    dc = unpacked.dc_id
    try:
        await callback_query.edit_message_text(get_dc_text(dc))
    except Exception:
        await callback_query.answer("数据错误", show_alert=True)
