import contextlib
from urllib.parse import quote

from defs.glover import amap_key

from init import request

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrogram.types import Message

REQUEST_URL = f"https://restapi.amap.com/v3/geocode/geo?key={amap_key}&"


async def get_geo_data_from_text(message: str):
    cmd = message.split()
    mode, lat, lon = "address", 0, 0  # noqa
    with contextlib.suppress(ValueError, IndexError):
        lat, lon = float(cmd[0]), float(cmd[1])
        mode = "location"
    return await get_geo_data(mode, lat, lon, message)


async def get_geo_data_from_message(message: "Message"):
    mode, lat, lon = "address", 0, 0  # noqa
    with contextlib.suppress(ValueError, IndexError):
        lat, lon = float(message.command[1]), float(message.command[2])
        mode = "location"
    return await get_geo_data(mode, lat, lon, " ".join(message.command[1:]))


async def get_geo_data(mode: str, lat: float, lon: float, text: str):
    if mode == "location":
        try:
            geo = (
                await request.get(
                    f"{REQUEST_URL.replace('/geo?', '/regeo?')}location={lat},{lon}"
                )
            ).json()
            formatted_address = geo["regeocode"]["formatted_address"]
            assert isinstance(formatted_address, str)
            return lat, lon, formatted_address
        except (KeyError, AssertionError):
            return None, None, None
    else:
        try:
            geo = (
                await request.get(f"{REQUEST_URL}address={quote(text).strip()}")
            ).json()
            formatted_address = geo["geocodes"][0]["formatted_address"]
            lat, lon = geo["geocodes"][0]["location"].split(",")
            return lat, lon, formatted_address
        except (KeyError, AssertionError, IndexError, ValueError):
            return None, None, None
