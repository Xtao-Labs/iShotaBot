from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from defs.lofter import get_loft, input_media


@Client.on_message(filters.incoming & filters.text &
                   filters.regex(r"lofter.com/post/"))
async def lofter_share(_: Client, message: Message):
    if not message.text:
        return
    static = "static" in message.text
    try:
        for num in range(len(message.entities)):
            entity = message.entities[num]
            if entity.type == MessageEntityType.URL:
                url = message.text[entity.offset:entity.offset + entity.length]
            elif entity.type == MessageEntityType.TEXT_LINK:
                url = entity.url
            else:
                continue
            img = await get_loft(url)
            if not img:
                continue
            if len(img) == 1:
                await img[0].reply_to(message, static=static)
            else:
                await message.reply_media_group(media=await input_media(img[:9], static), quote=True)
    except Exception as e:
        print(e)
        breakpoint()
    raise ContinuePropagation
