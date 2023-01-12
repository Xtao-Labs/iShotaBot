import asyncio
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

from pyrogram import Client, filters, ContinuePropagation
from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.types import Message

from defs.twitter_api import (
    twitter_api,
    get_twitter_status,
    twitter_link,
    twitter_media,
    twitter_user_link,
    get_twitter_user,
)


@Client.on_message(filters.incoming & filters.text & filters.regex(r"twitter.com/"))
async def twitter_share(client: Client, message: Message):
    if not message.text:
        return
    static = "static" in message.text
    try:
        for num in range(len(message.entities)):
            entity = message.entities[num]
            if entity.type == MessageEntityType.URL:
                url = message.text[entity.offset : entity.offset + entity.length]
            elif entity.type == MessageEntityType.TEXT_LINK:
                url = entity.url
            else:
                continue
            url = urlparse(url)
            if url.hostname and url.hostname in ["twitter.com", "vxtwitter.com"]:
                if url.path.find("status") >= 0:
                    status_id = str(
                        url.path[url.path.find("status") + 7 :].split("/")[0]
                    ).split("?")[0]
                    url_json = None
                    with ThreadPoolExecutor() as executor:
                        for _ in range(3):
                            try:
                                future = client.loop.run_in_executor(
                                    executor, twitter_api.GetStatus, status_id
                                )
                                url_json = await asyncio.wait_for(
                                    future, timeout=30, loop=client.loop
                                )
                            except Exception as e:
                                print(e)
                                return
                            if url_json:
                                break
                    if not url_json:
                        return
                    (
                        text,
                        user_text,
                        media_model,
                        media_list,
                        quoted_status,
                    ) = get_twitter_status(url_json)
                    text = f"<b>Twitter Status Info</b>\n\n{text}\n\n{user_text}"
                    if len(media_model) == 0:
                        await client.send_message(
                            message.chat.id,
                            text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                            reply_to_message_id=message.id,
                            reply_markup=twitter_link(
                                url_json.id, quoted_status, url_json.user.screen_name
                            ),
                        )
                    elif len(media_model) == 1:
                        if static:
                            await message.reply_document(
                                media_list[0],
                                caption=text,
                                quote=True,
                                parse_mode=ParseMode.HTML,
                                reply_markup=twitter_link(
                                    url_json.id,
                                    quoted_status,
                                    url_json.user.screen_name,
                                ),
                            )
                        elif media_model[0] == "photo":
                            await message.reply_photo(
                                media_list[0],
                                caption=text,
                                parse_mode=ParseMode.HTML,
                                quote=True,
                                reply_markup=twitter_link(
                                    url_json.id,
                                    quoted_status,
                                    url_json.user.screen_name,
                                ),
                            )
                        elif media_model[0] == "gif":
                            await message.reply_animation(
                                media_list[0],
                                caption=text,
                                parse_mode=ParseMode.HTML,
                                quote=True,
                                reply_markup=twitter_link(
                                    url_json.id,
                                    quoted_status,
                                    url_json.user.screen_name,
                                ),
                            )
                        else:
                            await message.reply_video(
                                media_list[0],
                                caption=text,
                                parse_mode=ParseMode.HTML,
                                quote=True,
                                reply_markup=twitter_link(
                                    url_json.id,
                                    quoted_status,
                                    url_json.user.screen_name,
                                ),
                            )
                    else:
                        await client.send_media_group(
                            message.chat.id,
                            media=twitter_media(text, media_model, media_list, static),
                        )
                elif url.path == "/":
                    return
                else:
                    # 解析用户
                    uid = url.path.replace("/", "")
                    url_json = None
                    with ThreadPoolExecutor() as executor:
                        for _ in range(3):
                            try:
                                future = client.loop.run_in_executor(
                                    executor, twitter_api.GetUser, None, uid
                                )
                                url_json = await asyncio.wait_for(
                                    future, timeout=30, loop=client.loop
                                )
                            except Exception as e:
                                print(e)
                                return
                            if url_json:
                                break
                    if not url_json:
                        return
                    text, user_username, status_link = get_twitter_user(url_json)
                    await message.reply_photo(
                        url_json.profile_image_url_https.replace("_normal", ""),
                        caption=text,
                        quote=True,
                        reply_markup=twitter_user_link(user_username, status_link),
                    )
    except Exception as e:
        print(e)
    raise ContinuePropagation
