from defs.browser import get_browser


async def get_mihoyo_screenshot(url):
    browser = await get_browser()
    context = await browser.new_context(
        viewport={"width": 2560, "height": 1080},
        device_scale_factor=2,
    )
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        # 被删除或者进审核了
        if page.url == "https://bbs.mihoyo.com/ys/404":
            return None
        card = await page.query_selector(".mhy-article-page__main")
        assert card
        clip = await card.bounding_box()
        assert clip
        clip["width"] += 310
        return await page.screenshot(clip=clip, full_page=True)
    except Exception as e:
        print(f"截取米哈游帖子时发生错误：{e}")
        return await page.screenshot(full_page=True)
    finally:
        await context.close()
