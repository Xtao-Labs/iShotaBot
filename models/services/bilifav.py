from typing import cast, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from init import sqlite
from models.models.bilifav import BiliFav


class BiliFavAction:
    @staticmethod
    async def get_by_id(id_: int, fav: bool = False) -> Optional[BiliFav]:
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            statement = select(BiliFav).where(BiliFav.id == id_)
            if fav:
                statement = statement.where(BiliFav.message_id != 0)
            results = await session.exec(statement)
            return post[0] if (post := results.first()) else None

    @staticmethod
    async def get_by_bv_id(bv_id: str, fav: bool = False) -> Optional[BiliFav]:
        if not bv_id:
            return None
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            statement = select(BiliFav).where(BiliFav.bv_id == bv_id.lower())
            if fav:
                statement = statement.where(BiliFav.message_id != 0)
            results = await session.exec(statement)
            return post[0] if (post := results.first()) else None

    @staticmethod
    async def add_bili_fav(bili_fav: BiliFav):
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            session.add(bili_fav)
            await session.commit()

    @staticmethod
    async def update_bili_fav(bili_fav: BiliFav):
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            session.add(bili_fav)
            await session.commit()
            await session.refresh(bili_fav)
