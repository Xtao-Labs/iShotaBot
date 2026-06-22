from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    ReplyParameters,
    InputRichMessage,
    InputRichMessageContent,
)
from init import bot

USAGE = """用法：
/md <Markdown 文本> - 以 Markdown 富文本发送
/html <HTML 文本>   - 以 HTML 富文本发送
内联查询：在任意输入框输入 `md 文本` 或 `html 文本` 后选择结果发送。"""


def _make_rich(mode: str, text: str) -> InputRichMessage:
    """根据模式构造富文本消息对象"""
    return InputRichMessage(**{mode: text})


async def _send_rich(_: Client, message: Message, mode: str):
    """发送富文本消息的通用逻辑"""
    if len(message.command) < 2:
        await message.reply(USAGE)
        raise ContinuePropagation
    text = " ".join(message.command[1:])
    rich = _make_rich(mode, text)
    await bot.send_rich_message(
        message.chat.id,
        rich,
        reply_parameters=ReplyParameters(message_id=message.id),
    )


async def _answer_inline(_: Client, inline_query: InlineQuery, mode: str, title: str):
    """内联查询的通用应答逻辑"""
    text = " ".join(inline_query.query.split(" ")[1:])
    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                title=title,
                input_message_content=InputRichMessageContent(
                    rich_message=_make_rich(mode, text),
                ),
            )
        ],
        switch_pm_text="发送后查询",
        switch_pm_parameter="start",
        cache_time=0,
    )
    inline_query.stop_propagation()


@bot.on_message(filters.incoming & filters.command(["md"]))
async def md_command(client: Client, message: Message):
    await _send_rich(client, message, "markdown")


@bot.on_message(filters.incoming & filters.command(["html"]))
async def html_command(client: Client, message: Message):
    await _send_rich(client, message, "html")


@bot.on_inline_query(filters.regex(r"^md"))
async def md_query(client: Client, inline_query: InlineQuery):
    await _answer_inline(client, inline_query, "markdown", "查询 md")


@bot.on_inline_query(filters.regex(r"^html"))
async def html_query(client: Client, inline_query: InlineQuery):
    await _answer_inline(client, inline_query, "html", "查询 html")
