from init import request


class Exchange:
    API = (
        "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies.json"
    )

    def __init__(self):
        self.inited = False
        self.data = {}
        self.currencies = []

    async def refresh(self):
        try:
            req = await request.get(self.API)
            data = req.json()
            self.currencies.clear()
            for key in list(enumerate(data)):
                self.currencies.append(key[1].upper())
            self.currencies.sort()
            self.inited = True
        except Exception:
            pass

    async def check_ex(self, message):
        tlist = message.text.split()
        if not 2 < len(tlist) < 5:
            return "help"
        elif len(tlist) == 3:
            num = 1.0
            FROM = tlist[1].upper().strip()
            TO = tlist[2].upper().strip()
        else:
            try:
                num = float(tlist[1])
                if len(str(int(num))) > 10:
                    return "ValueBig"
                if len(str(num)) > 15:
                    return "ValueSmall"
            except ValueError:
                return "ValueError"
            FROM = tlist[2].upper().strip()
            TO = tlist[3].upper().strip()
        if self.currencies.count(FROM) == 0:
            return "FromError"
        if self.currencies.count(TO) == 0:
            return "ToError"
        endpoint = (
            f"https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest/currencies/"
            f"{FROM.lower()}/{TO.lower()}.json"
        )
        try:
            req = await request.get(endpoint)
            rate_data = req.json()
            return (
                f"{num} {FROM} = <b>{round(num * rate_data[TO.lower()], 2)} {TO}</b>\n"
                f"Rate: <b>{round(1.0 * rate_data[TO.lower()], 6)}</b>"
            )
        except Exception as e:
            print(e)
            return "请求 API 发送错误。"


exchange_client = Exchange()
