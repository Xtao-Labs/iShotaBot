import re
from re import Pattern
from typing import Union

from pyrogram.filters import create
from pyrogram.types import Message, CallbackQuery, InlineQuery, PreCheckoutQuery, ChosenInlineResult, Update


def regex(pattern: Union[str, Pattern], flags: int = 0):
    async def func(flt, _, update: Update):
        if isinstance(update, Message):
            value = update.text or update.caption
        elif isinstance(update, CallbackQuery):
            value = update.data
        elif isinstance(update, (InlineQuery, ChosenInlineResult)):
            value = update.query
        elif isinstance(update, PreCheckoutQuery):
            value = update.invoice_payload
        else:
            raise ValueError(f"Regex filter doesn't work with {type(update)}")

        if value:
            update.matches = list(flt.p.finditer(value)) or None

        return bool(update.matches)

    return create(
        func,
        "RegexFilter",
        p=pattern if isinstance(pattern, Pattern) else re.compile(pattern, flags)
    )
