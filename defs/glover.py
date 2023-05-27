from configparser import RawConfigParser
from typing import Union
from distutils.util import strtobool

# [pyrogram]
api_id: int = 0
api_hash: str = ""
# [Basic]
ipv6: Union[bool, str] = "False"
# [post]
admin: int = 0
lofter_channel: int = 0
lofter_channel_username: str = ""
# [api]
amap_key: str = ""
bili_cookie: str = ""
config = RawConfigParser()
config.read("config.ini")
api_id = config.getint("pyrogram", "api_id", fallback=api_id)
api_hash = config.get("pyrogram", "api_hash", fallback=api_hash)
ipv6 = config.get("basic", "ipv6", fallback=ipv6)
admin = config.getint("post", "admin", fallback=admin)
lofter_channel = config.getint("post", "lofter_channel", fallback=lofter_channel)
lofter_channel_username = config.get(
    "post", "lofter_channel_username", fallback=lofter_channel_username
)
amap_key = config.get("api", "amap_key", fallback=amap_key)
bili_cookie = config.get("api", "bili_cookie", fallback=bili_cookie)
try:
    ipv6 = bool(strtobool(ipv6))
except ValueError:
    ipv6 = False
