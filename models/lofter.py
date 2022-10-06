from typing import cast, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from init import sqlite
from models.models.lofter import Lofter


class LofterPost:
    @staticmethod
    async def get_by_post_and_user_id(user_id: str, post_id: str) -> Optional[Lofter]:
        async with sqlite.Session() as session:
            session = cast(AsyncSession, session)
            if user_id != "0":
                check = Lofter.post_id == post_id and Lofter.user_id == user_id
            else:
                check = Lofter.post_id == post_id
            statement = select(Lofter).where(check)
            results = await session.exec(statement)
            if post := results.first():
                return post[0]
            else:
                return None

    @staticmethod
    async def get_by_post_id(post_id: str) -> Optional[Lofter]:
        return await LofterPost.get_by_post_and_user_id("0", post_id)

    @staticmethod
    async def add_post(post: Lofter):
        async with sqlite.Session() as session:
            session = cast(AsyncSession, session)
            session.add(post)
            await session.commit()
