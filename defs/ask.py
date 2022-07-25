import re
import secrets
from typing import List
from init import bot


async def how_many(message: str) -> str:
    while re.findall("几|多少", message):
        message = message.replace("几", str(secrets.choice(range(99))), 1)
        message = message.replace("多少", str(secrets.choice(range(99))), 1)
    return message


async def what_time(message: str) -> str:
    time = ["早上", "中午", "晚上", "今天", "明天", "下周", "下个月", "明年"]
    while re.findall("什么时候|啥时候", message):
        message = message.replace("什么时候", secrets.choice(time), 1)
        message = message.replace("啥时候", secrets.choice(time), 1)
    return message


async def how_long(message: str) -> str:
    unit = ["秒", "小时", "天", "周", "月", "年", "世纪"]
    while re.findall("多久|多长时间", message):
        message = message.replace("多久", str(secrets.choice(range(99))) + secrets.choice(unit), 1)
        message = message.replace("多长时间", str(secrets.choice(range(99))) + secrets.choice(unit), 1)
    return message


async def hif(message: str) -> str:
    keyword = list(set(re.findall(r"(.)不\1", message)))
    for k in keyword:
        k = f"{k}不{k}"
        if secrets.choice([True, False]):
            message = message.replace(k, k[:1])
        else:
            message = message.replace(k, k[1:])
    return message


async def who(message: str, group_id: int) -> str:
    group_member_list = await bot.get_chat_member(group_id)
    member_list: List[str] = [n.first_name for n in group_member_list]
    while "谁" in message:
        member_name = member_list[secrets.choice(range(len(member_list) - 1))]
        message = message.replace("谁", member_name, 1)
    return message


async def handle_pers(message: str) -> str:
    message_list = list(message)
    for i in range(len(message_list)):
        if message_list[i] == "我":
            message_list[i] = "你"
            continue
        if message[i] == "你":
            message_list[i] = "我"
            continue

    message = "".join(message_list)

    message = message.replace("bot", "我")
    message = message.replace("Bot", "我")
    message = message.replace("吗", "")
    message = message.replace("呢", "")
    message = message.replace("？", "")
    message = message.replace("?", "")

    return message
