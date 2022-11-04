from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel

TON_TO_USD_RATE = {"rate": 1.61}


class Price(BaseModel):
    ton: int

    @property
    def usd(self) -> float:
        return self.ton * TON_TO_USD_RATE["rate"]

    @property
    def text(self) -> str:
        return f"{self.ton} TON ~ ${round(self.usd, 2)}"


class AuctionStatus(Enum):
    Available = "Available"
    OnAuction = "On auction"
    Sold = "Sold"
    Sale = "For sale"
    ComingSoon = "Coming soon"
    Unavailable = "Unavailable"

    @property
    def text(self) -> str:
        if self.value == "Available":
            return "等待出价"
        elif self.value == "On auction":
            return "正在拍卖"
        elif self.value == "Sold":
            return "已售出"
        elif self.value == "For sale":
            return "正在出售"
        elif self.value == "Coming soon":
            return "即将拍卖"
        elif self.value == "Unavailable":
            return "暂时不会出售"


class UserName(BaseModel):
    name: str
    now_price: Optional[Price]
    end_time: Optional[datetime]
    purchaser: Optional[str]
    status: AuctionStatus

    @property
    def end_human_time(self) -> str:
        diff = self.end_time - datetime.now(timezone.utc)
        args = []
        if diff.days:
            args.append(f"{diff.days} 天")
        if diff.seconds // 3600:
            args.append(f"{diff.seconds // 3600} 时")
        if diff.seconds % 3600 // 60:
            args.append(f"{diff.seconds % 3600 // 60} 分")
        if diff.seconds % 60:
            args.append(f"{diff.seconds % 60} 秒")
        return " ".join(args)

    @property
    def strf_end_time(self) -> str:
        return (self.end_time + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def text(self) -> str:
        text = f"用户名：@{self.name}\n" \
               f"状态：{self.status.text}\n"
        if self.status == AuctionStatus.Available:
            text += f"最低出价：{self.now_price.text}\n"
        elif self.status == AuctionStatus.OnAuction:
            text += f"目前最高出价：{self.now_price.text}\n" \
                    f"距离拍卖结束：{self.end_human_time}\n"
        elif self.status == AuctionStatus.Sold:
            text += f"售出价格：{self.now_price.text}\n" \
                    f"最终买家：<a href='https://tonapi.io/account/{self.purchaser}'>{self.purchaser[:12]}...</a>\n" \
                    f"售出时间：{self.strf_end_time}\n"
        elif self.status == AuctionStatus.Sale:
            text += f"售价：{self.now_price.text}\n" \
                    f"距离出售结束：{self.end_human_time}\n"
        return text
