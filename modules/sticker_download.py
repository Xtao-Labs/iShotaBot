import contextlib
import tempfile
from typing import TYPE_CHECKING

from cashews import cache
from pyrogram import filters, ContinuePropagation
from pyrogram.enums import ChatAction, MessageEntityType
from pyrogram.errors import StickersetInvalid

from defs.sticker_download import get_from_sticker_set, get_from_sticker, custom_emoji_filter, \
    get_from_custom_emoji, export_end, export_add
from init import bot

if TYPE_CHECKING:
    from pyrogram import Client
    from pyrogram.types import Message


@bot.on_message(
    filters.private & filters.text & filters.incoming & filters.regex(r"^https://t.me/addstickers/.*")
)
async def process_sticker_set(client: "Client", message: "Message"):
    cid = message.from_user.id
    short_name = message.text.replace("https://t.me/addstickers/", "")
    file = None
    try:
        reply = await message.reply("正在下载贴纸包...请耐心等待", quote=True)
        file = await get_from_sticker_set(short_name, cid, client, reply)
        with contextlib.suppress(Exception):
            await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
        await message.reply_document(file.as_posix(), quote=True)
        with contextlib.suppress(Exception):
            await reply.delete()
    except StickersetInvalid:
        await message.reply("无效的贴纸包", quote=True)
    finally:
        if file:
            file.unlink(missing_ok=True)
    raise ContinuePropagation


@bot.on_message(filters.private & filters.sticker & filters.incoming)
async def process_single_sticker(client: "Client", message: "Message"):
    await message.reply_chat_action(ChatAction.TYPING)
    if temp := await cache.get(f"sticker:export:{message.from_user.id}"):
        try:
            await export_add(temp, message.sticker, client)
            await message.reply_text("成功加入导出列表，结束选择请输入 /sticker_export_end", quote=True)
        except ValueError as exc:
            await message.reply(str(exc), quote=True)
    else:
        reply = await message.reply("正在转换贴纸...请耐心等待", quote=True)
        target_file = None
        try:
            target_file = await get_from_sticker(client, message)
            await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            await message.reply_document(target_file.as_posix(), quote=True)
            with contextlib.suppress(Exception):
                await reply.delete()
        except ValueError as exc:
            await reply.edit(str(exc))
        finally:
            if target_file:
                target_file.unlink(missing_ok=True)
    raise ContinuePropagation


@bot.on_message(filters.private & custom_emoji_filter & filters.incoming)
async def process_custom_emoji(client: "Client", message: "Message"):
    try:
        stickers = await client.get_custom_emoji_stickers(
            [i.custom_emoji_id for i in message.entities if i and i.type == MessageEntityType.CUSTOM_EMOJI]
        )
    except AttributeError:
        await message.reply("无法获取贴纸", quote=True)
        raise ContinuePropagation
    reply = await message.reply(f"正在下载 {len(stickers)} 个 emoji ...请耐心等待", quote=True)
    exc = None
    for sticker in stickers:
        target_file = None
        try:
            target_file = await get_from_custom_emoji(client, sticker)
            await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            await message.reply_document(target_file.as_posix(), quote=True)
        except ValueError as exc_:
            exc = exc_
        finally:
            if target_file:
                target_file.unlink(missing_ok=True)
    if exc:
        await reply.edit(str(exc))
    else:
        with contextlib.suppress(Exception):
            await reply.delete()
    raise ContinuePropagation


@bot.on_message(
    filters.private & filters.incoming & filters.command(
        ["sticker_export_start", "sticker_export_end"]
    )
)
async def batch_start(_: "Client", message: "Message"):
    uid = message.from_user.id
    if "start" in message.command[0].lower():
        if await cache.get(f"sticker:export:{uid}"):
            await message.reply("已经开始批量导出贴纸，请直接发送贴纸，完成选择请输入 /sticker_export_end", quote=True)
            return
        await cache.set(f"sticker:export:{uid}", tempfile.mkdtemp())
        await message.reply("开始批量导出贴纸，请直接发送贴纸，完成选择请输入 /sticker_export_end", quote=True)
    else:
        target_dir = await cache.get(f"sticker:export:{uid}")
        if not target_dir:
            await message.reply("未开始批量导出贴纸，请先使用命令 /sticker_export_start", quote=True)
            return
        file = None
        try:
            reply = await message.reply("正在打包贴纸包...请耐心等待", quote=True)
            file = await export_end(uid, target_dir, reply)
            await message.reply_chat_action(ChatAction.UPLOAD_DOCUMENT)
            await message.reply_document(file.as_posix())
        except FileNotFoundError:
            await message.reply("没有选择贴纸，导出失败", quote=True)
        finally:
            await cache.delete(f"sticker:export:{uid}")
            if file:
                file.unlink(missing_ok=True)
