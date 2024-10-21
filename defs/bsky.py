import asyncio
import traceback
from typing import Optional, TYPE_CHECKING

from atproto_client.exceptions import BadRequestError
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)

from init import bot, logs
from models.models.bsky import HumanPost, HumanAuthor
from models.services.bsky import bsky_client

if TYPE_CHECKING:
    from modules.bsky_api import Reply


def flood_wait():
    def decorator(function):
        async def wrapper(*args, **kwargs):
            try:
                return await function(*args, **kwargs)
            except FloodWait as e:
                logs.warning(f"遇到 FloodWait，等待 {e.value} 秒后重试！")
                await asyncio.sleep(e.value + 1)
                return await wrapper(*args, **kwargs)
            except Exception as e:
                traceback.print_exc()
                raise e

        return wrapper

    return decorator


class Timeline:
    @staticmethod
    def get_button(post: HumanPost) -> InlineKeyboardMarkup:
        buttons = [
            InlineKeyboardButton("Source", url=post.url),
            InlineKeyboardButton("Author", url=post.author.url),
        ]
        if post.parent_post:
            buttons.insert(1, InlineKeyboardButton("RSource", url=post.parent_post.url))
        return InlineKeyboardMarkup([buttons])

    @staticmethod
    def get_author_button(author: HumanAuthor) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Author", url=author.url),
                ]
            ]
        )

    @staticmethod
    def get_media_group(text: str, post: HumanPost) -> list[InputMediaPhoto]:
        data = []
        images = post.images
        for idx, image in enumerate(images):
            data.append(
                InputMediaPhoto(
                    image,
                    caption=text if idx == 0 else None,
                    parse_mode=ParseMode.HTML,
                )
            )
        return data

    @staticmethod
    def get_post_text(post: HumanPost) -> str:
        text = "<b>Bsky Post Info</b>\n\n<code>"
        if post.parent_post:
            text += f"> {post.parent_post.content}\n\n=====================\n\n"
        text += post.content
        text += "\n\n"
        if (post.is_reply or post.is_quote) and post.parent_post:
            text += f"{post.parent_post.author.format} {post.parent_post.status}于 {post.parent_post.time_str}\n"
        text += f"{post.author.format} {post.status}于 {post.time_str}\n"
        if post.is_repost:
            text += f"{post.repost_info.by.format} {post.status}于 {post.repost_info.time_str}\n"
        text += f"点赞: {post.like_count} | 引用: {post.quote_count} | 回复: {post.reply_count} | 转发: {post.repost_count}"
        return text

    @staticmethod
    @flood_wait()
    async def send_to_user(reply: "Reply", post: HumanPost):
        text = Timeline.get_post_text(post)
        if post.gif:
            return await bot.send_animation(
                reply.cid,
                post.gif,
                caption=text,
                reply_to_message_id=reply.mid,
                parse_mode=ParseMode.HTML,
                reply_markup=Timeline.get_button(post),
            )
        elif post.external:
            return await bot.send_document(
                reply.cid,
                post.external,
                caption=text,
                reply_to_message_id=reply.mid,
                parse_mode=ParseMode.HTML,
                reply_markup=Timeline.get_button(post),
            )
        elif not post.images:
            return await bot.send_message(
                reply.cid,
                text,
                disable_web_page_preview=True,
                reply_to_message_id=reply.mid,
                parse_mode=ParseMode.HTML,
                reply_markup=Timeline.get_button(post),
            )
        elif len(post.images) == 1:
            return await bot.send_photo(
                reply.cid,
                post.images[0],
                caption=text,
                reply_to_message_id=reply.mid,
                parse_mode=ParseMode.HTML,
                reply_markup=Timeline.get_button(post),
            )
        else:
            await bot.send_media_group(
                reply.cid,
                Timeline.get_media_group(text, post),
                reply_to_message_id=reply.mid,
            )

    @staticmethod
    def code(text: str) -> str:
        return f"<code>{text}</code>"

    @staticmethod
    def get_author_text(author: HumanAuthor) -> str:
        text = "<b>Bsky User Info</b>\n\n"
        text += f"Name: {Timeline.code(author.display_name)}\n"
        text += f"Username: {author.format_handle}\n"
        if author.description:
            text += f"Bio: {Timeline.code(author.description)}\n"
        text += f"Joined: {Timeline.code(author.time_str)}\n"
        if author.posts_count:
            text += f"📤 {author.posts_count} "
        if author.followers_count:
            text += f"粉丝 {author.followers_count} "
        if author.follows_count:
            text += f"关注 {author.follows_count}"
        return text

    @staticmethod
    @flood_wait()
    async def send_user(reply: "Reply", author: HumanAuthor):
        text = Timeline.get_author_text(author)
        if author.avatar_img:
            return await bot.send_photo(
                reply.cid,
                author.avatar_img,
                caption=text,
                reply_to_message_id=reply.mid,
                parse_mode=ParseMode.HTML,
                reply_markup=Timeline.get_author_button(author),
            )
        else:
            return await bot.send_message(
                reply.cid,
                text,
                disable_web_page_preview=True,
                reply_to_message_id=reply.mid,
                parse_mode=ParseMode.HTML,
                reply_markup=Timeline.get_author_button(author),
            )

    @staticmethod
    async def fetch_post(handle: str, cid: str) -> Optional[HumanPost]:
        try:
            user = await Timeline.fetch_user(handle)
            uri = f"at://{user.did}/app.bsky.feed.post/{cid}"
            post = await bsky_client.client.get_post_thread(uri)
            return HumanPost.parse_thread(post.thread)
        except BadRequestError as e:
            logs.error(f"bsky Error: {e}")
        return None

    @staticmethod
    async def fetch_user(handle: str) -> Optional[HumanAuthor]:
        try:
            user = await bsky_client.client.get_profile(handle)
            return HumanAuthor.parse_detail(user)
        except BadRequestError as e:
            logs.error(f"bsky Error: {e}")
        return None
