import textwrap
from io import BytesIO
from os import sep
from PIL import Image, ImageDraw, ImageFont


def process_pic(content) -> BytesIO:
    text = content
    para = textwrap.wrap(text, width=15)
    MAX_W = 480
    bk_img = Image.open(f"resources{sep}images{sep}luxun.jpg")
    font_path = f"resources{sep}font{sep}msyh.ttf"
    font = ImageFont.truetype(font_path, 37)
    font2 = ImageFont.truetype(font_path, 30)
    draw = ImageDraw.Draw(bk_img)
    current_h, pad = 300, 10
    for line in para:
        w, h = draw.textsize(line, font=font)
        draw.text(((MAX_W - w) / 2, current_h), line, font=font)
        current_h += h + pad
    draw.text((320, 400), "——鲁迅", font=font2, fill=(255, 255, 255))

    picture = BytesIO()
    bk_img.save(picture, format="PNG")
    picture.name = "luxun.png"

    return picture
