import contextlib

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from defs.lofter import get_loft, input_media, gen_button


@Client.on_message(filters.incoming & filters.text &
                   filters.regex(r"lofter.com/post/"))
async def lofter_share(_: Client, message: Message):
    if not message.text:
        return
    with contextlib.suppress(Exception):
        for num in range(len(message.entities)):
            entity = message.entities[num]
            if entity.type == MessageEntityType.URL:
                url = message.text[entity.offset:entity.offset + entity.length]
            elif entity.type == MessageEntityType.TEXT_LINK:
                url = entity.url
            else:
                continue
            img, text = await get_loft(url)
            if not img:
                continue
            if len(img) == 1:
                await message.reply_photo(img[0], caption=text, quote=True, reply_markup=gen_button(url))
            else:
                await message.reply_media_group(media=input_media(img[:9], text), quote=True)
    raise ContinuePropagation
