import json
from secrets import choice
from os import sep
from typing import List

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message


book_of_answers: List[str]


with open(f"resources{sep}text{sep}book_of_answers.json", "r", encoding="utf-8") as file:
    book_of_answers = json.load(file)


@Client.on_message(filters.incoming &
                   filters.regex(r"^答案之书$"))
async def book_of_answer(_: Client, message: Message):
    await message.reply_text(
        f"{choice(book_of_answers)}",
        quote=True
    )
    raise ContinuePropagation
