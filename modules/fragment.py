import contextlib
import re

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)

from models.fragment import FragmentSubText, FragmentSub, AuctionStatus
from defs.fragment import parse_fragment, NotAvailable, parse_sub
from init import user_me, bot
from scheduler import scheduler, add_delete_message_job

QUERY_PATTERN = re.compile(r"^@\w[a-zA-Z0-9_]{3,32}$")


@Client.on_message(
    filters.incoming & filters.command(["username", f"username@{user_me.username}"])
)
async def fragment_command(client: Client, message: Message):
    status = None
    user = None
    if len(message.command) <= 1:
        return await message.reply("没有找到要查询的用户名 ...")
    elif message.command[1] == "订阅列表":
        status = FragmentSubText.List
    elif len(message.command) > 2:
        if message.command[2] not in ["订阅", "退订"]:
            return await message.reply("只能查询一个用户名 ...")
        status = FragmentSubText(message.command[2])
    if status and message.from_user:
        data = await client.get_chat_member(message.chat.id, message.from_user.id)
        if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            rep = await message.reply("You are not an admin of this chat.")
            add_delete_message_job(rep)
            raise ContinuePropagation
    if status == FragmentSubText.List:
        text = await parse_sub(status, user, message.chat.id)
    else:
        username = message.command[1]
        if not username.startswith("@"):
            username = f"@{username}"
        if not QUERY_PATTERN.match(username):
            return await message.reply("无效的用户名")
        username = username[1:]
        try:
            user = await parse_fragment(username)
            text = user.text
        except NotAvailable:
            text = "解析失败了 ... 请稍后再试"
        except Exception:
            text = "查询失败了 ... 请稍后再试"
        if status and user is not None:
            text = await parse_sub(status, user, message.chat.id)
    await message.reply(text)


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
        text = f"用户名：@{username}\n" f"状态：暂未开放购买\n"
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
                    [
                        InlineKeyboardButton(
                            "Open", url=f"https://fragment.com/username/{username}"
                        )
                    ]
                ]
            ),
        ),
    ]
    await inline_query.answer(
        results=results,
        switch_pm_text="查询成功",
        switch_pm_parameter="start",
        cache_time=0,
    )


@scheduler.scheduled_job("cron", hour="8", minute="1", id="fragment.sub")
async def fragment_sub() -> None:
    data = await FragmentSub.get_all()
    if not data:
        return
    for item in data:
        with contextlib.suppress(NotAvailable, Exception):
            user = await parse_fragment(item.username)
            text = user.text
            if user.status in [AuctionStatus.Sold, AuctionStatus.Unavailable]:
                await FragmentSub.unsubscribe(item)
            await bot.send_message(item.cid, text)
