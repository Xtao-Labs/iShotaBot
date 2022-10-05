from pyrogram import Client, filters
from defs.glover import admin
from pyrogram.types import Message

from defs.post import LofterPost


@Client.on_message(filters.incoming & filters.private & filters.user(admin) &
                   filters.command(["lofter_post"]))
async def lofter_post_command(client: Client, message: Message):
    """
        抓取 lofter 粮单
    """
    data = message.text.split(" ")
    offset = 0
    if len(data) < 2:
        await message.reply("参数错误")
        return
    elif len(data) == 2:
        url = data[1]
    else:
        url = data[1]
        offset = data[2]
    data = LofterPost(url, offset)
    client.loop.create_task(data.upload(message))
