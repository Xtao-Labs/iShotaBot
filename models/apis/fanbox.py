import datetime
from typing import Optional

from pydantic import BaseModel


class LiteUser(BaseModel):
    name: str
    userId: str
    iconUrl: Optional[str]


class User(BaseModel):
    coverImageUrl: Optional[str]
    creatorId: str
    description: str
    hasAdultContent: bool
    user: LiteUser
    ...

    @property
    def url(self) -> str:
        return f"https://{self.creatorId}.fanbox.cc"

    @property
    def kemono_url(self) -> str:
        return f"https://kemono.su/fanbox/user/{self.user.userId}"

    @property
    def name(self) -> str:
        return f"🔞 {self.user.name}" if self.hasAdultContent else self.user.name

    @property
    def text(self) -> str:
        return (
            f"<b>Fanbox User Info</b>\n\n"
            f"Name: <code>{self.user.name}</code>\n"
            f'Username: <a href="{self.url}">{self.creatorId}</a>\n'
            f"Bio: <code>{self.description.strip()}</code>"
        )


class Post(BaseModel):
    id: str
    coverImageUrl: Optional[str]
    creatorId: str
    excerpt: str
    feeRequired: int
    likeCount: int
    publishedDatetime: str
    title: str
    user: LiteUser
    ...

    @property
    def url(self) -> str:
        return f"{self.user_url}posts/{self.id}"

    @property
    def kemono_url(self) -> str:
        return f"https://kemono.su/fanbox/user/{self.user.userId}/post/{self.id}"

    @property
    def user_url(self) -> str:
        return f"https://{self.creatorId}.fanbox.cc/"

    @property
    def create_time(self) -> str:
        # 2022-10-05T20:21:19+09:00
        jp_time = datetime.datetime.strptime(
            self.publishedDatetime, "%Y-%m-%dT%H:%M:%S%z"
        )
        cn_time = jp_time.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
        return cn_time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def text(self) -> str:
        return (
            f"<b>Fanbox Post Info</b>\n\n"
            f"<code>{self.excerpt.strip()}</code>\n\n"
            f'<a href="{self.user_url}">{self.user.name}</a> 发表于 {self.create_time}\n'
            f"❤️ {self.likeCount}・{self.feeRequired} 日元"
        )
