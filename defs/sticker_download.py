import asyncio
import contextlib
import os
import shutil
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from sys import executable
from typing import TYPE_CHECKING, Union

from pathlib import Path

import aiofiles
from pyrogram.enums import MessageEntityType
from pyrogram.filters import create as create_filter
from pyrogram.file_id import FileType, FileId
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.raw.types.messages import StickerSet
from pyrogram.types import Message, Sticker

from init import logs

if TYPE_CHECKING:
    from pyrogram import Client

temp_path = Path("data/cache")
temp_path.mkdir(parents=True, exist_ok=True)
lottie_path = Path(executable).with_name("lottie_convert.py")


async def _custom_emoji_filter(_, __, message: Message):
    entities = message.entities or message.caption_entities
    if not entities:
        return False
    for entity in entities:
        if entity.type == MessageEntityType.CUSTOM_EMOJI:
            return True
    return False


custom_emoji_filter = create_filter(_custom_emoji_filter)


def get_target_file_path(src: Path) -> Path:
    old_ext = src.suffix
    if old_ext in [".jpeg", ".jpg", ".png", ".webp"]:
        return src.with_suffix(".png")
    elif old_ext in [".mp4", ".webm", ".tgs"]:
        return src.with_suffix(".gif")
    else:
        return src.with_suffix(".mp4")


async def converter(src_file: Union[Path, str]) -> Path:
    src_file = Path(src_file)
    target_file = get_target_file_path(src_file)
    if src_file.suffix == ".tgs":
        process = await asyncio.create_subprocess_exec(
            executable,
            lottie_path,
            src_file,
            target_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            src_file,
            target_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    _, stderr = await process.communicate()

    if process.returncode == 0:
        src_file.unlink(missing_ok=True)
    else:
        logs.error(
            "转换 %s -> %s 时出错: %s",
            src_file.name,
            target_file.name,
            stderr.decode("utf-8"),
        )
        raise ValueError("转换 %s -> %s 时出错" % (src_file.name, target_file.name))
    return target_file


def get_file_id(doc, set_id, set_hash) -> FileId:
    return FileId(
        file_type=FileType.STICKER,
        dc_id=doc.dc_id,
        file_reference=doc.file_reference,
        media_id=doc.id,
        access_hash=doc.access_hash,
        sticker_set_id=set_id,
        sticker_set_access_hash=set_hash,
    )


def get_ext_from_mime(mime: str) -> str:
    if mime == "image/jpeg":
        return ".jpg"
    elif mime == "image/png":
        return ".png"
    elif mime == "image/webp":
        return ".webp"
    elif mime == "video/mp4":
        return ".mp4"
    elif mime == "video/webm":
        return ".webm"
    elif mime == "application/x-tgsticker":
        return ".tgs"
    else:
        return ""


def zip_dir(dir_path: str, zip_filepath: Path):
    zipf = zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_path = Path(root).joinpath(file)
            file_name = file_path.relative_to(dir_path)
            zipf.write(file_path, file_name)
    zipf.close()


async def run_zip_dir(dir_path: str, zip_filepath: Path):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(
            executor,
            zip_dir,
            dir_path,
            zip_filepath,
        )


async def edit_message(reply: "Message", text: str) -> "Message":
    with contextlib.suppress(Exception):
        return await reply.edit(text)


async def get_from_sticker_set(
    short_name: str, uid: int, client: "Client", reply: "Message"
) -> Path:
    s = InputStickerSetShortName(short_name=short_name)
    packs: "StickerSet" = await client.invoke(GetStickerSet(stickerset=s, hash=0))
    tempdir = tempfile.mkdtemp()
    logs.info("下载贴纸包 %s", short_name)
    for doc in packs.documents:
        file_id = get_file_id(doc, packs.set.id, packs.set.access_hash)
        ext = get_ext_from_mime(doc.mime_type)
        file_path = Path(tempdir) / f"{doc.id}{ext}"
        async with aiofiles.open(file_path, "wb") as file:
            async for chunk in client.get_file(file_id):
                await file.write(chunk)
    logs.info("转换贴纸包 %s", short_name)
    await edit_message(reply, "正在转换贴纸包...请耐心等待")
    for f in Path(tempdir).glob("*"):
        await converter(f)
    logs.info("打包贴纸包 %s", short_name)
    await edit_message(reply, "正在打包贴纸包...请耐心等待")
    zip_file_path = temp_path / f"{uid}_{short_name}.zip"
    await run_zip_dir(tempdir, zip_file_path)
    shutil.rmtree(tempdir)
    logs.info("发送贴纸包 %s", short_name)
    await edit_message(reply, "正在发送贴纸包...请耐心等待")
    return zip_file_path


async def get_from_sticker(client: "Client", message: "Message") -> Path:
    sticker_path = await client.download_media(message)
    return await converter(sticker_path)


async def get_from_custom_emoji(client: "Client", sticker: "Sticker") -> Path:
    sticker_path = await client.download_media(sticker.file_id)
    return await converter(sticker_path)


async def export_add(tempdir: str, sticker: Sticker, client: "Client"):
    file_id = sticker.file_id
    file_unique_id = sticker.file_unique_id
    ext = sticker.file_name.split(".")[-1]
    filepath: "Path" = Path(tempdir).joinpath(f"{file_unique_id}.{ext}")
    await client.download_media(file_id, file_name=filepath.as_posix())
    await converter(filepath)


async def export_end(uid: int, tempdir: str, reply: "Message") -> Path:
    if not Path(tempdir).glob("*"):
        raise FileNotFoundError
    logs.info("打包 %s 的批量导出的贴纸包", uid)
    zip_file_path = temp_path / f"{uid}.zip"
    await run_zip_dir(tempdir, zip_file_path)
    shutil.rmtree(tempdir)
    logs.info("发送 %s 的批量导出的贴纸包", uid)
    await edit_message(reply, "正在发送贴纸包...请耐心等待")
    return zip_file_path
