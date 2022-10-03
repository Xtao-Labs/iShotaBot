import contextlib
from datetime import datetime, timedelta
from defs.glover import consumer_key, consumer_secret, access_token_key, access_token_secret

import twitter

from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo, \
    InputMediaDocument, InputMediaAnimation

twitter_api = twitter.Api(consumer_key=consumer_key,
                          consumer_secret=consumer_secret,
                          access_token_key=access_token_key,
                          access_token_secret=access_token_secret,
                          tweet_mode='extended',
                          timeout=30)


def twitter_link(status_id, qid, uid):
    if qid:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Source", url=f"https://twitter.com/{uid}/status/{status_id}"),
            InlineKeyboardButton(text="RSource", url=f"https://twitter.com/{qid}"),
            InlineKeyboardButton(text="Author", url=f"https://twitter.com/{uid}")]])
    else:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Source", url=f"https://twitter.com/{uid}/status/{status_id}"),
            InlineKeyboardButton(text="Author", url=f"https://twitter.com/{uid}")]])


def twitter_user_link(user_username, status_link):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text="Author", url=f"https://twitter.com/{user_username}"),
                                  InlineKeyboardButton(text="Status", url=status_link)]]) if status_link else \
        InlineKeyboardMarkup([[InlineKeyboardButton(text="Author", url=f"https://twitter.com/{user_username}")]])


def twitter_media(text, media_model, media_list, static: bool = False):
    media_lists = []
    for ff in range(len(media_model)):
        if static:
            media_lists.append(InputMediaDocument(
                media_list[ff],
                caption=text if ff == 0 else None,
                parse_mode=ParseMode.HTML
            ))
        elif media_model[ff] == 'photo':
            media_lists.append(InputMediaPhoto(
                media_list[ff],
                caption=text if ff == 0 else None,
                parse_mode=ParseMode.HTML
            ))
        elif media_model[ff] == 'gif':
            media_lists.append(InputMediaAnimation(
                media_list[ff],
                caption=text if ff == 0 else None,
                parse_mode=ParseMode.HTML
            ))
        else:
            media_lists.append(
                InputMediaVideo(
                    media_list[ff],
                    caption=text if ff == 0 else None,
                    parse_mode=ParseMode.HTML
                ))
    return media_lists


def get_twitter_time(date: str) -> str:
    try:
        date = datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y") + timedelta(hours=8)
        return date.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return date


def get_twitter_user(url_json):
    user_name = url_json.name
    user_username = url_json.screen_name
    status = ''
    status_link = None
    verified = '💎' if url_json.verified else ''
    protected = '🔒' if url_json.protected else ''
    if url_json.status:
        status_link = f"https://twitter.com/{user_username}/{url_json.status.id_str}"
        status = f'🆕  New Status: <a href="{status_link}">{get_twitter_time(url_json.status.created_at)}</a>\n'
    text = f'<b>Twitter User Info</b>\n\n' \
           f'Name: {verified}{protected}<code>{user_name}</code>\n' \
           f'Username: <a href="https://twitter.com/{user_username}">@{user_username}</a>\n' \
           f'Bio: <code>{url_json.description}</code>\n' \
           f'Joined: <code>{get_twitter_time(url_json.created_at)}</code>\n' \
           f'{status}' \
           f'📤 {url_json.statuses_count} ❤️{url_json.favourites_count} ' \
           f'粉丝 {url_json.followers_count} 关注 {url_json.friends_count}'
    return text, user_username, status_link


def get_twitter_status(url_json):
    created_at = get_twitter_time(url_json.created_at)
    favorite_count = url_json.favorite_count if hasattr(url_json, 'favorite_count') else 0
    retweet_count = url_json.retweet_count if hasattr(url_json, 'retweet_count') else 0
    user_name = url_json.user.name
    user_username = url_json.user.screen_name
    text = url_json.full_text if hasattr(url_json, 'full_text') else '暂 无 内 容'
    text = f'<code>{text}</code>'
    verified = ''
    protected = ''
    if url_json.user.verified:
        verified = '💎'
    if url_json.user.protected:
        protected = '🔒'
    user_text = f'{verified}{protected}<a href="https://twitter.com/{user_username}">{user_name}</a> 发表于 {created_at}' \
                f'\n👍 {favorite_count}   🔁 {retweet_count}'
    media_model = []
    media_list = []
    media_alt_list = []
    with contextlib.suppress(Exception):
        media_info = url_json.media
        for i in media_info:
            media_url = i.url if hasattr(i, 'url') else None
            if media_url:
                text = text.replace(media_url, '')
            if i.type == 'photo':
                media_model.append('photo')
                media_list.append(i.media_url_https)
            elif i.type == 'animated_gif':
                media_model.append('gif')
                media_list.append(i.video_info['variants'][0]['url'])
            else:
                media_model.append('video')
                for f in i.video_info['variants']:
                    if f['content_type'] == 'video/mp4':
                        media_list.append(f['url'])
                        break
            try:
                media_alt_list.append(i.ext_alt_text)
            except:
                media_alt_list.append('')
    quoted_status = False
    with contextlib.suppress(Exception):
        quoted = url_json.quoted_status
        quoted_status = quoted.user.screen_name + '/status/' + url_json.quoted_status_id_str
        quoted_created_at = get_twitter_time(quoted.created_at)
        quoted_favorite_count = quoted.favorite_count if hasattr(quoted, 'favorite_count') else 0
        quoted_retweet_count = quoted.retweet_count if hasattr(quoted, 'retweet_count') else 0
        quoted_user_name = quoted.user.name
        quoted_user_username = quoted.user.screen_name
        quoted_text = quoted.full_text if hasattr(quoted, 'full_text') else '暂 无 内 容'
        text += f'\n\n> <code>{quoted_text}</code>'
        quoted_verified = ''
        quoted_protected = ''
        if quoted.user.verified:
            quoted_verified = '💎'
        if quoted.user.protected:
            quoted_protected = '🔒'
        user_text += f'\n> {quoted_verified}{quoted_protected}<a href="https://twitter.com/{quoted_user_username}">' \
                     f'{quoted_user_name}</a> 发表于 {quoted_created_at}' \
                     f'\n👍 {quoted_favorite_count}   🔁 {quoted_retweet_count}'
        with contextlib.suppress(Exception):
            quoted_media_info = quoted.media
            for i in quoted_media_info:
                media_url = i.url if hasattr(i, 'url') else None
                if media_url:
                    text = text.replace(media_url, '')
                if i.type == 'photo':
                    media_model.append('photo')
                    media_list.append(i.media_url_https)
                elif i.type == 'animated_gif':
                    media_model.append('gif')
                    media_list.append(i.video_info['variants'][0]['url'])
                else:
                    media_model.append('video')
                    media_list.append(i.video_info['variants'][0]['url'])
                try:
                    media_alt_list.append(i.ext_alt_text)
                except:
                    media_alt_list.append('')
    return text, user_text, media_model, media_list, quoted_status
