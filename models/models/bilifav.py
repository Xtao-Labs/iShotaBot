from sqlmodel import SQLModel, Field


class BiliFav(SQLModel, table=True):
    __table_args__ = dict(mysql_charset="utf8mb4", mysql_collate="utf8mb4_general_ci")

    id: int = Field(primary_key=True)
    bv_id: str = Field()
    type: int = Field(default=2)
    title: str = Field()
    cover: str = Field()
    message_id: int = Field(default=0)
    file_id: str = Field()
    timestamp: int = Field(default=0)
