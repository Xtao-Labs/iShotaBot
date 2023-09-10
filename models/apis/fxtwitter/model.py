from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    screen_name: str
    avatar_url: str = ""
    banner_url: str = ""
    description: str = ""
    location: str = ""
    url: str
    followers: int = 0
    following: int = 0
    joined: str
    tweets: int = 0
    likes: int = 0

    @property
    def created(self) -> datetime:
        """入推时间"""
        # 'Fri Jun 30 12:08:56 +0000 2023'
        return datetime.strptime(self.joined, "%a %b %d %H:%M:%S %z %Y") + timedelta(
            hours=8
        )

    @property
    def icon(self) -> str:
        """头像"""
        return self.avatar_url.replace("_normal.jpg", ".jpg")

    @property
    def one_line(self) -> str:
        return f'<a href="{self.url}">{self.screen_name}</a>'


class FixTweetMedia(BaseModel):
    type: str
    url: str
    width: int = 0
    height: int = 0
    altText: str = ""


class FixTweet(BaseModel):
    url: str
    id: int
    text: str
    replies: int
    """ 回复 """
    retweets: int
    """ 转推 """
    likes: int
    """ 喜欢 """
    created_at: str
    views: int
    """ 阅读次数 """
    source: str
    medias: Optional[List[FixTweetMedia]] = None
    author: User
    retweeted: "FixTweet" = None
    quoted: "FixTweet" = None

    @property
    def created(self) -> datetime:
        # 'Fri Jun 30 12:08:56 +0000 2023'
        return datetime.strptime(
            self.created_at, "%a %b %d %H:%M:%S %z %Y"
        ) + timedelta(hours=8)

    @property
    def retweet_or_quoted(self) -> "FixTweet":
        return self.retweeted or self.quoted
