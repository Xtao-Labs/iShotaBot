import asyncio
import traceback
from io import BytesIO
from typing import List

from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import InlineQueryResultCachedPhoto

from defs.glover import splash_channel, splash_channel_username
from defs.request import cache_file
from init import bot, request, logger
from models.models.splash import Splash as SplashModel
from models.apis.splash import Splash as SplashApi
from models.services.splash import SplashService


async def get_splash() -> List[SplashApi]:
    data = await request.get("https://bbs-api.miyoushe.com/apihub/api/getAppSplash")
    splash_list = []
    if data.is_success:
        data = data.json()
        for i in data["data"]["splashes"]:
            splash_list.append(SplashApi(**i))
    return splash_list


async def check_splash(splash: SplashApi) -> bool:
    if data := await SplashService.get_by_splash_id(splash.id):
        if splash.splash_image:
            data.splash_image = splash.splash_image
        if splash.online_ts:
            data.online_ts = splash.online_ts
        if splash.offline_ts:
            data.offline_ts = splash.offline_ts
        if splash.article_url:
            data.article_url = splash.article_url
        await SplashService.update_splash(data)
        return False
    return True


def gen_splash(splash: SplashApi) -> SplashModel:
    return SplashModel(
        id=splash.id,
        splash_image=splash.splash_image,
        online_ts=splash.online_ts,
        offline_ts=splash.offline_ts,
        file_id=splash.file_id,
        article_url=splash.article_url,
    )


def retry(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            logger.warning(f"Sleeping for {e.value}s")
            await asyncio.sleep(e.value + 1)
            return await func(*args, **kwargs)

    return wrapper


@retry
async def send_splash_text(api: SplashApi):
    await bot.send_message(
        splash_channel,
        api.text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@retry
async def send_splash_photo(model: SplashModel, content: BytesIO):
    photo = await bot.send_photo(
        splash_channel,
        content,
    )
    model.file_id = photo.photo.file_id


@retry
async def send_splash_document(content: BytesIO):
    await bot.send_document(
        splash_channel,
        content,
        force_document=True,
    )


async def send_splash(api: SplashApi, model: SplashModel):
    content = await cache_file(api.splash_image)
    await send_splash_text(api)
    await send_splash_photo(model, content)
    await send_splash_document(content)


async def update_splash():
    logger.info("Updating splash ...")
    try:
        data = await get_splash()
    except Exception:
        traceback.print_exc()
        return
    for i in data:
        if not await check_splash(i):
            continue
        model = gen_splash(i)
        if not model.splash_image:
            continue
        try:
            await send_splash(i, model)
        except Exception:
            traceback.print_exc()
            continue
        await SplashService.add_splash(model)
    logger.info("Splash updated.")


async def get_inline_results() -> List[InlineQueryResultCachedPhoto]:
    splash = await SplashService.get_all_splashes()
    splash.sort(key=lambda x: x.offline_ts, reverse=True)
    splash = splash[:50]
    results = []
    for idx, i in enumerate(splash):
        results.append(
            InlineQueryResultCachedPhoto(
                title=f"Splash No.{idx + 1}",
                photo_file_id=i.file_id,
                caption=f"#id{i.id} @{splash_channel_username}",
            )
        )
    return results
