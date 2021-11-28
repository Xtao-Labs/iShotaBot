import re
from os import sep

import httpx
import qrcode
import string

from pyrogram import ContinuePropagation
from qrcode.image.pil import PilImage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def cut_text(old_str, cut):
    """
    :说明: `get_cut_str`
    > 长文本自动换行切分
    :参数:
      * `str: [type]`: 文本
      * `cut: [type]`: 换行宽度，需要至少大于20
    :返回:
      - `List`: 切分后的文本列表
    """
    punc = """，,、。.？?）》】“"‘'；;：:！!·`~%^& """
    si = 0
    i = 0
    next_str = old_str
    str_list = []
    for s in next_str:
        if s in string.printable:
            si += 1
        else:
            si += 2
        i += 1
        if next_str[0] == "\n":
            next_str = next_str[1:]
        elif s == "\n":
            str_list.append(next_str[: i - 1])
            next_str = next_str[i - 1:]
            si = 0
            i = 0
            continue
        if si > cut:
            try:
                if next_str[i] in punc:
                    i += 1
                if next_str[i] in string.ascii_letters:
                    for j in range(i, i - 18, -1):
                        if next_str[j] == " ":
                            i = j + 1
                            break
            except IndexError:
                str_list.append(next_str)
                return str_list
            str_list.append(next_str[:i])
            next_str = next_str[i:]
            si = 0
            i = 0
    str_list.append(next_str)
    i = 0
    non_wrap_str = []
    for p in str_list:
        if p[-1] == "\n":
            p = p[:-1]
        non_wrap_str.append(p)
        i += 1
    return non_wrap_str


async def b23_extract(text):
    b23 = re.compile(r"b23.tv\\/(\w+)").search(text)
    if not b23:
        b23 = re.compile(r"b23.tv/(\w+)").search(text)
    try:
        assert b23 is not None
        url = f"https://b23.tv/{b23[1]}"
    except AssertionError:
        raise ContinuePropagation
    resp = httpx.get(url)
    r = str(resp.url)
    return r


async def video_info_get(cid):
    if cid[:2] == "av":
        video_info = httpx.get(
            f"http://api.bilibili.com/x/web-interface/view?aid={cid[2:]}"
        )
        video_info = video_info.json()
    elif cid[:2] == "BV":
        video_info = httpx.get(f"http://api.bilibili.com/x/web-interface/view?bvid={cid}")
        video_info = video_info.json()
    else:
        return
    return video_info


def numf(num: int):
    if num < 10000:
        view = str(num)
    elif num < 100000000:
        view = ("%.2f" % (num / 10000)) + "万"
    else:
        view = ("%.2f" % (num / 100000000)) + "亿"
    return view


def binfo_image_create(video_info: dict):
    bg_y = 0
    # 封面
    pic_url = video_info["data"]["pic"]
    pic_get = httpx.get(pic_url).content
    pic_bio = BytesIO(pic_get)
    pic = Image.open(pic_bio)
    pic = pic.resize((560, 350))
    pic_time_box = Image.new("RGBA", (560, 50), (0, 0, 0, 150))
    pic.paste(pic_time_box, (0, 300), pic_time_box)
    bg_y += 350 + 20

    # 时长
    minutes, seconds = divmod(video_info["data"]["duration"], 60)
    hours, minutes = divmod(minutes, 60)
    video_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    tiem_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 30)
    draw = ImageDraw.Draw(pic)
    draw.text((10, 305), video_time, "white", tiem_font)

    # 分区
    tname = video_info["data"]["tname"]
    tname_x, _ = tiem_font.getsize(tname)
    draw.text((560 - tname_x - 10, 305), tname, "white", tiem_font)

    # 标题
    title = video_info["data"]["title"]
    title_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 25)
    title_cut_str = "\n".join(cut_text(title, 40))
    _, title_text_y = title_font.getsize_multiline(title_cut_str)
    title_bg = Image.new("RGB", (560, title_text_y + 23), "#F5F5F7")
    draw = ImageDraw.Draw(title_bg)
    draw.text((15, 10), title_cut_str, "black", title_font)
    title_bg_y = title_bg.size[1]
    bg_y += title_bg_y

    # 简介
    dynamic = (
        "该视频没有简介" if video_info["data"]["desc"] == "" else video_info["data"]["desc"]
    )
    dynamic_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-semibold.ttf", 18)
    dynamic_cut_str = "\n".join(cut_text(dynamic, 58))
    _, dynamic_text_y = dynamic_font.getsize_multiline(dynamic_cut_str)
    dynamic_bg = Image.new("RGB", (560, dynamic_text_y + 24), "#F5F5F7")
    draw = ImageDraw.Draw(dynamic_bg)
    draw.rectangle((0, 0, 580, dynamic_text_y + 24), "#E1E1E5")
    draw.text((10, 10), dynamic_cut_str, "#474747", dynamic_font)
    dynamic_bg_y = dynamic_bg.size[1]
    bg_y += dynamic_bg_y

    # 视频数据
    icon_font = ImageFont.truetype(f"resources{sep}font{sep}vanfont.ttf", 46)
    icon_color = (247, 145, 185)
    info_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 26)

    view = numf(video_info["data"]["stat"]["view"])  # 播放 \uE6E6
    danmaku = numf(video_info["data"]["stat"]["danmaku"])  # 弹幕 \uE6E7
    favorite = numf(video_info["data"]["stat"]["favorite"])  # 收藏 \uE6E1
    coin = numf(video_info["data"]["stat"]["coin"])  # 投币 \uE6E4
    like = numf(video_info["data"]["stat"]["like"])  # 点赞 \uE6E0

    info_bg = Image.new("RGB", (560, 170), "#F5F5F7")
    draw = ImageDraw.Draw(info_bg)
    draw.text((5 + 10, 20), "\uE6E0", icon_color, icon_font)
    draw.text((5 + 64, 27), like, "#474747", info_font)
    draw.text((5 + 10 + 180, 20), "\uE6E4", icon_color, icon_font)
    draw.text((5 + 64 + 180, 27), coin, "#474747", info_font)
    draw.text((5 + 10 + 180 + 180, 20), "\uE6E1", icon_color, icon_font)
    draw.text((5 + 64 + 180 + 180, 27), favorite, "#474747", info_font)
    draw.text((5 + 100, 93), "\uE6E6", icon_color, icon_font)
    draw.text((5 + 154, 100), view, "#474747", info_font)
    draw.text((5 + 100 + 210, 93), "\uE6E7", icon_color, icon_font)
    draw.text((5 + 154 + 210, 100), danmaku, "#474747", info_font)
    info_bg_y = info_bg.size[1]
    bg_y += info_bg_y

    # UP主
    # 等级 0-4 \uE6CB-F 5-6\uE6D0-1
    # UP \uE723

    if "staff" in video_info["data"]:
        up_list = []
        for up in video_info["data"]["staff"]:
            up_mid = up["mid"]
            up_data = httpx.get(
                f"https://api.bilibili.com/x/space/acc/info?mid={up_mid}"
            ).json()
            up_list.append(
                {
                    "name": up["name"],
                    "up_title": up["title"],
                    "face": up["face"],
                    "color": up_data["data"]["vip"]["nickname_color"]
                    if up_data["data"]["vip"]["nickname_color"] != ""
                    else "black",
                    "follower": up["follower"],
                    "level": up_data["data"]["level"],
                }
            )
    else:
        up_mid = video_info["data"]["owner"]["mid"]
        up_data = httpx.get(
            f"https://api.bilibili.com/x/space/acc/info?mid={up_mid}"
        ).json()
        up_stat = httpx.get(
            f"https://api.bilibili.com/x/relation/stat?vmid={up_mid}"
        ).json()
        up_list = [
            {
                "name": up_data["data"]["name"],
                "up_title": "UP主",
                "face": up_data["data"]["face"],
                "color": up_data["data"]["vip"]["nickname_color"]
                if up_data["data"]["vip"]["nickname_color"] != ""
                else "black",
                "follower": up_stat["data"]["follower"],
                "level": up_data["data"]["level"],
            }
        ]
    up_num = len(up_list)
    up_bg = Image.new("RGB", (560, 20 + (up_num * 120) + 20), "#F5F5F7")
    draw = ImageDraw.Draw(up_bg)
    face_size = (80, 80)
    mask = Image.new("RGBA", face_size, color=(0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        (0, 0, face_size[0], face_size[1]), fill=(0, 0, 0, 255)  # type: ignore
    )
    name_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 24)
    up_title_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 20)
    follower_font = ImageFont.truetype(f"resources{sep}font{sep}sarasa-mono-sc-semibold.ttf", 22)

    i = 0
    for up in up_list:
        if up["level"] == 0:
            up_level = "\uE6CB"
            level_color = (191, 191, 191)
        elif up["level"] == 1:
            up_level = "\uE6CC"
            level_color = (191, 191, 191)
        elif up["level"] == 2:
            up_level = "\uE6CD"
            level_color = (149, 221, 178)
        elif up["level"] == 3:
            up_level = "\uE6CE"
            level_color = (146, 209, 229)
        elif up["level"] == 4:
            up_level = "\uE6CF"
            level_color = (255, 179, 124)
        elif up["level"] == 5:
            up_level = "\uE6D0"
            level_color = (255, 108, 0)
        else:
            up_level = "\uE6D1"
            level_color = (255, 0, 0)

        # 头像
        face_url = up["face"]
        face_get = httpx.get(face_url).content
        face_bio = BytesIO(face_get)
        face = Image.open(face_bio)
        face.convert("RGB")
        face = face.resize(face_size)
        up_bg.paste(face, (20, 20 + (i * 120)), mask)
        # 名字
        draw.text((160, 25 + (i * 120)), up["name"], up["color"], name_font)
        name_size_x, _ = name_font.getsize(up["name"])
        # 等级
        draw.text(
            (160 + name_size_x + 10, 16 + (i * 120)), up_level, level_color, icon_font
        )
        # 身份
        up_title_size_x, up_title_size_y = up_title_font.getsize(up["up_title"])
        draw.rectangle(
            (
                60,
                10 + (i * 120),
                73 + up_title_size_x,
                18 + (i * 120) + up_title_size_y,
            ),
            "white",
            icon_color,
            3,
        )
        draw.text((67, 13 + (i * 120)), up["up_title"], icon_color, up_title_font)
        # 粉丝量
        draw.text(
            (162, 66 + (i * 120)),
            "粉丝 " + numf(up["follower"]),
            "#474747",
            follower_font,
        )
        i += 1

    up_bg_y = up_bg.size[1]
    bg_y += up_bg_y

    # 底部栏
    baner_bg = Image.new("RGB", (600, 170), icon_color)
    draw = ImageDraw.Draw(baner_bg)
    # 二维码
    qr = qrcode.QRCode(border=1)
    qr.add_data("https://b23.tv/" + video_info["data"]["bvid"])
    qr_image = qr.make_image(PilImage, fill_color=icon_color, back_color="#F5F5F7")
    qr_image = qr_image.resize((140, 140))
    baner_bg.paste(qr_image, (50, 10))
    # Logo
    # LOGO \uE725
    logo_font = ImageFont.truetype(f"resources{sep}font{sep}vanfont.ttf", 100)
    draw.text((300, 28), "\uE725", "#F5F5F7", logo_font)
    bg_y += 170

    video = Image.new("RGB", (600, bg_y + 40), "#F5F5F7")
    video.paste(pic, (20, 20))
    video.paste(title_bg, (20, 390))
    video.paste(dynamic_bg, (20, 390 + title_bg_y + 20))
    video.paste(info_bg, (20, 390 + title_bg_y + 20 + dynamic_bg_y + 20))
    video.paste(up_bg, (20, 390 + title_bg_y + 20 + dynamic_bg_y + 10 + info_bg_y))
    video.paste(
        baner_bg, (0, 390 + title_bg_y + 20 + dynamic_bg_y + 10 + info_bg_y + up_bg_y)
    )

    picture = BytesIO()
    video.save(picture, format="PNG")
    picture.name = "bilibili.png"

    return picture
