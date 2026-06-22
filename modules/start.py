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


# 内联查询帮助列表：每项为 (关键词, 描述) 格式
# 添加更多帮助只需在此列表追加一项即可
INLINE_HELPS: list[tuple[str, str]] = [
    ("m", "使用 m 来查询米游社启动图"),
    ("dc", "使用 dc 来查询会话数据中心"),
    ("exchange", "使用 exchange 来查询汇率数据"),
    ("ip", "使用 ip 来查询 ip 数据"),
    ("whois", "使用 whois 来查询 whois 数据"),
    ("weather", "使用 weather 来查询天气数据"),
    ("md", "使用 markdown 渲染消息"),
    ("html", "使用 html 渲染消息"),
]


def empty():
    async def fun(_, __, update):
        return not bool(update.query)

    return filters.create(fun)


def _build_help_results() -> list[InlineQueryResultArticle]:
    """根据 INLINE_HELPS 构造内联帮助条目列表"""
    return [
        InlineQueryResultArticle(
            title=keyword,
            input_message_content=InputTextMessageContent(desc),
            description=desc,
        )
        for keyword, desc in INLINE_HELPS
    ]


@bot.on_inline_query(filters=empty())
async def empty_inline(_, inline_query: InlineQuery):
    return await inline_query.answer(
        results=_build_help_results(),
        switch_pm_text="使用关键词开始查询",
        switch_pm_parameter="start",
        cache_time=0,
    )
