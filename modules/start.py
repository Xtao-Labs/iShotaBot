from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from defs.button import gen_button, Button
from init import bot

des = """本机器人特性：

★ 解析 bilibili 视频、动态
★ 解析 lofter 日志、用户
★ 解析 fanbox 发帖、用户
★ 汇率查询
★ 复读机（3条）
★ 答案之书
★ 鲁迅说过
★ 我有个朋友
★ 简易版问与答
"""


@bot.on_message(filters.incoming & filters.private & filters.command(["start"]))
async def start_command(_: Client, message: Message):
    """
    回应机器人信息
    """
    await message.reply(
        des,
        quote=True,
        reply_markup=gen_button(
            [
                Button(0, "Gitlab", "https://gitlab.com/Xtao-Labs/iShotaBot"),
                Button(0, "Github", "https://github.com/Xtao-Labs/iShotaBot"),
            ]
        ),
    )


def empty():
    async def fun(_, __, update):
        return not bool(update.query)

    return filters.create(fun)


@bot.on_inline_query(filters=empty())
async def empty_inline(_, inline_query: InlineQuery):
    results = [
        InlineQueryResultArticle(
            title="@username",
            input_message_content=InputTextMessageContent("使用 @username 来查询遗产"),
            description="使用 @username 来查询遗产",
        ),
        InlineQueryResultArticle(
            title="m",
            input_message_content=InputTextMessageContent("使用 m 来查询米游社启动图"),
            description="使用 m 来查询米游社启动图",
        ),
        InlineQueryResultArticle(
            title="dc",
            input_message_content=InputTextMessageContent("使用 dc 来查询会话数据中心"),
            description="使用 dc 来查询会话数据中心",
        ),
        InlineQueryResultArticle(
            title="exchange",
            input_message_content=InputTextMessageContent(
                "使用 exchange 来查询汇率数据"
            ),
            description="使用 exchange 来查询汇率数据",
        ),
    ]
    return await inline_query.answer(
        results=results,
        switch_pm_text="使用关键词开始查询",
        switch_pm_parameter="start",
        cache_time=0,
    )
