from typing import cast, Optional, List

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from init import sqlite
from models.models.splash import Splash


class SplashService:
    @staticmethod
    async def get_by_splash_id(splash_id: int) -> Optional[Splash]:
        async with sqlite.Session() as session:
            session = cast(AsyncSession, session)
            check = Splash.id == splash_id
            statement = select(Splash).where(check)
            results = await session.exec(statement)
            return post[0] if (post := results.first()) else None

    @staticmethod
    async def get_all_splashes() -> List[Optional[Splash]]:
        async with sqlite.Session() as session:
            session = cast(AsyncSession, session)
            statement = select(Splash)
            results = await session.exec(statement)
            return [item[0] for item in results.all()]

    @staticmethod
    async def add_splash(splash: Splash):
        async with sqlite.Session() as session:
            session = cast(AsyncSession, session)
            session.add(splash)
            await session.commit()

    @staticmethod
    async def update_splash(splash: Splash):
        async with sqlite.Session() as session:
            session = cast(AsyncSession, session)
            session.add(splash)
            await session.commit()
            await session.refresh(splash)
