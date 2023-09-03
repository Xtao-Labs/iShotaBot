from datetime import datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel


class VideoInfoVariant(BaseModel):
    bitrate: Optional[int]
    content_type: str
    url: str


class VideoInfo(BaseModel):
    variants: List[VideoInfoVariant]

    @property
    def best_variant(self) -> VideoInfoVariant:
        variants = [
            i for i in self.variants if i.content_type.startswith("video/mp4")
        ] or self.variants
        return max(variants, key=lambda x: x.bitrate or 0)


class MediaItem(BaseModel):
    display_url: str
    expanded_url: str
    id_str: str
    media_url_https: str
    """ 真实链接 """
    type: str
    """ 类型 """
    url: str
    """ 短链接 """
    video_info: Optional[VideoInfo]
    """ 视频信息 """

    @property
    def media_url(self):
        if self.type == "photo":
            ext = self.media_url_https.split(".")[-1]
            return f"{self.media_url_https[:-(len(ext) + 1)]}?format={ext}&name=orig"
        elif self.type == "video":
            return self.video_info.best_variant.url
        return self.media_url_https


class ExtendedEntities(BaseModel):
    media: Optional[List[MediaItem]]


class User(BaseModel):
    created_at: str
    description: str
    statuses_count: int = 0
    favourites_count: int = 0
    followers_count: int = 0
    """ 关注者 """
    friends_count: int = 0
    """ 正在关注 """
    location: str
    name: str
    profile_banner_url: Optional[str] = None
    profile_image_url_https: str
    screen_name: str
    verified: bool = False
    protected: bool = False

    @property
    def created(self) -> datetime:
        """入推时间"""
        # 'Fri Jun 30 12:08:56 +0000 2023'
        return datetime.strptime(
            self.created_at, "%a %b %d %H:%M:%S %z %Y"
        ) + timedelta(hours=8)

    @property
    def icon(self) -> str:
        """头像"""
        return self.profile_image_url_https.replace("_normal.jpg", ".jpg")

    @property
    def url(self) -> str:
        """链接"""
        return f"https://twitter.com/{self.screen_name}"

    @property
    def one_line(self) -> str:
        verified = "" if not self.verified else "💎"
        protected = "" if not self.protected else "🔒"
        return f'{verified}{protected}<a href="{self.url}">{self.screen_name}</a>'


class Tweet(BaseModel):
    bookmark_count: int
    """ 书签次数 """
    created_at: str
    conversation_id_str: str
    extended_entities: Optional[ExtendedEntities] = None
    favorite_count: int
    """ 喜欢次数 """
    full_text: str
    quote_count: int
    """ 引用 """
    reply_count: int
    """ 回复 """
    retweet_count: int
    """ 转推 """
    id_str: str
    """ tweet id """
    user: User
    retweet: "Tweet" = None
    quoted: "Tweet" = None

    @property
    def created(self) -> datetime:
        # 'Fri Jun 30 12:08:56 +0000 2023'
        return datetime.strptime(
            self.created_at, "%a %b %d %H:%M:%S %z %Y"
        ) + timedelta(hours=8)

    @property
    def url(self) -> str:
        return f"https://twitter.com/{self.user.screen_name}/status/{self.id_str}"

    @property
    def retweet_or_quoted(self) -> "Tweet":
        return self.retweet or self.quoted
