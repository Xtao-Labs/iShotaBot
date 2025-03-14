import re
from os import sep
from typing import Optional

import qrcode
import string

from bilibili_api import Credential, ResponseCodeException
from bilibili_api.audio import Audio
from bilibili_api.video import Video
from bilibili_api.utils.network import Api
from pyrogram import ContinuePropagation
from qrcode.image.pil import PilImage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from defs.cookie import get_bili_cookie, get_bili_browser_cookie, set_bili_cookie
from defs.browser import get_browser
from init import request


def from_cookie_get_credential() -> Optional[Credential]:
    """
    从 cookie 中获取 Credential 对象。

    Returns:
        Credential: Credential 对象。
    """
    cookie = get_bili_cookie()
    try:
        sessdata = cookie["SESSDATA"]
        bili_jct = cookie["bili_jct"]
        buvid3 = cookie["buvid3"]
        buvid4 = cookie["buvid4"]
        dedeuserid = cookie["DedeUserID"]
    except KeyError:
        return None
    try:
        ac_time_value = cookie["ac_time_value"]
    except KeyError:
        ac_time_value = None
    return Credential(
        sessdata=sessdata,
        bili_jct=bili_jct,
        buvid3=buvid3,
        buvid4=buvid4,
        dedeuserid=dedeuserid,
        ac_time_value=ac_time_value,
    )


credential = from_cookie_get_credential()


def set_cookie_from_cred(new_cred: Credential) -> None:
    cookie = get_bili_cookie()
    if new_cred.sessdata:
        cookie["SESSDATA"] = new_cred.sessdata
    if new_cred.bili_jct:
        cookie["bili_jct"] = new_cred.bili_jct
    if new_cred.buvid3:
        cookie["buvid3"] = new_cred.buvid3
    if new_cred.buvid4:
        cookie["buvid4"] = new_cred.buvid4
    if new_cred.dedeuserid:
        cookie["DedeUserID"] = new_cred.dedeuserid
    if new_cred.ac_time_value:
        cookie["ac_time_value"] = new_cred.ac_time_value
    set_bili_cookie(cookie)


async def check_and_refresh_credential() -> None:
    """
    检查并刷新 Credential 对象。
    """
    if await credential.check_refresh():
        await credential.refresh()
        set_cookie_from_cred(credential)


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
            next_str = next_str[i - 1 :]
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
        if not p:
            continue
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
    resp = await request.head(url, follow_redirects=True)
    r = str(resp.url)
    return r


def create_video(cid) -> Optional[Video]:
    v = None
    if cid[:2] == "av":
        v = Video(aid=int(cid[2:]), credential=credential)
    elif cid[:2] == "BV":
        v = Video(bvid=cid, credential=credential)
    return v


def create_audio(aid: str) -> Optional[Audio]:
    a = None
    if aid[:2] == "au":
        a = Audio(auid=int(aid[2:]), credential=credential)
    return a


async def video_info_get(cid):
    v = create_video(cid)
    if not v:
        return None
    video_info = await v.get_info()
    return video_info


def numf(num: int):
    if num < 10000:
        view = str(num)
    elif num < 100000000:
        view = ("%.2f" % (num / 10000)) + "万"
    else:
        view = ("%.2f" % (num / 100000000)) + "亿"
    return view


async def get_user_info(mid: int):
    api = "https://api.bilibili.com/x/web-interface/card"
    params = {"mid": mid}
    result = await Api(api, "GET", credential=credential).update_params(**params).result
    return result


async def binfo_up_info(video_info: dict):
    # UP主
    # 等级 0-4 \uE6CB-F 5-6\uE6D0-1
    # UP \uE723
    if "staff" in video_info:
        up_list = []
        for up in video_info["staff"]:
            up_mid = up["mid"]
            up_data = await get_user_info(up_mid)
            nickname_color, level = (
                up_data["card"]["vip"]["nickname_color"],
                up_data["card"]["level_info"]["current_level"],
            )
            up_list.append(
                {
                    "name": up["name"],
                    "up_title": up["title"],
                    "face": up["face"],
                    "color": nickname_color if nickname_color != "" else "black",
                    "follower": up["follower"],
                    "level": level,
                }
            )
    else:
        up_mid = video_info["owner"]["mid"]
        up_data = await get_user_info(up_mid)
        nickname_color, level = (
            up_data["card"]["vip"]["nickname_color"],
            up_data["card"]["level_info"]["current_level"],
        )
        name, face, follower = (
            up_data["card"]["name"],
            up_data["card"]["face"],
            up_data["follower"],
        )
        up_list = [
            {
                "name": name,
                "up_title": "UP主",
                "face": face,
                "color": nickname_color if nickname_color != "" else "black",
                "follower": follower,
                "level": level,
            }
        ]
    return up_list


async def binfo_image_create(video_info: dict):
    bg_y = 0
    # 封面
    pic_url = video_info["pic"]
    pic_get = (await request.get(pic_url)).content
    pic_bio = BytesIO(pic_get)
    pic = Image.open(pic_bio)
    pic = pic.resize((560, 350))
    pic_time_box = Image.new("RGBA", (560, 50), (0, 0, 0, 150))
    pic.paste(pic_time_box, (0, 300), pic_time_box)
    bg_y += 350 + 20

    # 时长
    minutes, seconds = divmod(video_info["duration"], 60)
    hours, minutes = divmod(minutes, 60)
    video_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    tiem_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 30
    )
    draw = ImageDraw.Draw(pic)
    draw.text((10, 305), video_time, "white", tiem_font)

    # 分区
    tname = video_info["tname"]
    _, _, tname_x, _ = tiem_font.getbbox(tname)
    draw.text((560 - tname_x - 10, 305), tname, "white", tiem_font)

    # 标题
    title = video_info["title"]
    title_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 25
    )
    title_cut_str = "\n".join(cut_text(title, 40))
    _, _, _, title_text_y = draw.multiline_textbbox((0, 0), title_cut_str, title_font)
    title_bg = Image.new("RGB", (560, title_text_y + 23), "#F5F5F7")
    draw = ImageDraw.Draw(title_bg)
    draw.text((15, 10), title_cut_str, "black", title_font)
    title_bg_y = title_bg.size[1]
    bg_y += title_bg_y

    # 简介
    dynamic = "该视频没有简介" if video_info["desc"] == "" else video_info["desc"]
    dynamic_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-semibold.ttf", 18
    )
    dynamic_cut_str = "\n".join(cut_text(dynamic, 58))
    _, _, _, dynamic_text_y = draw.multiline_textbbox(
        (0, 0), dynamic_cut_str, dynamic_font
    )
    dynamic_bg = Image.new("RGB", (560, dynamic_text_y + 24), "#F5F5F7")
    draw = ImageDraw.Draw(dynamic_bg)
    draw.rectangle((0, 0, 580, dynamic_text_y + 24), "#E1E1E5")
    draw.text((10, 10), dynamic_cut_str, "#474747", dynamic_font)
    dynamic_bg_y = dynamic_bg.size[1]
    bg_y += dynamic_bg_y

    # 视频数据
    icon_font = ImageFont.truetype(f"resources{sep}font{sep}vanfont.ttf", 46)
    icon_color = (247, 145, 185)
    info_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 26
    )

    view = numf(video_info["stat"]["view"])  # 播放 \uE6E6
    danmaku = numf(video_info["stat"]["danmaku"])  # 弹幕 \uE6E7
    favorite = numf(video_info["stat"]["favorite"])  # 收藏 \uE6E1
    coin = numf(video_info["stat"]["coin"])  # 投币 \uE6E4
    like = numf(video_info["stat"]["like"])  # 点赞 \uE6E0

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

    try:
        up_list = await binfo_up_info(video_info)
    except ResponseCodeException as e:
        print(f"获取UP主信息时发生错误：{e}")
        up_list = []

    up_num = len(up_list)
    up_bg = Image.new("RGB", (560, 20 + (up_num * 120) + 20), "#F5F5F7")
    draw = ImageDraw.Draw(up_bg)
    face_size = (80, 80)
    mask = Image.new("RGBA", face_size, color=(0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        (0, 0, face_size[0], face_size[1]), fill=(0, 0, 0, 255)  # type: ignore
    )
    name_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 24
    )
    up_title_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-bold.ttf", 20
    )
    follower_font = ImageFont.truetype(
        f"resources{sep}font{sep}sarasa-mono-sc-semibold.ttf", 22
    )

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
        face_get = (await request.get(face_url)).content
        face_bio = BytesIO(face_get)
        face = Image.open(face_bio)
        face.convert("RGB")
        face = face.resize(face_size)
        up_bg.paste(face, (20, 20 + (i * 120)), mask)
        # 名字
        draw.text((160, 25 + (i * 120)), up["name"], up["color"], name_font)
        _, _, name_size_x, _ = name_font.getbbox(up["name"])
        # 等级
        draw.text(
            (160 + name_size_x + 10, 16 + (i * 120)), up_level, level_color, icon_font
        )
        # 身份
        _, _, up_title_size_x, up_title_size_y = up_title_font.getbbox(up["up_title"])
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
    qr.add_data("https://b23.tv/" + video_info["bvid"])
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


async def get_dynamic_screenshot_pc(dynamic_id):
    """电脑端动态截图"""
    url = f"https://t.bilibili.com/{dynamic_id}"
    browser = await get_browser()
    context = await browser.new_context(
        viewport={"width": 2560, "height": 1080},
        device_scale_factor=2,
    )
    await context.add_cookies(get_bili_browser_cookie())
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=10000)
        # 动态被删除或者进审核了
        if page.url == "https://www.bilibili.com/404":
            return None
        card = await page.query_selector(".bili-dyn-item__main")
        assert card
        clip = await card.bounding_box()
        assert clip
        return await page.screenshot(clip=clip, full_page=True)
    except Exception:
        print(f"截取动态时发生错误：{url}")
        return await page.screenshot(full_page=True)
    finally:
        await context.close()
