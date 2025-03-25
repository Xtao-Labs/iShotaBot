#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author         : yanyongyu
@Date           : 2021-03-12 13:42:43
@LastEditors    : yanyongyu
@LastEditTime   : 2021-11-01 14:05:41
@Description    : None
@GitHub         : https://github.com/yanyongyu
"""

__author__ = "yanyongyu"

import asyncio
import platform
from contextlib import asynccontextmanager
from os import getcwd
from typing import Optional, AsyncIterator
from playwright.async_api import Page, Browser, async_playwright, Error
from init import logger
from uvicorn.loops import asyncio as _asyncio
from uvicorn import config


def asyncio_setup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


@property
def should_reload(self):
    return False


if platform.system() == "Windows":
    _asyncio.asyncio_setup = asyncio_setup
    config.Config.should_reload = should_reload
    logger.warning("检测到当前为 Windows 系统，已自动注入猴子补丁")

_browser: Optional[Browser] = None
_playwright = None


async def init(**kwargs) -> Browser:
    global _browser
    global _playwright
    _playwright = await async_playwright().start()
    try:
        _browser = await launch_browser(**kwargs)
    except Error:
        await install_browser()
        _browser = await launch_browser(**kwargs)
    return _browser


async def launch_browser(**kwargs) -> Browser:
    return await _playwright.chromium.launch(**kwargs)


async def get_browser(**kwargs) -> Browser:
    return _browser or await init(**kwargs)


@asynccontextmanager
async def get_new_page(**kwargs) -> AsyncIterator[Page]:
    browser = await get_browser()
    page = await browser.new_page(**kwargs)
    try:
        yield page
    finally:
        await page.close()


async def shutdown_browser():
    await _browser.close()
    await _playwright.stop()


async def install_browser():
    logger.info("正在安装 chromium")
    import sys
    from playwright.__main__ import main

    sys.argv = ["", "install", "chromium"]
    try:
        main()
    except SystemExit:
        pass


async def html_to_pic(
    html: str, wait: int = 0, template_path: str = f"file://{getcwd()}", **kwargs
) -> bytes:
    """html转图片
    Args:
        html (str): html文本
        wait (int, optional): 等待时间. Defaults to 0.
        template_path (str, optional): 模板路径 如 "file:///path/to/template/"
    Returns:
        bytes: 图片, 可直接发送
    """
    # logger.debug(f"html:\n{html}")
    if "file:" not in template_path:
        raise "template_path 应该为 file:///path/to/template"
    async with get_new_page(**kwargs) as page:
        await page.goto(template_path)
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(wait)
        img_raw = await page.screenshot(full_page=True)
    return img_raw
