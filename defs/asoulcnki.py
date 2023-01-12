import time
from io import BytesIO
from PIL import Image
import httpx
import jinja2
import random
from os import sep
from init import logger
from defs.browser import html_to_pic
from defs.diff import diff_text

env = jinja2.Environment(enable_async=True)
with open(f"resources{sep}templates{sep}article.html", "r", encoding="utf-8") as f:
    article_data = f.read()
article_tpl = env.from_string(article_data)


async def check_text(text: str):
    try:
        url = "https://asoulcnki.asia/v1/api/check"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url=url, json={"text": text})
            result = resp.json()

        if result["code"] != 0:
            return None, None

        data = result["data"]
        if not data["related"]:
            return None, "没有找到重复的小作文捏"

        rate = data["rate"]
        related = data["related"][0]
        reply_url = str(related["reply_url"]).strip()
        reply = related["reply"]

        msg = [
            "枝网文本复制检测报告",
            "",
            "总复制比 {:.2f}%".format(rate * 100),
            f'相似小作文: <a href="{reply_url}">地点</a> - '
            f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reply["ctime"]))}',
        ]

        image = await render_reply(reply, diff=text)
        if not image:
            return None, "\n".join(msg)
        return image, "\n".join(msg)
    except Exception as e:
        logger.warning(f"Error in check_text: {e}")
        return None, None


async def random_text(keyword: str = ""):
    try:
        url = "https://asoulcnki.asia/v1/api/ranking"
        params = {"pageSize": 10, "pageNum": 1, "timeRangeMode": 0, "sortMode": 0}
        if keyword:
            params["keywords"] = keyword
        else:
            params["pageNum"] = random.randint(1, 100)

        async with httpx.AsyncClient() as client:
            resp = await client.get(url=url, params=params)
            result = resp.json()

        if result["code"] != 0:
            return None, None

        replies = result["data"]["replies"]
        if not replies:
            return None, "没有找到小作文捏"

        reply = random.choice(replies)
        image = await render_reply(reply)
        reply_url = (
            f"https://t.bilibili.com/{reply['dynamic_id']}/#reply{reply['rpid']}"
        )
        if not image:
            return None, f'<a href="{reply_url}">转到小作文</a>'
        return image, f'<a href="{reply_url}">转到小作文</a>'
    except Exception as e:
        logger.warning(f"Error in random_text: {e}")
        return None, None


async def render_reply(reply: dict, diff: str = ""):
    try:
        article = {}
        article["username"] = reply["m_name"]
        article["like"] = reply["like_num"]
        article["all_like"] = reply["similar_like_sum"]
        article["quote"] = reply["similar_count"]
        article["text"] = (
            diff_text(diff, reply["content"]) if diff else reply["content"]
        )
        article["time"] = time.strftime("%Y-%m-%d", time.localtime(reply["ctime"]))

        html = await article_tpl.render_async(article=article)
        img_raw = await html_to_pic(
            html, wait=0, viewport={"width": 500, "height": 100}
        )
        # 将bytes结果转化为字节流
        bytes_stream = BytesIO(img_raw)
        # 读取到图片
        img = Image.open(bytes_stream)
        imgByteArr = BytesIO()  # 初始化一个空字节流
        img.save(imgByteArr, format("PNG"))  # 把我们得图片以 PNG 保存到空字节流
        imgByteArr = imgByteArr.getvalue()  # 无视指针，获取全部内容，类型由io流变成bytes。
        with open(f"data{sep}asoulcnki.png", "wb") as i:
            i.write(imgByteArr)
        return f"data{sep}asoulcnki.png"
    except Exception as e:
        logger.warning(f"Error in render_reply: {e}")
        return None
