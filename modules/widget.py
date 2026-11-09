import contextlib
import io
import zlib

from pyrogram import Client, filters
from pyrogram.types import Document, Message

from init import bot


def widget_html(payload: bytes) -> str:
    """widget payload 是 zlib 压缩的 HTML，兼容 gzip / raw deflate。"""
    for wbits in (zlib.MAX_WBITS, zlib.MAX_WBITS | 16, -zlib.MAX_WBITS):
        try:
            return zlib.decompress(payload, wbits).decode("utf-8")
        except zlib.error:
            continue
    raise ValueError("无法识别的 payload 压缩格式")


async def html_sender_command(message: Message):
    document: Document = message.reply_to_message.document
    if document.file_size > 10_000_000:
        return
    width, height = 100, 100
    with contextlib.suppress(ValueError, IndexError):
        width, height = int(message.command[1]), int(message.command[2])
    document_file = await message.reply_to_message.download(in_memory=True)
    document_file_html = document_file.getvalue().decode("utf-8")

    from pyrogram import raw

    chat_id = message.chat.id
    media = raw.types.InputMediaWidget(
        width=width,
        height=height,
        html=document_file_html,
    )
    rpc = raw.functions.messages.SendMedia(
        peer=await bot.resolve_peer(chat_id),
        media=media,
        message="",
        silent=False,
        reply_to=None,
        random_id=bot.rnd_id(),
        schedule_date=None,
        noforwards=None,
        allow_paid_floodskip=None,
        allow_paid_stars=None,
        reply_markup=None,
        effect=None,
        suggested_post=None,
    )
    await bot.invoke(rpc)


@bot.on_message(filters.incoming & filters.reply & filters.command(["widget"]))
async def html_rec_command(_: Client, message: Message):
    document: Document = message.reply_to_message.document
    if document:
        await html_sender_command(message)
        return

    p = message.reply_to_message.raw.media.payload
    html = widget_html(p)

    file_stream = io.BytesIO(html.encode("utf-8"))
    file_stream.name = "demo.html"

    await message.reply_document(file_stream)
