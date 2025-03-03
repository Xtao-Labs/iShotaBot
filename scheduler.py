import contextlib
import datetime
from pathlib import Path

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram.types import Message

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Shanghai"))


async def delete_message(message: Message) -> bool:
    with contextlib.suppress(Exception):
        await message.delete()
        return True
    return False


async def delete_file(path: str):
    path = Path(path)
    if path.exists():
        path.unlink(missing_ok=True)


def add_delete_message_job(message: Message, delete_seconds: int = 60):
    scheduler.add_job(
        delete_message,
        "date",
        id=f"{message.chat.id}|{message.id}|delete_message",
        name=f"{message.chat.id}|{message.id}|delete_message",
        args=[message],
        run_date=datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        + datetime.timedelta(seconds=delete_seconds),
        replace_existing=True,
    )


def add_delete_file_job(path: str, delete_seconds: int = 3600):
    scheduler.add_job(
        delete_file,
        "date",
        id=f"{hash(path)}|delete_file",
        name=f"{hash(path)}|delete_file",
        args=[path],
        run_date=datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        + datetime.timedelta(seconds=delete_seconds),
        replace_existing=True,
    )


async def reply_message(
    msg: Message, text: str, delete_origin: bool = True, *args, **kwargs
):
    reply_msg = await msg.reply(text, *args, **kwargs)
    add_delete_message_job(reply_msg)
    if delete_origin:
        add_delete_message_job(msg)
