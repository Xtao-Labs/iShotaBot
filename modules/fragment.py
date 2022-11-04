import re

from pyrogram import Client
from pyrogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, \
    InlineKeyboardButton

from defs.fragment import parse_fragment, NotAvailable

QUERY_PATTERN = re.compile(r"^@\w[a-zA-Z0-9_]{3,32}$")


@Client.on_inline_query()
async def fragment_inline(_, inline_query: InlineQuery):
    username = inline_query.query
    if not username.startswith("@"):
        username = f"@{username}"
    if not QUERY_PATTERN.match(username):
        return await inline_query.answer(
            results=[],
            switch_pm_text="请输入 @username 来查询遗产",
            switch_pm_parameter="start",
            cache_time=0,
        )
    username = username[1:]
    try:
        user = await parse_fragment(username)
        text = user.text
    except NotAvailable:
        text = f"用户名：@{username}\n" \
               f"状态：暂未开放购买\n"
    except Exception:
        text = ""
    if not text:
        return await inline_query.answer(
            results=[],
            switch_pm_text="查询失败了 ~ 呜呜呜",
            switch_pm_parameter="start",
            cache_time=0,
        )
    results = [
        InlineQueryResultArticle(
            title=username,
            input_message_content=InputTextMessageContent(text),
            url=f"https://fragment.com/username/{username}",
            description="点击发送详情",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        "Open",
                        url=f"https://fragment.com/username/{username}"
                    )]
                ]
            )
        ),
    ]
    await inline_query.answer(
        results=results,
        switch_pm_text="查询成功",
        switch_pm_parameter="start",
        cache_time=0
    )
