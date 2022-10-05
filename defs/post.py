import asyncio
import contextlib
import os
import re
from asyncio import sleep
from io import BytesIO
from typing import List, Dict

from pyrogram.errors import FloodWait
from pyrogram.types import Message

from defs.glover import lofter_channel
from defs.lofter import lofter_link
from init import request, bot

pattern = re.compile(r'<[^>]+>',re.S)


class LofterPost:
    def __init__(self, url: str, offset: str):
        try:
            self.grainId = int(url)
        except ValueError:
            self.grainId = int(url[url.find('grainId=') + 8:].split("&")[0])
        try:
            self.offset = int(offset)
        except ValueError:
            self.offset = 0
        self.url = f"https://api.lofter.com/api-grain/grain/getH5Detail.json?grainId={self.grainId}&offset="

    async def get_data(self):
        if self.offset == -1:
            return None
        res = await request.get(self.url + str(self.offset))
        assert res.status_code == 200
        return res.json()

    class Item:
        def __init__(self, url, origin_url, title, username, name, tags, comment, static):
            self.url = url.split('?')[0]
            self.origin_url = origin_url
            self.username = username
            self.static = static
            title = pattern.sub('\n', title).strip()[:500]
            self.text = f"<b>Lofter Status Info</b>\n\n" \
                        f"<code>{title}</code>\n\n" \
                        f"✍️ <a href=\"https://{username}.lofter.com/\">{name}</a>\n" \
                        f"{tags}\n" \
                        f"{comment}"

        async def init(self):
            file = await request.get(self.url, timeout=30)
            file = BytesIO(file.content)
            file.name = os.path.basename(self.url)
            return file

        async def upload(self, file):
            try:
                if self.static:
                    await bot.send_document(lofter_channel, file, caption=self.text, disable_notification=True,
                                            reply_markup=lofter_link(self.url, self.origin_url, self.username))
                else:
                    await bot.send_photo(lofter_channel, file, caption=self.text, disable_notification=True,
                                         reply_markup=lofter_link(self.url, self.origin_url, self.username))
            except FloodWait as e:
                await asyncio.sleep(e.value + 0.5)
                await self.upload(file)

    @staticmethod
    def parse_data(data: List[Dict]) -> List[Item]:
        datas = []
        for i in data:
            if post_data := i.get("postData"):
                username, name, comment = "", "", ""
                if blog_info := post_data.get("blogInfo"):
                    username = blog_info.get("blogName", "")
                    name = blog_info.get("blogNickName", "")
                if post_count_view := post_data.get("postCountView"):
                    a = post_count_view.get("responseCount", 0)
                    b = post_count_view.get("hotCount", 0)
                    c = post_count_view.get("favoriteCount", 0)
                    comment = f"评论({a})  热度({b})  喜欢({c})"
                if post_view := post_data.get("postView"):
                    title = post_view.get("digest", "")
                    permalink = post_view.get("permalink", "")
                    origin_url = f"https://{username}.lofter.com/post/{permalink}"
                    tags = "".join(f"#{i} " for i in post_view.get("tagList", []))
                    if photo_post_view := post_view.get("photoPostView"):
                        if photo_links := photo_post_view.get("photoLinks"):
                            for photo in photo_links:
                                if url := photo.get("orign"):
                                    width = photo.get("ow", 0)
                                    height = photo.get("oh", 0)
                                    static = abs(height - width) > 1300
                                    datas.append(LofterPost.Item(
                                        url,
                                        origin_url,
                                        title,
                                        username,
                                        name,
                                        tags,
                                        comment,
                                        static
                                    ))
        return datas

    async def get_items(self) -> List[Item]:
        datas: List[LofterPost.Item] = []
        while True:
            data = await self.get_data()
            if not data:
                break
            data = data.get("data", {})
            if not data:
                break
            self.offset = data.get("offset", 0)
            posts = data.get("posts", [])
            if not posts:
                break
            datas.extend(self.parse_data(posts))
            if self.offset == -1:
                break
        return datas

    async def upload(self, message: Message):
        msg = await message.reply_text("正在获取数据...")
        try:
            items = await self.get_items()
        except Exception as e:
            await msg.edit_text(f"获取数据失败: {e}")
            return
        await msg.edit(f"获取到{len(items)}条数据，正在上传...")
        success, error, final = 0, 0, len(items)
        for item in items:
            try:
                file = await item.init()
                await item.upload(file)
                success += 1
                await sleep(1)
            except Exception:
                error += 1
            if (success + error) % 10 == 0:
                with contextlib.suppress(Exception):
                    await msg.edit(f"已成功上传{success}条，失败{error}条，剩余{final - success - error}条")
        await msg.edit(f"上传完成，成功{success}条，失败{error}条")
