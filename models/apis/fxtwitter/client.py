from typing import Dict

from httpx import AsyncClient

from .model import FixTweet, FixTweetMedia, User


class FixTwitterError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class FixTwitterClient:
    def __init__(self):
        self.client = AsyncClient(timeout=60.0, headers={"User-Agent": "TelegramBot/iShotaBot"})
        self.url = "https://api.fxtwitter.com/"

    @staticmethod
    def gen_tweet(data: Dict) -> FixTweet:
        tweet = FixTweet(**data)
        if medias := data.get("media"):
            if all_media := medias.get("all"):
                tweet.medias = [FixTweetMedia(**i) for i in all_media]
        if quote := data.get("quote"):
            tweet.quoted = FixTwitterClient.gen_tweet(quote)
        if retweet := data.get("retweet"):
            tweet.retweeted = FixTwitterClient.gen_tweet(retweet)
        return tweet

    async def tweet_detail(self, tid: int) -> FixTweet:
        url = f"{self.url}2/thread/{tid}"
        response = await self.client.get(url)
        if response.status_code != 200:
            raise FixTwitterError(response.status_code, response.text)
        data = response.json()
        if data.get("code", 200) != 200:
            raise FixTwitterError(data.get("code"), data.get("message"))
        return self.gen_tweet(data["status"])

    async def user_by_screen_name(self, username: str) -> User:
        url = f"{self.url}{username}"
        response = await self.client.get(url)
        if response.status_code != 200:
            raise FixTwitterError(response.status_code, response.text)
        data = response.json()
        if data.get("code", 200) != 200:
            raise FixTwitterError(data.get("code"), data.get("message"))
        return User(**data["user"])


fix_twitter_client = FixTwitterClient()
