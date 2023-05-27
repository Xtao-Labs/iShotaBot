from typing import Dict, List

from defs.glover import bili_cookie


def get_bili_cookie() -> Dict[str, str]:
    data = {}
    for i in bili_cookie.split(";"):
        if i:
            k, v = i.split("=")
            data[k] = v
    return data


def get_bili_browser_cookie() -> List[Dict[str, str]]:
    cookie = get_bili_cookie()
    data = []
    for k, v in cookie.items():
        data.append(
            {
                "name": k,
                "value": v,
                "domain": ".bilibili.com",
                "path": "/",
            }
        )
    return data
