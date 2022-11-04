import contextlib
import re
from datetime import datetime

from bs4 import BeautifulSoup
from init import request
from models.fragment import AuctionStatus, UserName, TON_TO_USD_RATE, Price


class NotAvailable(Exception):
    pass


async def get_fragment_html(username: str):
    try:
        resp = await request.get(f"https://fragment.com/username/{username}", follow_redirects=False)
        assert resp.status_code == 200
        return resp.text
    except AssertionError as e:
        raise AssertionError from e
    except Exception as e:
        raise NotAvailable from e


def refresh_rate(html: str) -> None:
    pattern = re.compile(r'"tonRate":"(.+)"}}')
    with contextlib.suppress(Exception):
        TON_TO_USD_RATE["rate"] = float(pattern.findall(html)[0])


def parse_user(username: str, html: str) -> UserName:
    soup = BeautifulSoup(html, "lxml")
    try:
        refresh_rate(html)
        status = AuctionStatus(soup.find("span", {"class": "tm-section-header-status"}).getText())
        if status == AuctionStatus.OnAuction and "Highest Bid" not in html:
            status = AuctionStatus.Available
        user = UserName(name=username, status=status)
        if user.status == AuctionStatus.Available:
            user.now_price = Price(ton=int(soup.find(
                "div", {"class": "table-cell-value tm-value icon-before icon-ton"}
            ).getText().replace(",", "")))
        elif user.status == [AuctionStatus.OnAuction, AuctionStatus.Sale]:
            info = soup.find("div", {"class": "tm-section-box tm-section-bid-info"})
            user.now_price = Price(ton=int(info.find(
                "div", {"class": "table-cell-value tm-value icon-before icon-ton"}
            ).getText().replace(",", "")))
            user.end_time = datetime.fromisoformat(soup.find("time", {"class": "tm-countdown-timer"})["datetime"])
        elif user.status == AuctionStatus.Sold:
            info = soup.find("div", {"class": "tm-section-box tm-section-bid-info"})
            user.now_price = Price(ton=int(info.find(
                "div", {"class": "table-cell-value tm-value icon-before icon-ton"}
            ).getText().replace(",", "")))
            user.purchaser = info.find("a")["href"].split("/")[-1]
            user.end_time = datetime.fromisoformat(info.find("time")["datetime"])
        return user
    except (AttributeError, ValueError) as e:
        raise NotAvailable from e


async def search_fragment_html(username: str) -> str:
    try:
        resp = await request.get(f"https://fragment.com/?query={username}", follow_redirects=False)
        return resp.text
    except Exception as e:
        raise NotAvailable from e


def search_user(username: str, html: str) -> UserName:
    soup = BeautifulSoup(html, "lxml")
    try:
        user = soup.find_all("tr", {"class": "tm-row-selectable"})[0]
        status = AuctionStatus(user.find("div", {"class": "table-cell-status-thin"}).getText())
        return UserName(name=username, status=status)
    except (AttributeError, ValueError, IndexError) as e:
        raise NotAvailable from e


async def parse_fragment(username: str) -> UserName:
    try:
        html = await get_fragment_html(username)
        return parse_user(username, html)
    except AssertionError:
        html = await search_fragment_html(username)
        return search_user(username, html)
