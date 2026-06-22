import inspect
import re
from types import MethodType

import pyrogram
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.handlers import InlineQueryHandler
from pyrogram.raw.types import UpdateBotGuestChatQuery
from pyrogram.types import (
    Update,
    InlineQuery,
    User,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from init import bot

START_TEXT = """欢迎使用 iShotaBot！

可用关键词：
★ exchange - 查询汇率数据
★ ip - 查询 ip 数据
★ whois - 查询 whois 数据
★ weather - 查询天气数据
★ md - 使用 markdown 渲染消息
★ html - 使用 html 渲染消息
"""


async def _dispatch_inline_query(client: Client, inline_query: InlineQuery):
    """
    手动将构造的 InlineQuery 派发到所有已注册的 InlineQueryHandler。
    返回首个被命中并成功处理的 handler 收集到的 results 列表（来自 answer hook）。
    """
    for group in client.dispatcher.groups.values():
        for handler in group:
            if not isinstance(handler, InlineQueryHandler):
                continue
            try:
                if not await handler.check(client, inline_query):
                    continue
            except Exception:
                continue
            try:
                if inspect.iscoroutinefunction(handler.callback):
                    await handler.callback(client, inline_query)
                else:
                    await client.loop.run_in_executor(
                        client.executor, handler.callback, client, inline_query
                    )
            except pyrogram.StopPropagation:
                return
            except pyrogram.ContinuePropagation:
                continue
            except Exception:
                continue
            return


@bot.on_raw_update()
async def guest_chat_query(client: Client, update: Update, users, chats):
    if not isinstance(update, UpdateBotGuestChatQuery):
        raise pyrogram.ContinuePropagation

    message = await pyrogram.types.Message._parse(client, update.message, users, chats)
    qid = update.query_id
    text = message.text or message.caption or ""
    query = text
    if me := client.me:
        query = re.sub(
            rf"@{re.escape(me.username)}", "", query, flags=re.IGNORECASE
        ).strip()

    if not query:
        result = InlineQueryResultArticle(
            title="iShotaBot",
            input_message_content=InputTextMessageContent(message_text=START_TEXT),
            description="使用关键词开始查询",
        )
        q = pyrogram.raw.functions.messages.SetBotGuestChatResult(
            query_id=qid,
            result=await result.write(client),
        )
        return await client.invoke(q)

    from_user = (
        message.from_user
        if message.from_user
        else User(id=0, is_bot=False, is_self=False, client=client)
    )

    inline_query = InlineQuery(
        client=client,
        id=str(qid),
        from_user=from_user,
        query=query,
        offset="",
        chat_type=ChatType.PRIVATE,
    )

    captured: dict = {}

    async def _answer(self, results, *args, **kwargs):
        captured["results"] = results

    inline_query.answer = MethodType(_answer, inline_query)

    await _dispatch_inline_query(client, inline_query)

    results = captured.get("results") or []
    if not results:
        raise pyrogram.ContinuePropagation

    q = pyrogram.raw.functions.messages.SetBotGuestChatResult(
        query_id=qid,
        result=await results[0].write(client),
    )
    return await client.invoke(q)
