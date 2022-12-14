import pickle
from os import sep, mkdir
from os.path import exists


def init() -> None:
    if not exists("data"):
        mkdir("data")
    if not exists(f"data{sep}anti_channel.pkl"):
        data = {}
        with open(f"data{sep}anti_channel.pkl", "wb") as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)


def add(gid: int, cid: int) -> None:
    with open(f"data{sep}anti_channel.pkl", "rb") as f:
        data = pickle.load(f)
    try:
        if cid in data[gid]:
            return
        data[gid].append(cid)
    except KeyError:
        data[gid] = [cid]
    with open(f"data{sep}anti_channel.pkl", "wb") as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)


def clean(gid: int) -> None:
    with open(f"data{sep}anti_channel.pkl", "rb") as f:
        data = pickle.load(f)
    try:
        data[gid] = []
    except KeyError:
        return
    with open(f"data{sep}anti_channel.pkl", "wb") as f:
        pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)


def get(gid: int) -> list:
    with open(f"data{sep}anti_channel.pkl", "rb") as f:
        data = pickle.load(f)
    try:
        return data[gid]
    except KeyError:
        return []


def get_status(gid: int) -> bool:
    return len(get(gid)) != 0


def check_status(gid: int, cid: int) -> bool:
    return cid in get(gid)
