from typing import Dict, List

from defs.glover import config, save_config


def set_bili_cookie(cookies: Dict[str, str]):
    cookies_str = ""
    for k, v in cookies.items():
        if k and v:
            cookies_str += f"{k}={v};"
    config.set("api", "bili_cookie", cookies_str)
    save_config()


def get_bili_cookie() -> Dict[str, str]:
    bili_cookie = config.get("api", "bili_cookie", fallback="")
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
