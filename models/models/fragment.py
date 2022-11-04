from sqlmodel import SQLModel, Field


class Fragment(SQLModel, table=True):
    __table_args__ = dict(mysql_charset='utf8mb4', mysql_collate="utf8mb4_general_ci")

    cid: int = Field(primary_key=True)
    username: str = Field(primary_key=True)
    timestamp: int = Field(default=0)
