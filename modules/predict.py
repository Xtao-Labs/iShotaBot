import time

from pyrogram import Client, filters
from pyrogram.types import Message

from defs.predict import predict
from init import bot


@bot.on_message(filters.incoming & filters.command(["predict"]))
async def predict_command(_: Client, message: Message):
    r = message
    if message.reply_to_message and message.reply_to_message.photo:
        r = message.reply_to_message
    if not r.photo:
        return await message.reply("请发送/回复一张图片")
    time1 = time.time()
    file = await r.download(in_memory=True)
    download_time = time.time()
    face, image = await predict(file)
    if face and image:
        text = f"下载耗时: {download_time - time1:.2f}s\n预测耗时: {face.predict_time:.2f}s\n绘制耗时: {face.draw_time:.2f}s"
        await message.reply_photo(image, caption=text)
    else:
        await message.reply("未检测到人脸")
