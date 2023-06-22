from sqlmodel import SQLModel, Field


class Splash(SQLModel, table=True):
    __table_args__ = dict(mysql_charset="utf8mb4", mysql_collate="utf8mb4_general_ci")

    id: int = Field(primary_key=True)
    splash_image: str = Field()
    online_ts: int = Field(default=0)
    offline_ts: int = Field(default=0)
    file_id: str = Field()
    article_url: str = Field(default="")
