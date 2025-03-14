import traceback
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from defs.fix_twitter_api import Reply, process_status


class ExchangeData(BaseModel):
    to: list[str]
    action: str
    type: str
    data: dict[str, Any]

    @property
    def need_process(self) -> bool:
        return "ishotabot" in self.to


class ExchangeDataTwitterData(BaseModel):
    cid: int
    id: str


class ExchangeDataTwitter(ExchangeData):
    data: ExchangeDataTwitterData


def get_process_data(data: str) -> Optional[ExchangeData]:
    try:
        raw = ExchangeData.model_validate_json(data)
    except ValidationError:
        return None
    if not raw.need_process:
        return None
    if raw.type == "twitter":
        try:
            return ExchangeDataTwitter.model_validate_json(data)
        except ValidationError:
            return None


async def process_data_twitter(data: ExchangeDataTwitter) -> None:
    if data.action == "send_status":
        reply = Reply(cid=data.data.cid)
        try:
            await process_status(reply, data.data.id)
        except Exception as e:
            traceback.print_exc()


async def process_data(data: str) -> Optional[ExchangeData]:
    raw = get_process_data(data)
    if not raw:
        return None
    if isinstance(raw, ExchangeDataTwitter):
        await process_data_twitter(raw)
