from sqlmodel import SQLModel

from models.models.lofter import Lofter
from models.models.fragment import Fragment

__all__ = ["Lofter", "Fragment"]

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession


class Sqlite:
    def __init__(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///data/data.db")
        self.Session = sessionmaker(bind=self.engine, class_=AsyncSession)

    async def create_db_and_tables(self):
        async with self.engine.begin() as session:
            await session.run_sync(SQLModel.metadata.create_all)

    async def get_session(self):
        async with self.Session() as session:
            yield session

    def stop(self):
        self.Session.close_all()
