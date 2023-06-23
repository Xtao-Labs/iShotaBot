import contextlib
from pyrogram import Client, filters, ContinuePropagation, errors
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from pyrogram.raw import types, functions
from pyrogram.raw.base import Update

from asyncio import sleep

from defs.anti_channel import init, add, get_status, check_status, clean
from init import logs, bot

init()


@bot.on_raw_update(filters.incoming & filters.group)
async def anti_channel_msg(client: Client, update: Update, _, __: dict):
    while True:
        try:
            # Check for message that are from channel
            if not isinstance(update, types.UpdateNewChannelMessage) or not isinstance(
                update.message.from_id, types.PeerChannel
            ):
                raise ContinuePropagation

            # Basic data
            message = update.message
            chat_id = int(f"-100{message.peer_id.channel_id}")

            # Check if open
            if not get_status(chat_id):
                raise ContinuePropagation

            channel_id = int(f"-100{message.from_id.channel_id}")

            # Check for linked channel
            if (
                message.fwd_from
                and message.fwd_from.saved_from_peer
                == message.fwd_from.from_id
                == message.from_id
            ) or channel_id == chat_id:
                raise ContinuePropagation

            # Check if blocked
            if check_status(chat_id, channel_id):
                raise ContinuePropagation

            # Delete the message sent by channel and ban it.
            await client.invoke(
                functions.channels.EditBanned(
                    channel=await client.resolve_peer(chat_id),
                    participant=await client.resolve_peer(channel_id),
                    banned_rights=types.ChatBannedRights(
                        until_date=0,
                        view_messages=True,
                        send_messages=True,
                        send_media=True,
                        send_stickers=True,
                        send_gifs=True,
                        send_games=True,
                        send_polls=True,
                    ),
                )
            )
            await client.delete_messages(chat_id, message.id)
            add(chat_id, channel_id)
            raise ContinuePropagation
        except errors.FloodWait as e:
            logs.debug(f"{e}, retry after {e.value} seconds...")
            await sleep(e.value)
        except errors.ChatAdminRequired as e:
            with contextlib.suppress(NameError):
                clean(chat_id)  # noqa
            raise ContinuePropagation from e
        except ContinuePropagation as e:
            raise ContinuePropagation from e


@bot.on_message(
    filters.incoming
    & filters.group
    & filters.command(["anti_channel_msg", f"anti_channel_msg@{bot.me.username}"])
)
async def switch_anti_channel_msg(client: Client, message: Message):
    # Check user
    if message.from_user:
        data = await client.get_chat_member(message.chat.id, message.from_user.id)
        if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply("You are not an admin of this chat.")
            raise ContinuePropagation
    # Check self
    data = await client.get_chat_member(message.chat.id, bot.me.id)
    if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await message.reply("I'm not an admin of this chat.")
        raise ContinuePropagation
    switch = len(message.text.split(" ")) > 1
    if get_status(message.chat.id):
        if switch:
            clean(message.chat.id)
            await message.reply("Anti-channel is now disabled.")
        else:
            await message.reply(
                "Anti-channel is already enabled.\n"
                "\n"
                "Tips: Use `/anti_channel_msg true` to enable or disable it."
            )
    elif switch:
        add(message.chat.id, message.chat.id)
        await message.reply("Anti-channel is now enabled.")
    else:
        await message.reply(
            "Anti-channel is already disabled.\n"
            "\n"
            "Tips: Use `/anti_channel_msg true` to enable or disable it."
        )
    raise ContinuePropagation
