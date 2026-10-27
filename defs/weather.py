import contextlib
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFont

from defs.glover import caiyun_weather


def zz_font(size):
    return ImageFont.truetype(
        "resources/font/ZhuZiAWan-2.ttc", size=size, encoding="utf-8"
    )


class Weather:
    @staticmethod
    def get_api_url() -> str:
        return f"https://api.caiyunapp.com/v2.6/{caiyun_weather}/"

    @staticmethod
    async def get_weather_data(lat: float, lot: float):
        async with httpx.AsyncClient() as req:
            rain_sub = (
                await req.get(
                    Weather.get_api_url()
                    + f"{lat},{lot}/weather?alert=true&dailysteps=7&hourlysteps=72"
                )
            ).json()
            return rain_sub.get("result", {})

    @staticmethod
    def draw_bg(data):
        im = Image.open("resources/images/bg.png")
        draw = ImageDraw.Draw(im)
        # 位置
        if len(data["geo"]) > 12:
            data["geo"] = data["geo"][:12] + "..."
        draw.text((145, 71), data["geo"], "white", zz_font(90))
        # 概况
        draw.text((237, 250), data["skycon_chs"], "white", zz_font(45))
        # 温度
        draw.text((237, 320), f"{data['temperature']}℃", "white", zz_font(45))
        # 云量
        draw.text(
            (600, 320), f"{int(float(data['cloudrate']) * 100)} %", "white", zz_font(45)
        )
        # 体感温度
        draw.text((237, 390), f"{data['apparent_temperature']}℃", "white", zz_font(45))
        # 降水量
        draw.text((600, 390), data["intensity"], "white", zz_font(45))
        # 风向
        draw.text((335, 465), f"{data['direction']}°", "white", zz_font(45))
        # 风速
        draw.text((600, 465), data["speed"], "white", zz_font(45))
        # 紫外线
        draw.text((250, 610), data["ultraviolet"], "white", zz_font(45))
        # 能见度
        draw.text((605, 610), data["visibility"], "white", zz_font(45))
        # pm2.5
        draw.text((427, 680), data["pm25"], "white", zz_font(40))
        # pm10
        draw.text((427, 755), data["pm10"], "white", zz_font(40))
        # 穿衣指数
        draw.text((237, 900), data["comfort"], "white", zz_font(45))
        # AQI
        draw.text((700, 900), data["aqi"], "white", zz_font(45))
        # 下雨
        draw.text((237, 975), data["rain"], "white", zz_font(45))
        new_io = BytesIO()
        im.save(new_io, format="png")
        new_io.seek(0)
        return new_io

    @staticmethod
    def get_sky_con(skycon: str) -> str:
        # 格式化天气
        skycon_all = [
            "CLEAR_DAY",
            "CLEAR_NIGHT",
            "PARTLY_CLOUDY_DAY",
            "PARTLY_CLOUDY_NIGHT",
            "CLOUDY",
            "LIGHT_HAZE",
            "MODERATE_HAZE",
            "HEAVY_HAZE",
            "LIGHT_RAIN",
            "MODERATE_RAIN",
            "HEAVY_RAIN",
            "STORM_RAIN",
            "FOG",
            "LIGHT_SNOW",
            "MODERATE_SNOW",
            "HEAVY_SNOW",
            "STORM_SNOW",
            "DUST",
            "SAND",
            "WIND",
        ]
        skycon_now = [
            "晴朗",
            "夜间晴朗",
            "多云（白天）",
            "多云（夜间）",
            "阴",
            "轻度雾霾",
            "中度雾霾",
            "重度雾霾",
            "小雨",
            "中雨",
            "大雨",
            "暴雨",
            "雾",
            "小雪",
            "中雪",
            "大雪",
            "暴雪",
            "浮尘",
            "沙尘",
            "大风",
        ]
        skycon_chs = "未知天气"
        # 格式化天气状况
        with contextlib.suppress(ValueError):
            if skycon_int := skycon_all.index(skycon):
                skycon_chs = skycon_now[skycon_int]
        return skycon_chs

    @staticmethod
    async def get_weather_format_data(formatted_address: str, lat: float, lot: float):
        # weather_sub = ['温度', '体感温度', "气压", '相对湿度', '云量', '短波辐射', '能见度', '天气状况',
        #                '风向', '风速',
        #                '本地降水强度',
        #                '舒适度指数', '紫外线指数',
        #                'PM25浓度', 'PM10浓度', '臭氧浓度', '二氧化氮浓度', '二氧化硫浓度', '一氧化碳浓度',
        #                'AQI']
        # weather_s = ['temperature', 'apparent_temperature', 'pressure', 'humidity', 'cloudrate', 'dswrf',
        #              'visibility', 'skycon']
        # weather_air = ['pm25', 'pm10', 'o3', 'so2', 'no2', 'co']
        weather_json = await Weather.get_weather_data(lat, lot)
        weather_alert = weather_json.get("alert", {}).get("content", [])
        rain = weather_json.get("forecast_keypoint", "")
        weather_json = weather_json.get("realtime", {})
        weather_json1 = weather_json.get("air_quality", {})
        weather_alert_text = "\n================\n"
        if not len(weather_alert) == 0:
            for i in weather_alert:
                weather_alert_text += i["title"] + "\n================\n"
        else:
            weather_alert_text += "无气象局预警信息。\n================\n"
        skycon_chs = Weather.get_sky_con(weather_json["skycon"])
        data = {
            "skycon_chs": skycon_chs,
            "temperature": weather_json["temperature"],
            "cloudrate": weather_json["cloudrate"],
            "geo": formatted_address,
            "apparent_temperature": weather_json["apparent_temperature"],
            "intensity": str(weather_json["precipitation"]["local"]["intensity"]),
            "direction": weather_json["wind"]["direction"],
            "speed": str(weather_json["wind"]["speed"]),
            "ultraviolet": weather_json["life_index"]["ultraviolet"]["desc"],
            "visibility": str(weather_json["visibility"]),
            "pm25": str(weather_json1["pm25"]),
            "pm10": str(weather_json1["pm10"]),
            "o3": str(weather_json1["o3"]),
            "no2": str(weather_json1["no2"]),
            "so2": str(weather_json1["so2"]),
            "co": str(weather_json1["co"]),
            "comfort": weather_json["life_index"]["comfort"]["desc"],
            "aqi": str(weather_json1["aqi"]["chn"]),
            "rain": rain,
            "weather_alert_text": weather_alert_text,
        }
        return data

    @staticmethod
    async def get_weather_text(formatted_address: str, lat: float, lot: float):
        format_data = await Weather.get_weather_format_data(formatted_address, lat, lot)
        text = (
            f"⛳ {formatted_address}\n"
            f"✨ {format_data['skycon_chs']} - {format_data['temperature']}℃ ☁ {format_data['cloudrate']}\n\n"
            f"☂ {format_data['rain']}\n\n"
            f"🌡 {format_data['apparent_temperature']}℃ "
            f"💧 {format_data['intensity']}mm/h\n"
            f"🌀 北顺 {format_data['direction']}° - {format_data['speed']}km/h\n"
            f"🏖 紫外线 {format_data['ultraviolet']} 👀 {format_data['visibility']}km\n"
            f"🧫 PM2.5 {format_data['pm25']}μg/m3 PM10 {format_data['pm10']}μg/m3\n"
            f"💨 O3 {format_data['o3']}μg/m3 NO2 {format_data['no2']}μg/m3\n"
            f"💨 SO2 {format_data['so2']}μg/m3 CO {format_data['co']}mg/m3\n"
            f"🧣 {format_data['comfort']} 🌏 AQI {format_data['aqi']}{format_data['weather_alert_text']}"
        )
        return text

    @staticmethod
    async def get_weather_photo(formatted_address: str, lat: float, lot: float):
        data = await Weather.get_weather_format_data(formatted_address, lat, lot)
        weather_alert_text = data["weather_alert_text"]
        photo = Weather.draw_bg(data)
        text = f"⛳ {formatted_address}{weather_alert_text}"
        return photo, text
