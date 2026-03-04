from sqlmodel import SQLModel, Field


class RankUpdate(SQLModel, table=True):
    __table_args__ = dict(mysql_charset="utf8mb4", mysql_collate="utf8mb4_general_ci")

    chat_id: int = Field(primary_key=True)
    log_chat_id: int = Field()
    timestamp: int = Field(default=0)
