import base64
import json
import random
from typing import Dict, Any

from httpx import AsyncClient, Cookies

from .model import Tweet, User


class TwitterError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


class TwitterClient:
    headers = {
        "authorization": "",
        "x-guest-token": "",
        "x-twitter-auth-type": "",
        "x-twitter-client-language": "en",
        "x-twitter-active-user": "yes",
        "x-csrf-token": "",
        "Referer": "https://twitter.com/",
    }
    tokens = ["CjulERsDeqhhjSme66ECg:IQWdVyqFxghAtURHGeGiWAsmCAGmdW3WmbEx6Hck"]

    _variables = {
        "count": 20,
        "includePromotedContent": False,
        "withSuperFollowsUserFields": True,
        "withBirdwatchPivots": False,
        "withDownvotePerspective": False,
        "withReactionsMetadata": False,
        "withReactionsPerspective": False,
        "withSuperFollowsTweetFields": True,
        "withClientEventToken": False,
        "withBirdwatchNotes": False,
        "withVoice": True,
        "withV2Timeline": False,
        "__fs_interactive_text": False,
        "__fs_dont_mention_me_view_api_enabled": False,
    }
    _features = {
        "tweets": {
            "rweb_lists_timeline_redesign_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False,
        },
        "user_by_screen_name": {
            "hidden_profile_likes_enabled": False,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "subscriptions_verification_info_verified_since_enabled": True,
            "highlights_tweets_tab_ui_enabled": True,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
        },
    }

    def __init__(self):
        self.cookie = Cookies()
        self.client = AsyncClient(cookies=self.cookie, timeout=60.0)
        self.inited = False

    async def request(
        self, url: str, method: str = "GET", headers: Dict[str, str] = None, **kwargs
    ):
        headers = headers or self.headers
        headers = {key: value for key, value in headers.items() if value is not None}
        return await self.client.request(method, url, headers=headers, **kwargs)

    async def reset_session(self):
        self.headers[
            "authorization"
        ] = f"Basic {base64.b64encode(self.tokens[0].encode()).decode()}"
        response = await self.request(
            "https://api.twitter.com/oauth2/token",
            method="POST",
            params={"grant_type": "client_credentials"},
        )
        access_token = response.json()["access_token"]
        self.headers["authorization"] = f"Bearer {access_token}"
        # 生成csrf - token
        # 32个随机十六进制字符
        csrf_token = "".join([random.choice("0123456789abcdef") for _ in range(32)])
        self.cookie.set("ct0", csrf_token, domain=".twitter.com")
        self.headers["x-csrf-token"] = csrf_token
        self.headers["x-guest-token"] = ""
        # 发起初始化请求
        response = await self.request(
            "https://api.twitter.com/1.1/guest/activate.json",
            method="POST",
        )
        # 获取guest - token
        guest_token = response.json()["guest_token"]
        self.headers["x-guest-token"] = guest_token
        self.cookie.set("gt", guest_token, domain=".twitter.com")
        # 发起第二个初始化请求, 获取_twitter_sess
        await self.request(
            "https://twitter.com/i/js_inst",
            method="GET",
            params={"c_name": "ui_metrics"},
        )

    async def func(self, url: str, method: str = "GET", **kwargs):
        if not self.inited:
            await self.reset_session()
            self.inited = True
        response = await self.request(
            url,
            method=method,
            **kwargs,
        )
        if response.status_code == 403:
            await self.reset_session()
            response = await self.request(
                url,
                method=method,
                **kwargs,
            )
        if response.status_code != 200:
            raise TwitterError(response.status_code, response.text)
        csrf_token = response.cookies.get("ct0")
        if csrf_token:
            self.headers["x-csrf-token"] = csrf_token
        return response

    async def pagination_tweets(
        self,
        endpoint: str,
        variables: Dict[str, Any],
    ) -> Tweet:
        _variables = self._variables.copy()
        _variables.update(variables)
        data = await self.func(
            f"https://twitter.com/i/api{endpoint}",
            params={
                "variables": json.dumps(_variables),
                "features": json.dumps(self._features["tweets"]),
            },
        )
        result = data.json()["data"]["tweetResult"]["result"]
        type_name = result["__typename"]
        if type_name != "Tweet":
            raise TwitterError(400, result.get("reason"))
        tweet_legacy = result["legacy"]
        user = User(**result["core"]["user_results"]["result"]["legacy"])
        tweet = Tweet(**tweet_legacy, **{"user": user})
        if tweet_legacy.get("quoted_status_id_str"):
            try:
                tweet.quoted = await self.tweet_detail(
                    int(tweet_legacy["quoted_status_id_str"])
                )
            except TwitterError:
                pass
        return tweet

    async def tweet_detail(self, tid: int) -> Tweet:
        return await self.pagination_tweets(
            "/graphql/0hWvDhmW8YQ-S_ib3azIrw/TweetResultByRestId",
            variables={
                "tweetId": tid,
                "withCommunity": True,
                "includePromotedContent": False,
                "withVoice": False,
            },
        )

    async def user_by_screen_name(self, username: str):
        _variables = {"screen_name": username, "withHighlightedLabel": True}
        data = await self.func(
            "https://twitter.com/i/api/graphql/oUZZZ8Oddwxs8Cd3iW3UEA/UserByScreenName",
            params={
                "variables": json.dumps(_variables),
                "features": json.dumps(self._features["user_by_screen_name"]),
            },
        )
        return User(**data.json()["data"]["user"]["result"]["legacy"])


twitter_client = TwitterClient()
