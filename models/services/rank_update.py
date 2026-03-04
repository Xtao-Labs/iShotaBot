import time
from typing import cast, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from init import sqlite
from models.models.rank_update import RankUpdate


class RankUpdateAction:
    @staticmethod
    async def get_by_chat_id(chat_id: int) -> Optional[RankUpdate]:
        if not chat_id:
            return None
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            statement = select(RankUpdate).where(RankUpdate.chat_id == chat_id)
            results = await session.exec(statement)
            return post[0] if (post := results.first()) else None

    @staticmethod
    async def add_rank_update(chat_id: int, log_chat_id: int):
        rank_update = RankUpdate(
            chat_id=chat_id, log_chat_id=log_chat_id, timestamp=int(time.time())
        )
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            session.add(rank_update)
            await session.commit()
            return rank_update

    @staticmethod
    async def update_rank_update(rank_update: RankUpdate):
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            session.add(rank_update)
            await session.commit()
            await session.refresh(rank_update)
            return rank_update

    @staticmethod
    async def delete_rank_update(rank_update: RankUpdate):
        async with sqlite.session() as session:
            session = cast(AsyncSession, session)
            await session.delete(rank_update)
            await session.commit()
