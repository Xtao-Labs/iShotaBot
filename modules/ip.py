from urllib.parse import urlparse

from pyrogram import Client, filters
from pyrogram.types import Message

from defs.ip import ip_info
from init import user_me, request


@Client.on_message(filters.incoming & filters.command(["ip", f"ip@{user_me.username}"]))
async def ip_command(_: Client, message: Message):
    msg = await message.reply("正在查询中...")
    rep_text = ""
    reply = message.reply_to_message
    if reply:
        if reply.entities:
            for num in range(0, len(reply.entities)):
                url = reply.text[
                    reply.entities[num].offset : reply.entities[num].offset
                    + reply.entities[num].length
                ]
                url = urlparse(url)
                if url.hostname or url.path:
                    if url.hostname:
                        url = url.hostname
                    else:
                        url = url.path
                    ipinfo_json = (
                        await request.get(
                            "http://ip-api.com/json/"
                            + url
                            + "?fields=status,message,country,regionName,city,"
                            "lat,lon,isp,"
                            "org,as,mobile,proxy,hosting,query"
                        )
                    ).json()
                    if ipinfo_json["status"] == "fail":
                        pass
                    elif ipinfo_json["status"] == "success":
                        rep_text = ip_info(url, ipinfo_json)
    text = ""
    if message.entities:
        for num in range(0, len(message.entities)):
            url = message.text[
                message.entities[num].offset : message.entities[num].offset
                + message.entities[num].length
            ]
            url = urlparse(url)
            if url.hostname or url.path:
                if url.hostname:
                    url = url.hostname
                else:
                    url = url.path
                ipinfo_json = (
                    await request.get(
                        "http://ip-api.com/json/"
                        + url
                        + "?fields=status,message,country,regionName,city,lat,"
                        "lon,isp,"
                        "org,as,mobile,proxy,hosting,query"
                    )
                ).json()
                if ipinfo_json["status"] == "fail":
                    pass
                elif ipinfo_json["status"] == "success":
                    text = ip_info(url, ipinfo_json)
        if text == "":
            url = message.text[4:]
            if not url == "":
                ipinfo_json = (
                    await request.get(
                        "http://ip-api.com/json/"
                        + url
                        + "?fields=status,message,country,regionName,city,lat,"
                        "lon,isp,"
                        "org,as,mobile,proxy,hosting,query"
                    )
                ).json()
                if ipinfo_json["status"] == "fail":
                    pass
                elif ipinfo_json["status"] == "success":
                    text = ip_info(url, ipinfo_json)
    if rep_text == "" and text == "":
        await msg.edit("没有找到要查询的 ip/域名 ...")
    elif not rep_text == "" and not text == "":
        await msg.edit(f"{rep_text}\n================\n{text}")
    else:
        await msg.edit(f"{rep_text}{text}")
