from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message

from init import bot

last_msg = {}
last_repeat_msg = {}
repeat_count = {}


@bot.on_message(filters.incoming & filters.group)
async def repeater_handler(client: Client, message: Message):
    global last_msg, last_repeat_msg, repeat_count

    group_id = message.chat.id

    try:
        last_msg[group_id]
    except KeyError:
        last_msg[group_id] = {}
    try:
        last_repeat_msg[group_id]
    except KeyError:
        last_repeat_msg[group_id] = ""

    msg = t_msg = message.text
    if not msg:
        raise ContinuePropagation
    if (
        msg.startswith("/")
        or msg.startswith("!")
        or msg.startswith(",")
        or msg.startswith("，")
    ):
        raise ContinuePropagation

    last_msg_text = last_msg[group_id].get("text", "")
    last_msg_id = last_msg[group_id].get("id", 0)

    if message.id == last_msg_id:
        raise ContinuePropagation

    if msg != last_msg_text or msg == last_repeat_msg[group_id]:
        last_msg[group_id] = {"text": msg, "id": message.id}
        repeat_count[group_id] = 0
    else:
        repeat_count[group_id] += 1
        last_repeat_msg[group_id] = ""
        if repeat_count[group_id] >= 2:
            await client.send_message(group_id, t_msg)
            repeat_count[group_id] = 0
            last_msg[group_id] = {}
            last_repeat_msg[group_id] = msg
    raise ContinuePropagation
