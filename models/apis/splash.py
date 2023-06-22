import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

GAME_ID_MAP = {1: "bh3", 2: "ys", 3: "bh2", 4: "wd", 5: "dby", 6: "sr", 8: "zzz"}


class Splash(BaseModel):
    id: int
    splash_image: str
    app_path: str
    online_ts: int
    offline_ts: int
    game_id: Optional[int] = 0
    file_id: Optional[str] = ""

    @property
    def online_time(self) -> datetime:
        return datetime.fromtimestamp(int(self.online_ts))

    @property
    def online_time_str(self) -> str:
        return self.online_time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def offline_time(self) -> datetime:
        return datetime.fromtimestamp(int(self.offline_ts))

    @property
    def offline_time_str(self) -> str:
        return self.offline_time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def article_id(self) -> int:
        try:
            return int(re.search(r"article/(\d+)", self.app_path).group(1))
        except AttributeError:
            return 0

    @property
    def game_short_name(self) -> str:
        if not self.game_id:
            return ""
        return GAME_ID_MAP.get(self.game_id)

    @property
    def article_url(self) -> str:
        if self.app_path.startswith("http"):
            return self.app_path
        if not self.article_id:
            return ""
        if not self.game_short_name:
            return ""
        return f"https://www.miyoushe.com/{self.game_short_name}/article/{self.article_id}"

    @property
    def text(self) -> str:
        return f"#id{self.id} \n" \
               f"ID：<code>{self.id}</code>\n" \
               f"所属分区：<code>{self.game_id} - {self.game_short_name}</code>\n" \
               f"开始时间：<code>{self.online_time_str}</code>\n" \
               f"结束时间：<code>{self.offline_time_str}</code>\n" \
               f"链接： {self.splash_image}\n" \
               f"文章链接： {self.article_url}"
