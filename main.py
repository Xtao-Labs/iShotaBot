import logging

from pyrogram.types import User

from defs.glover import ipv6
from pyrogram import Client
from logging import getLogger, INFO, ERROR, StreamHandler, basicConfig
from coloredlogs import ColoredFormatter
from cashews import cache

# Config cache
cache.setup("mem://")
# Enable logging
logs = getLogger("iShotaBot")
logging_format = "%(levelname)s [%(asctime)s] [%(name)s] %(message)s"
logging_handler = StreamHandler()
logging_handler.setFormatter(ColoredFormatter(logging_format))
root_logger = getLogger()
root_logger.setLevel(ERROR)
root_logger.addHandler(logging_handler)
basicConfig(level=INFO)
logs.setLevel(INFO)
logger = logging.getLogger("iShotaBot")
# Init client
bot = Client("bot", ipv6=ipv6)
user_me = User(id=777000)


async def save_id():
    global user_me
    async with bot:
        me = await bot.get_me()
    user_me = me


if __name__ == "__main__":
    bot.run(save_id())
    logs.info(f"@{user_me.username} 运行成功！")
    bot.run()
