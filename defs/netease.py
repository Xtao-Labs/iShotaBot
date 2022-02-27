# -*- coding: utf-8 -*-

from re import findall
from asyncio import create_subprocess_shell, sleep
from asyncio.subprocess import PIPE
from sys import executable
from os import sep, remove, listdir, rename
from os.path import isfile, getsize, splitext

from pyncm import GetCurrentSession, apis, SetCurrentSession, LoadSessionFromString
from pyncm.utils.helper import TrackHelper

from pyrogram.types import Message


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


async def netease_down(track_info: dict, song_info: dict, song, song_id: int) -> str:
    for i in listdir('data'):
        if splitext(i)[1] == ".lrc":
            remove(i)
            continue
        if song_info["songs"][0]["name"] in splitext(i)[0]:
            return i
    # Download
    await execute(f"{executable} -m pyncm http://music.163.com/song?id={song_id} "
                  f"--output data --load data/session.ncm --lyric-no lrc --lyric-no tlyric --lyric-no romalrc")
    for i in listdir('data'):
        if splitext(i)[1] == ".lrc":
            remove(i)
            continue
        if song_info["songs"][0]["name"] in splitext(i)[0]:
            name = f'data{sep}{song_info["songs"][0]["name"]}{splitext(i)[1]}'
            rename(i, name)
            return name
    return ""


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
    path = await netease_down(track_info, song_info, song, song_id)
    if path:
        await context.edit("正在上传歌曲。。。")
    else:
        msg = await message.edit(f"**没有找到歌曲**，请检查歌曲id是否正确。")
        await sleep(5)
        await msg.delete()
        return
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


async def execute(command, pass_error=True):
    """ Executes command and returns output, with the option of enabling stderr. """
    executor = await create_subprocess_shell(
        command,
        stdout=PIPE,
        stderr=PIPE,
        stdin=PIPE
    )

    stdout, stderr = await executor.communicate()
    if pass_error:
        try:
            result = str(stdout.decode().strip()) \
                     + str(stderr.decode().strip())
        except UnicodeDecodeError:
            result = str(stdout.decode('gbk').strip()) \
                     + str(stderr.decode('gbk').strip())
    else:
        try:
            result = str(stdout.decode().strip())
        except UnicodeDecodeError:
            result = str(stdout.decode('gbk').strip())
    return result
