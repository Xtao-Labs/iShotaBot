# -*- coding: utf-8 -*-

import base64
from re import findall
from asyncio import sleep
from os import sep, remove, listdir
from os.path import isfile, exists, getsize

from mutagen.mp3 import EasyMP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
from pyncm import GetCurrentSession, apis, SetCurrentSession, LoadSessionFromString
from pyncm.utils.helper import TrackHelper

from pyrogram.types import Message


def download_by_url(url, dest):
    # Downloads generic content
    response = GetCurrentSession().get(url, stream=True)
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(1024 * 2 ** 10):
            f.write(chunk)  # write every 1MB read
    return dest


def gen_author(song_info: dict) -> str:
    data = []
    for i in song_info["songs"][0]["ar"]:
        data.append(i["name"])
    return " ".join(data)


def get_duration(song_info: dict, track_info: dict) -> int:
    if track_info["data"][0]["freeTrialInfo"]:
        return track_info["data"][0]["freeTrialInfo"]["end"] - track_info["data"][0]["freeTrialInfo"]["start"]
    else:
        return int(song_info["songs"][0]["dt"] / 1000)


def get_file_size(path: str) -> float:
    return round(getsize(path) / float(1024 * 1024), 2)


def get_music_id(url: str) -> int:
    if ("music.163.com" in url) and ("playlist" not in url):
        data = findall(r'\?id=([0-9]*)', url)
        if len(data) >= 1:
            return int(data[0])
        else:
            return 0
    else:
        return 0


def tag_audio(track, file: str, cover_img: str = ''):
    def write_keys(song):
        # Write trackdatas
        song['title'] = track.TrackName
        song['artist'] = track.Artists
        song['album'] = track.AlbumName
        song['tracknumber'] = str(track.TrackNumber)
        song['date'] = str(track.TrackPublishTime)
        song.save()

    def mp3():
        song = EasyMP3(file)
        write_keys(song)
        if exists(cover_img):
            song = ID3(file)
            song.update_to_v23()  # better compatibility over v2.4
            song.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='',
                          data=open(cover_img, 'rb').read()))
            song.save(v2_version=3)

    def flac():
        song = FLAC(file)
        write_keys(song)
        if exists(cover_img):
            pic = Picture()
            pic.data = open(cover_img, 'rb').read()
            pic.mime = 'image/jpeg'
            song.add_picture(pic)
            song.save()

    def ogg():
        song = OggVorbis(file)
        write_keys(song)
        if exists(cover_img):
            pic = Picture()
            pic.data = open(cover_img, 'rb').read()
            pic.mime = 'image/jpeg'
            song["metadata_block_picture"] = [base64.b64encode(pic.write()).decode('ascii')]
            song.save()

    format_ = file.split('.')[-1].upper()
    for ext, method in [({'MP3'}, mp3), ({'FLAC'}, flac), ({'OGG', 'OGV'}, ogg)]:
        if format_ in ext:
            return method() or True
    return False


async def netease_down(track_info: dict, song_info: dict, song) -> str:
    if not isfile(f'data{sep}{song_info["songs"][0]["name"]}.{track_info["data"][0]["type"]}'):
        # Downloding source audio
        download_by_url(track_info["data"][0]["url"],
                        f'data{sep}{song_info["songs"][0]["name"]}.{track_info["data"][0]["type"]}')
        # Downloading cover
        if not isfile(f'data{sep}{song_info["songs"][0]["name"]}.jpg'):
            download_by_url(song.AlbumCover,
                            f'data{sep}{song_info["songs"][0]["name"]}.jpg')
        # 设置标签
        tag_audio(song, f'data{sep}{song_info["songs"][0]["name"]}.{track_info["data"][0]["type"]}',
                  f'data{sep}{song_info["songs"][0]["name"]}.jpg')
    # 返回
    return f'data{sep}{song_info["songs"][0]["name"]}.{track_info["data"][0]["type"]}'


async def start_download(context: Message, message: Message, song_id: int, flac_mode):
    # 加载登录信息
    if isfile(f"data{sep}session.ncm"):
        with open(f"data{sep}session.ncm") as f:
            SetCurrentSession(LoadSessionFromString(f.read()))
    # 海外用户
    GetCurrentSession().headers['X-Real-IP'] = '118.88.88.88'
    # 获取歌曲质量是否大于 320k HQ
    track_info = apis.track.GetTrackAudio([song_id], bitrate=3200 * 1000 if flac_mode else 320000)
    # 获取歌曲详情
    song_info = apis.track.GetTrackDetail([song_id])
    if track_info["data"][0]["code"] == 404:
        msg = await message.edit(f"**没有找到歌曲**，请检查歌曲id是否正确。")
        await sleep(5)
        await msg.delete()
        return
    await context.edit(f"正在下载歌曲：**{song_info['songs'][0]['name']} - {gen_author(song_info)}** "
                       f"{round(track_info['data'][0]['size'] / 1000 / 1000, 2)} MB")
    # 下载歌曲并且设置歌曲标签
    song = TrackHelper(song_info['songs'][0])
    # 转义
    for char in song_info["songs"][0]["name"]:
        if char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            song_info["songs"][0]["name"] = song_info["songs"][0]["name"].replace(char, '')
    path = await netease_down(track_info, song_info, song)
    await context.edit("正在上传歌曲。。。")
    # 上传歌曲
    cap_ = ""
    # 提醒登录VIP账号
    if track_info["data"][0]["freeTrialInfo"]:
        cap_ = f"**非VIP，正在试听 {track_info['data'][0]['freeTrialInfo']['start']}s ~ \n" \
               f"{track_info['data'][0]['freeTrialInfo']['end']}s**\n"
    cap = f"「**{song_info['songs'][0]['name']}**」\n" \
          f"{gen_author(song_info)}\n" \
          f"文件大小：{get_file_size(path)} MB\n" \
          f"\n{cap_}" \
          f"#netease #{int(track_info['data'][0]['br'] / 1000)}kbps #{track_info['data'][0]['type']}"
    await message.reply_audio(
        path,
        caption=cap,
        title=song_info['songs'][0]['name'],
        thumb=f'data{sep}{song_info["songs"][0]["name"]}.jpg',
        duration=get_duration(song_info, track_info),
        performer=gen_author(song_info),
    )
    await context.delete()
    # 过多文件自动清理
    if len(listdir("data")) > 100:
        for i in listdir("data"):
            if i.find(".mp3") != -1 or i.find(".jpg") != -1 or i.find(".flac") != -1 or i.find(".ogg") != -1:
                remove(f"data{sep}{i}")
