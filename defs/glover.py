from configparser import RawConfigParser
from typing import Union, List
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
splash_channel: int = 0
splash_channel_username: str = ""
bilifav_id: int = 0
bilifav_channel: int = 0
bilifav_channel_username: str = ""
exchange_channel: int = 0
# [api]
amap_key: str = ""
bili_auth_user_str: str = ""
bili_auth_chat_str: str = ""
caiyun_weather: str = ""
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
splash_channel = config.getint("post", "splash_channel", fallback=splash_channel)
splash_channel_username = config.get(
    "post", "splash_channel_username", fallback=splash_channel_username
)
bilifav_id = config.getint("post", "bilifav_id", fallback=bilifav_id)
bilifav_channel = config.getint("post", "bilifav_channel", fallback=bilifav_channel)
bilifav_channel_username = config.get(
    "post", "bilifav_channel_username", fallback=bilifav_channel_username
)
exchange_channel = config.getint("post", "exchange_channel", fallback=exchange_channel)
amap_key = config.get("api", "amap_key", fallback=amap_key)
bili_auth_user_str = config.get("api", "bili_auth_user", fallback=bili_auth_user_str)
bili_auth_chat_str = config.get("api", "bili_auth_chat", fallback=bili_auth_chat_str)
try:
    bili_auth_user: List[int] = list(map(int, bili_auth_user_str.split(",")))
    bili_auth_chat: List[int] = list(map(int, bili_auth_chat_str.split(",")))
except ValueError:
    bili_auth_user: List[int] = []
    bili_auth_chat: List[int] = []
caiyun_weather = config.get("api", "caiyun_weather", fallback=caiyun_weather)
# bsky
bsky_username = config.get("bsky", "username", fallback="")
bsky_password = config.get("bsky", "password", fallback="")
# predict
predict_url = config.get("predict", "url", fallback="")
predict_token = config.get("predict", "token", fallback="")
try:
    ipv6 = bool(strtobool(ipv6))
except ValueError:
    ipv6 = False


def save_config():
    config.write(open("config.ini", "w", encoding="utf-8"))
