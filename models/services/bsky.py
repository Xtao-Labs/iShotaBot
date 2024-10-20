from pathlib import Path

from atproto import AsyncClient
from atproto.exceptions import BadRequestError

from typing import Optional

from atproto_client import Session, SessionEvent

from defs.glover import bsky_username, bsky_password
from init import logs

DATA_PATH = Path("data")


class SessionReuse:
    def __init__(self):
        self.session_file = DATA_PATH / "session.txt"

    def get_session(self) -> Optional[str]:
        try:
            with open(self.session_file, encoding="UTF-8") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def save_session(self, session_str) -> None:
        with open(self.session_file, "w", encoding="UTF-8") as f:
            f.write(session_str)

    async def on_session_change(self, event: SessionEvent, session: Session) -> None:
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            self.save_session(session.export())


class BskyClient:
    def __init__(self):
        self.client = AsyncClient()
        self.session = SessionReuse()
        self.client.on_session_change(self.session.on_session_change)

    async def initialize(self):
        session = self.session.get_session()
        if session:
            try:
                await self.client.login(session_string=session)
                logs.info(
                    "[bsky] Login with session success, me: %s", self.client.me.handle
                )
                return
            except BadRequestError:
                pass
        await self.client.login(bsky_username, bsky_password)
        logs.info(
            "[bsky] Login with username and password success, me: %s",
            self.client.me.handle,
        )


bsky_client = BskyClient()
