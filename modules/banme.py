import re
import random
from time import time

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from init import user_me


@Client.on_message(filters.incoming & ~filters.edited & filters.group &
                   filters.command(["banme", f"banme@{user_me.username}"]))
async def ban_me_command(client: Client, message: Message):
    args = str(message.text).strip()
    # 检查是否有倍数参数
    if multiple_text := re.search(r'^(\d+)倍$', args):
        multiple = int(multiple_text.groups()[0])
    else:
        multiple = 1

    # 检查bot和用户身份
    if not (await client.get_chat_member(message.chat.id, "self")).status == "administrator":
        await message.reply('Bot非群管理员, 无法执行禁言操作QAQ')
        return
    if not message.from_user:
        # 频道
        await message.reply('你也是个管理, 别来凑热闹OvO')
        return
    member = (await client.get_chat_member(message.chat.id, message.from_user.id)).status
    if member in ["creator", "administrator"]:
        await message.reply('你也是个管理, 别来凑热闹OvO')
        return

    # 随机禁言时间
    random_time = 2 * int(random.gauss(128 * multiple, 640 * multiple // 10))
    act_time = 60 if random_time < 60 else (random_time if random_time < 2591940 else 2591940)
    msg = f'既然你那么想被口球的话, 那我就成全你吧!\n送你一份{act_time // 60}分{act_time % 60}秒禁言套餐哦, 谢谢惠顾~'

    await client.restrict_chat_member(message.chat.id, message.from_user.id, ChatPermissions(), int(time() + act_time))
    await message.reply(msg)
