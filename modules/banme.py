import contextlib
import re
import random

from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, ChatPermissions, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from init import bot
from scheduler import reply_message


def gen_cancel_button(uid: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="别口球我！", callback_data=f"banme_cancel_{uid}")
            ]
        ]
    )


@bot.on_message(
    filters.incoming
    & filters.group
    & filters.command(["banme", f"banme@{bot.me.username}"])
)
async def ban_me_command(client: Client, message: Message):
    args = str(message.text).strip()
    # 检查是否有倍数参数
    if multiple_text := re.search(r"^(\d+)倍$", args):
        multiple = int(multiple_text.groups()[0])
    else:
        multiple = 1
    if multiple > 5 or multiple < 1:
        multiple = 1

    # 检查bot和用户身份
    if (
            await client.get_chat_member(message.chat.id, "self")
    ).status != ChatMemberStatus.ADMINISTRATOR:
        await message.reply("Bot非群管理员, 无法执行禁言操作QAQ")
        return
    if not message.from_user:
        # 频道
        await reply_message(message, "你是个频道, 别来凑热闹OvO")
        return

    member = (
        await client.get_chat_member(message.chat.id, message.from_user.id)
    ).status
    if member in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await reply_message(message, "你也是个管理, 别来凑热闹OvO")
        return

    # 随机禁言时间
    random_time = 2 * int(random.gauss(128 * multiple, 640 * multiple // 10))
    act_time = 60 if random_time < 60 else min(random_time, 2591940)
    msg = f"既然你那么想被口球的话, 那我就成全你吧!\n送你一份{act_time // 60}分{act_time % 60}秒禁言套餐哦, 谢谢惠顾~"

    await client.restrict_chat_member(
        message.chat.id,
        message.from_user.id,
        ChatPermissions(),
        datetime.now() + timedelta(seconds=act_time),
    )
    await reply_message(message, msg, reply_markup=gen_cancel_button(message.from_user.id))


@bot.on_callback_query(
    filters.regex(r"^banme_cancel_(\d+)$")
)
async def ban_me_cancel(client: Client, callback_query: CallbackQuery):
    if not callback_query.from_user:
        return
    uid = int(callback_query.data.split("_")[-1])
    if callback_query.from_user.id != uid:
        await callback_query.answer("这不是属于你的按钮 ~")
        return
    await callback_query.answer("已撤销，请等待 60s 后发言")
    with contextlib.suppress(Exception):
        await callback_query.message.delete()
    await client.restrict_chat_member(
        callback_query.message.chat.id,
        callback_query.from_user.id,
        ChatPermissions(),
        datetime.now() + timedelta(seconds=60),
    )
