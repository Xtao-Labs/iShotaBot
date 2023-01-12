from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from defs.fanbox import parse_fanbox_url


@Client.on_message(filters.incoming & filters.text & filters.regex(r"fanbox.cc"))
async def fanbox_check(_: Client, message: Message):
    if not message.text:
        return
    try:
        for num in range(len(message.entities)):
            entity = message.entities[num]
            if entity.type == MessageEntityType.URL:
                url = message.text[entity.offset : entity.offset + entity.length]
            elif entity.type == MessageEntityType.TEXT_LINK:
                url = entity.url
            else:
                continue
            await parse_fanbox_url(url, message)
    except Exception as e:
        print(e)
    raise ContinuePropagation
