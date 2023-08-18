from sqlmodel import SQLModel

from models.models.bilifav import BiliFav
from models.models.lofter import Lofter
from models.models.fragment import Fragment
from models.models.splash import Splash

__all__ = ["BiliFav", "Lofter", "Fragment", "Splash", "Sqlite"]

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession


class Sqlite:
    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///data/data.db")
        self.session = sessionmaker(bind=self.engine, class_=AsyncSession)

    async def create_db_and_tables(self):
        async with self.engine.begin() as session:
            await session.run_sync(SQLModel.metadata.create_all)

    def stop(self):
        self.session.close_all()
