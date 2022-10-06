import asyncio
import contextlib
import os
import re
import time
from asyncio import sleep
from io import BytesIO
from typing import List, Dict

from pyrogram.errors import FloodWait
from pyrogram.types import Message

from defs.glover import lofter_channel
from defs.lofter import lofter_link
from models.lofter import LofterPost as LofterPostModel
from models.models.lofter import Lofter as LofterModel
from init import request, bot

pattern = re.compile(r'<[^>]+>', re.S)


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
        def __init__(self, url, origin_url, title, user_id, username, name, tags, comment, post_id, first, static):
            self.url = url.split('?')[0]
            self.origin_url = origin_url
            self.user_id = str(user_id)
            self.username = username
            self.post_id = post_id
            self.first = first
            self.static = static
            title = pattern.sub('\n', title).strip()[:500]
            self.text = f"<b>Lofter Status Info</b>\n\n" \
                        f"<code>{title}</code>\n\n" \
                        f"✍️ <a href=\"https://{username}.lofter.com/\">{name}</a>\n" \
                        f"{tags}\n" \
                        f"{comment}"

        async def check_exists(self):
            return await LofterPostModel.get_by_post_and_user_id(self.user_id, self.post_id)

        async def add_to_db(self):
            post = LofterModel(
                user_id=self.user_id,
                username=self.username,
                post_id=self.post_id,
                timestamp=int(time.time())
            )
            await LofterPostModel.add_post(post)

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
                user_id, username, name, comment = 0, "", "", ""
                if blog_info := post_data.get("blogInfo"):
                    user_id = blog_info.get("blogId", 0)
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
                            first = True
                            for photo in photo_links:
                                if url := photo.get("orign"):
                                    width = photo.get("ow", 0)
                                    height = photo.get("oh", 0)
                                    static = abs(height - width) > 1300
                                    datas.append(LofterPost.Item(
                                        url,
                                        origin_url,
                                        title,
                                        user_id,
                                        username,
                                        name,
                                        tags,
                                        comment,
                                        permalink,
                                        first,
                                        static
                                    ))
                                    first = False
        return datas

    async def get_items(self) -> List[Item]:
        datas: List[LofterPost.Item] = []
        data = await self.get_data()
        if data:
            data = data.get("data", {})
        if data:
            self.offset = data.get("offset", 0)
            if posts := data.get("posts", []):
                datas = self.parse_data(posts)
        return datas

    async def upload(self, message: Message):
        msg = await message.reply_text("正在上传中...")
        success, error, skip = 0, 0, 0
        temp_skip = False
        while True:
            try:
                items = await self.get_items()
                if not items:
                    break
                for item in items:
                    try:
                        if item.first:
                            if await item.check_exists():
                                temp_skip = True
                                skip += 1
                                await sleep(0.5)
                                continue
                            else:
                                temp_skip = False
                        elif temp_skip:
                            skip += 1
                            continue
                        file = await item.init()
                        await item.upload(file)
                        if item.first:
                            await item.add_to_db()
                        success += 1
                        await sleep(0.5)
                    except Exception as e:
                        print(f"Error uploading file: {e}")
                        error += 1
                    if (success + error) % 10 == 0:
                        with contextlib.suppress(Exception):
                            await msg.edit(f"已成功上传{success}条，失败{error}条，跳过 {skip} 条，第 {success + error + skip} 条")
                if self.offset == -1:
                    break
            except Exception as e:
                print(f"Error uploading file: {e}")
                continue
        await msg.edit(f"上传完成，成功{success}条，失败{error}条，跳过 {skip} 条，总共 {success + error + skip} 条")
