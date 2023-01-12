import logging
import pyrogram
import httpx

from models.sqlite import Sqlite
from defs.glover import api_id, api_hash, ipv6
from scheduler import scheduler
from logging import getLogger, INFO, ERROR, StreamHandler, basicConfig
from coloredlogs import ColoredFormatter
from cashews import cache

from models.temp_fix import temp_fix

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

if not scheduler.running:
    scheduler.start()
# Init client


class UserMe:
    username = "iShotaBot"
    id = 2144128213


user_me = UserMe()
sqlite = Sqlite()
bot = pyrogram.Client(
    "bot", api_id=api_id, api_hash=api_hash, ipv6=ipv6, plugins=dict(root="modules")
)
# temp fix topics group
setattr(pyrogram.types.Message, "old_parse", getattr(pyrogram.types.Message, "_parse"))
setattr(pyrogram.types.Message, "_parse", temp_fix)
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.72 Safari/537.36"
}
request = httpx.AsyncClient(timeout=60.0, headers=headers)
