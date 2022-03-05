import logging
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
bot = Client("bot", ipv6=ipv6, plugins=dict(root="plugins"))
bot.start()
user_me = bot.get_me()
bot.stop()
bot = Client("bot", ipv6=ipv6)
