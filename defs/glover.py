from configparser import RawConfigParser
from typing import Union
from distutils.util import strtobool

# [Basic]
ipv6: Union[bool, str] = "False"
config = RawConfigParser()
config.read("config.ini")
ipv6 = config.get("basic", "ipv6", fallback=ipv6)
try:
    ipv6 = strtobool(ipv6)
except ValueError:
    ipv6 = False
