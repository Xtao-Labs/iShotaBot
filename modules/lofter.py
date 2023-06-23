from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from defs.lofter import get_loft, input_media, get_loft_user, lofter_user_link
from init import bot


@bot.on_message(filters.incoming & filters.text & filters.regex(r"lofter.com"))
async def lofter_share(_: Client, message: Message):
    if not message.text:
        return
    static = "static" in message.text
    try:
        for num in range(len(message.entities)):
            entity = message.entities[num]
            if entity.type == MessageEntityType.URL:
                url = message.text[entity.offset : entity.offset + entity.length]
            elif entity.type == MessageEntityType.TEXT_LINK:
                url = entity.url
            else:
                continue
            if "/post/" in url:
                img = await get_loft(url)
                if not img:
                    continue
                if len(img) == 1:
                    await img[0].reply_to(message, static=static)
                else:
                    await message.reply_media_group(
                        media=await input_media(img[:9], static), quote=True
                    )
            elif "front/blog" not in url:
                text, avatar, username, status_link = await get_loft_user(url)
                if avatar:
                    await message.reply_photo(
                        avatar,
                        caption=text,
                        quote=True,
                        reply_markup=lofter_user_link(username, status_link),
                    )
                else:
                    await message.reply_text(
                        text,
                        quote=True,
                        disable_web_page_preview=True,
                        reply_markup=lofter_user_link(username, status_link),
                    )
    except Exception as e:
        print(e)
    raise ContinuePropagation
