from pathlib import Path

from sqlmodel import SQLModel

from models.models.bilifav import BiliFav
from models.models.fragment import Fragment
from models.models.lofter import Lofter
from models.models.splash import Splash

__all__ = ["BiliFav", "Fragment", "Lofter", "Splash", "Sqlite"]

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    close_all_sessions,
    create_async_engine,
)

DB_LOCK_PATH = Path("data") / "data.lock"


class Sqlite:
    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///data/data.db")
        self.session = async_sessionmaker(bind=self.engine, class_=AsyncSession)

    @staticmethod
    def need_create_db() -> bool:
        return not DB_LOCK_PATH.exists()

    @staticmethod
    def create_db_lock():
        DB_LOCK_PATH.touch(exist_ok=True)

    async def create_db_and_tables(self):
        if not self.need_create_db():
            return
        async with self.engine.begin() as session:
            await session.run_sync(SQLModel.metadata.create_all)
        self.create_db_lock()

    async def stop(self):
        await close_all_sessions()
