from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from defs.exchange import exchange_client
from scheduler import scheduler
from init import bot


@scheduler.scheduled_job("cron", hour="8", id="exchange.refresh")
async def exchange_refresh() -> None:
    await exchange_client.refresh()


@bot.on_message(
    filters.incoming & filters.command(["exchange", f"exchange@{bot.me.username}"])
)
async def exchange_command(_: Client, message: Message):
    if not exchange_client.inited:
        await exchange_client.refresh()
    if not exchange_client.inited:
        return await message.reply("获取汇率数据出现错误！")
    text = await exchange_client.check_ex(message)
    if text == "help":
        text = (
            "该指令可用于查询汇率。\n使用方式举例:\n/exchange USD CNY - 1 USD 等于多少 CNY\n"
            "/exchange 11 CNY USD - 11 CNY 等于多少 USD"
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
        return await message.reply(text)
    reply_ = await message.reply(text)
    if message.chat.type == ChatType.PRIVATE:
        await reply_.reply(
            "支持货币： <code>" + ", ".join(exchange_client.currencies) + "</code>"
        )
