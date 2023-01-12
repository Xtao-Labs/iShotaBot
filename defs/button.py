from typing import List

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Button:
    def __init__(self, type_name, name, data):
        self.type = type_name  # 按钮类型：链接(0)、回调(1)
        self.name = name  # 按钮名称
        self.data = data  # 按钮指向的链接/回调数据


def gen_button(data: List) -> InlineKeyboardMarkup:
    """
    生成按钮
    :param data: 按钮数据
    :return:
    """
    buttons_url = []
    buttons_callback = []
    for button in data:
        if button.type == 0:
            buttons_url.append(InlineKeyboardButton(text=button.name, url=button.data))
        elif button.type == 1:
            buttons_callback.append(
                InlineKeyboardButton(text=button.name, callback_data=button.data)
            )
    return InlineKeyboardMarkup(inline_keyboard=[buttons_callback, buttons_url])
