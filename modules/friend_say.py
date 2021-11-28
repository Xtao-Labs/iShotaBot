from io import BytesIO
from os import sep, makedirs
from os.path import exists

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.types import Message

from defs.friend_say import ImageUtil


@Client.on_message(filters.incoming & ~filters.edited & filters.group &
                   filters.regex(r"^我有个朋友"))
async def friend_say(client: Client, message: Message):
    if not message.reply_to_message:
        raise ContinuePropagation
    text = message.text[6:]
    if not text:
        raise ContinuePropagation
    text = text[1:] if text.startswith("说") else text
    # Get Gravatar
    avatar = None
    if message.reply_to_message.from_user.photo:
        avatar = await client.download_media(message.reply_to_message.from_user.photo.big_file_id,
                                             file_name="avatar.jpg")
    # Get Name
    user_name = message.reply_to_message.from_user.first_name
    # Create image
    if avatar:
        with open(avatar, 'rb') as fh:
            buf = BytesIO(fh.read())
        ava = ImageUtil(100, 100, background=buf)
    else:
        ava = ImageUtil(100, 100, color=(0, 0, 0))
    ava.circle()
    name = ImageUtil(300, 30, font_size=30)
    name.text((0, 0), user_name)
    img = ImageUtil(700, 150, font_size=25, color="white")
    img.paste(ava, (30, 25), alpha=True)
    img.paste(name, (150, 38))
    img.text((150, 85), text, (125, 125, 125))

    if not exists("data"):
        makedirs("data")
    img.save(f"data{sep}friend_say.png")

    await message.reply_photo(f"data{sep}friend_say.png")
    raise ContinuePropagation
