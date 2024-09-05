import asyncio
import os
import shutil
from pathlib import Path

import aiofiles
import httpx
from bs4 import BeautifulSoup

from defs.bilibili_download import execute

FFMPEG_PATH = "ffmpeg"
URL = "http://www.nmc.cn/publish/satellite/fy4b-visible.htm"
TEMP_PATH = Path("data") / "weather_tmp"
TEMP_PATH.mkdir(exist_ok=True, parents=True)
OUTPUT_PATH = TEMP_PATH / "output.mp4"


class WeatherGraphError(Exception):
    def __init__(self, error: str):
        self.error = error


async def download_img(client, index: int, url: str):
    try:
        res = await client.get(url)
        if res.status_code != 200:
            print(f"下载天气图片失败，错误代码 {res.status_code}")
        async with aiofiles.open(
            TEMP_PATH / f"img{str(index).zfill(3)}.jpg", "wb"
        ) as f:
            await f.write(res.content)
    except Exception as e:
        print(f"下载天气图片失败 {url} {e}")


async def get_images():
    async with httpx.AsyncClient() as client:
        res = await client.get(URL)
        if res.status_code != 200:
            raise WeatherGraphError(f"获取图片数据失败，错误代码 {res.status_code}")
        html = res.content
        soup = BeautifulSoup(html, "lxml")
        elements = soup.find_all(class_="time")
        tasks = []
        for index, element in enumerate(reversed(elements)):
            url = element["data-img"]
            url = url.replace("medium/", "")
            task = asyncio.create_task(download_img(client, index, url))
            tasks.append(task)
        await asyncio.gather(*tasks)


async def get_video():
    frame_rate = 6
    ffmpeg_cmd = f'{FFMPEG_PATH} -r {frame_rate} -i "{TEMP_PATH}/img%03d.jpg" -vf scale=1920:1080 -c:v libx264 -pix_fmt yuv420p -y "{TEMP_PATH}/output.mp4"'
    _, code = await execute(ffmpeg_cmd)
    if code != 0:
        raise WeatherGraphError("生成视频失败")


async def gen() -> Path:
    if not os.path.exists(TEMP_PATH):
        os.mkdir(TEMP_PATH)
    else:
        shutil.rmtree(TEMP_PATH)
        os.mkdir(TEMP_PATH)
    await get_images()
    await get_video()
    return OUTPUT_PATH
