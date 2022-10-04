import re
from io import BytesIO

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message

from PIL import Image

from defs.mihoyo_bbs import get_mihoyo_screenshot
from defs.button import gen_button, Button


@Client.on_message(filters.incoming & filters.text &
                   filters.regex(r'(https://)?(m\.)?bbs.mihoyo.com/.+/article/\d+'))
async def bili_dynamic(_: Client, message: Message):
    # sourcery skip: use-named-expression
    try:
        p = re.compile(r'(https://)?(m\.)?bbs.mihoyo.com/.+/article/\d+')
        article = p.search(message.text)
        if article:
            article_url = article.group()
            if not article_url.startswith(('https://', 'http://')):
                article_url = f'https://{article_url}'
            image = await get_mihoyo_screenshot(article_url)
            if image:
                # 将bytes结果转化为字节流
                photo = BytesIO(image)
                photo.name = "screenshot.png"
                pillow_photo = Image.open(BytesIO(image))
                width, height = pillow_photo.size
                if abs(height - width) > 1300:
                    await message.reply_document(
                        document=photo,
                        quote=True,
                        reply_markup=gen_button([Button(0, "Link", article_url)])
                    )
                else:
                    await message.reply_photo(
                        photo,
                        quote=True,
                        reply_markup=gen_button([Button(0, "Link", article_url)])
                    )
    except Exception as e:
        print(f"截取米哈游帖子时发生错误：{e}")
    raise ContinuePropagation
