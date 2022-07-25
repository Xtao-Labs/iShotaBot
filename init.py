import logging

import httpx

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


class UserMe:
    username = "iShotaBot"
    id = 2144128213


user_me = UserMe()
bot = Client("bot", ipv6=ipv6, plugins=dict(root="modules"))
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.72 Safari/537.36"
}
request = httpx.AsyncClient(timeout=10.0, headers=headers)
