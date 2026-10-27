import json
from os import sep
from secrets import choice

from pyrogram import Client, ContinuePropagation, filters
from pyrogram.types import Message

from init import bot

book_of_answers: list[str]


with open(
    f"resources{sep}text{sep}book_of_answers.json", "r", encoding="utf-8"
) as file:
    book_of_answers = json.load(file)


@bot.on_message(filters.incoming & filters.regex(r"^答案之书$"))
async def book_of_answer(_: Client, message: Message):
    await message.reply_text(f"{choice(book_of_answers)}")
    raise ContinuePropagation
