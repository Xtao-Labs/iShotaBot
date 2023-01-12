from sqlmodel import SQLModel, Field


class Lofter(SQLModel, table=True):
    __table_args__ = dict(mysql_charset="utf8mb4", mysql_collate="utf8mb4_general_ci")

    user_id: str = Field(primary_key=True)
    username: str = Field()
    post_id: str = Field(primary_key=True)
    timestamp: int = Field(default=0)
