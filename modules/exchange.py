from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from defs.exchange import exchange_client
from scheduler import scheduler
from init import bot


@scheduler.scheduled_job("cron", hour="8", id="exchange.refresh")
async def exchange_refresh() -> None:
    await exchange_client.refresh()


async def get_text(text: str, inline: bool):
    if not exchange_client.inited:
        return "获取汇率数据出现错误！", False
    text = await exchange_client.check_ex(text)
    if text == "help":
        prefix = "" if inline else "/"
        text = (
            f"该指令可用于查询汇率。\n使用方式举例:\n{prefix}exchange USD CNY - 1 USD 等于多少 CNY\n"
            f"{prefix}exchange 11 CNY USD - 11 CNY 等于多少 USD"
        )
    elif text == "ValueError":
        text = "金额不合法"
    elif text == "ValueBig":
        text = "我寻思你也没这么多钱啊。"
    elif text == "ValueSmall":
        text = "小数点后的数字咋这么多？"
    elif text == "FromError":
        text = "不支持的起源币种。"
    elif text == "ToError":
        text = "不支持的目标币种。"
    else:
        return text, True
    return text, False


@bot.on_message(
    filters.incoming & filters.command(["exchange", f"exchange@{bot.me.username}"])
)
async def exchange_command(_: Client, message: Message):
    if not exchange_client.inited:
        await exchange_client.refresh()
    text, success = await get_text(message.text, False)
    reply_ = await message.reply(text)
    if not success and message.chat.type == ChatType.PRIVATE:
        await reply_.reply(
            "支持货币： <code>" + ", ".join(exchange_client.currencies) + "</code>"
        )


@bot.on_inline_query(filters.regex("^exchange"))
async def exchange_inline(_: Client, inline_query: InlineQuery):
    text, success = await get_text(inline_query.query, True)
    results = [
        InlineQueryResultArticle(
            title="查询汇率数据成功" if success else "查询汇率数据失败",
            input_message_content=InputTextMessageContent(message_text=text),
            # reply_markup=InlineKeyboardMarkup(
            #     [[InlineKeyboardButton(text="重试", callback_data="dc")]]
            # ),
        )
    ]
    await inline_query.answer(
        results=results,
        cache_time=0,
    )
