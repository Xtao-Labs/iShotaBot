import contextlib

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMemberUpdated, Message

from init import bot
from models.services.rank_update import RankUpdateAction


TEXT = """#TITLE
• 来自: {} [<code>{}</code>]
• 对象: {} [<code>{}</code>]
• 群组: {} [<code>{}</code>]
• 旧标签: <code>{}</code>
• 新标签: <code>{}</code>
#chat{} #id{}
"""
USAGE = "Usage: /detect_member_rank_change [chat_id|false]"


@bot.on_chat_member_updated()
async def detect_member_rank_change(
    client: Client, chat_member_updated: ChatMemberUpdated
):
    chat = chat_member_updated.chat
    member = chat_member_updated.new_chat_member
    old_member = chat_member_updated.old_chat_member
    if not member or not member.user or not old_member or not old_member.user:
        raise ContinuePropagation
    now_rank = member.rank
    old_rank = old_member.rank
    actor = chat_member_updated.from_user
    if now_rank == old_rank:
        raise ContinuePropagation
    # 发生变化
    log_chat_id = await RankUpdateAction.get_by_chat_id(chat.id)
    if not log_chat_id:
        raise ContinuePropagation
    format_text = TEXT.format(
        actor.mention,
        actor.id,
        member.user.mention,
        member.user.id,
        chat.title,
        chat.id,
        old_rank,
        now_rank,
        abs(chat.id),
        member.user.id,
    )
    await client.send_message(log_chat_id.log_chat_id, format_text)
    raise ContinuePropagation


@bot.on_message(
    filters.incoming & filters.group & filters.command(["detect_member_rank_change"])
)
async def switch_detect_member_rank_change(client: Client, message: Message):
    # Check user
    if not message.from_user:
        return
    data = await client.get_chat_member(message.chat.id, message.from_user.id)
    if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply("You are not an admin of this chat.")
        raise ContinuePropagation
    # Check self
    data = await client.get_chat_member(message.chat.id, bot.me.id)
    if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply("I'm not an admin of this chat.")
        raise ContinuePropagation
    if len(message.command) < 2:
        await message.reply(USAGE)
        raise ContinuePropagation
    chat_id = message.chat.id
    log_chat_id = message.command[1]
    model = await RankUpdateAction.get_by_chat_id(chat_id)
    msg = USAGE
    if log_chat_id == "false":
        if model:
            await RankUpdateAction.delete_rank_update(model)
            msg = "已关闭成员标签检查"
        else:
            msg = "未开启成员标签检查"
    with contextlib.suppress(Exception):
        log_chat_id = int(log_chat_id)
    if isinstance(log_chat_id, int):
        if model:
            model.log_chat_id = log_chat_id
            await RankUpdateAction.update_rank_update(model)
            msg = "已更新成员标签检查日志频道"
        else:
            await RankUpdateAction.add_rank_update(chat_id, log_chat_id)
            msg = "已开启成员标签检查"
    await message.reply(msg)
    raise ContinuePropagation
