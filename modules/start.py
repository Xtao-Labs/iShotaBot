from pyrogram import Client, filters
from pyrogram.types import Message
from defs.button import gen_button, Button

des = """本机器人特性：

★ 解析 bilibili 视频、动态
★ 解析 twitter 推文、用户
★ 解析 lofter 日志、用户
★ 汇率查询
★ 复读机（3条）
★ 答案之书
★ 鲁迅说过
★ 我有个朋友
★ 简易版问与答
"""


@Client.on_message(filters.incoming & filters.private &
                   filters.command(["start"]))
async def start_command(_: Client, message: Message):
    """
        回应机器人信息
    """
    await message.reply(des,
                        quote=True,
                        reply_markup=gen_button(
                            [Button(0, "Gitlab", "https://gitlab.com/Xtao-Labs/iShotaBot"),
                             Button(0, "Github", "https://github.com/Xtao-Labs/iShotaBot")]))
