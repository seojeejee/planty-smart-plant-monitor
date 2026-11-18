"""날씨 정보 모듈 (현재 날씨 + 향후 N시간 예보)"""

import requests
import config
from datetime import datetime, timedelta, timezone


class WeatherChecker:
    """OpenWeatherMap API로 날씨 확인"""

    def __init__(self, plant_profile=None):

        self.api_key = config.WEATHER_API_KEY
        self.city = config.CITY
        self.plant = plant_profile

        self.url_current = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={self.city}&appid={self.api_key}&units=metric"
        )

        self.url_forecast = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?q={self.city}&appid={self.api_key}&units=metric"
        )

        print("Weather 모듈 초기화 완료!")

    def set_plant(self, plant_profile):
        """식물 프로필 변경 시 호출"""
        self.plant = plant_profile

    def get_current(self):
        """현재 날씨"""

        try:

            response = requests.get(
                self.url_current,
                timeout=5
            )

            if response.status_code == 200:

                data = response.json()

                return {
                    "temp": data["main"]["temp"],
                    "humi": data["main"]["humidity"],
                    "weather": data["weather"][0]["main"],
                    "desc": data["weather"][0]["description"],
                }

        except Exception as e:
            print(f"현재 날씨 조회 실패: {e}")

        return None

    def get_forecast(self):
        """현재 시각 + FORECAST_HOURS 에 가장 가까운 예보"""

        try:

            response = requests.get(
                self.url_forecast,
                timeout=5
            )

            if response.status_code != 200:
                return None

            data = response.json()

            forecast_list = data.get("list", [])

            if not forecast_list:
                return None

            target_time = (
                datetime.now(timezone.utc).replace(tzinfo=None)
                + timedelta(
                    hours=config.FORECAST_HOURS
                )
            )

            closest = min(
                forecast_list,
                key=lambda item: abs(
                    datetime.strptime(
                        item["dt_txt"],
                        "%Y-%m-%d %H:%M:%S"
                    )
                    - target_time
                )
            )

            print(
                f"[Forecast] Target(+{config.FORECAST_HOURS}h): "
                f"{target_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            print(
                f"[Forecast] Selected: "
                f"{closest['dt_txt']} "
                f"{closest['weather'][0]['main']} "
                f"{closest['main']['temp']}°C"
            )

            return {
                "temp": closest["main"]["temp"],
                "humi": closest["main"]["humidity"],
                "weather": closest["weather"][0]["main"],
                "desc": closest["weather"][0]["description"],
            }

        except Exception as e:
            print(f"예보 조회 실패: {e}")

        return None

    def check_alert(self):
        """예보 기반 경고"""

        forecast = self.get_forecast()

        if forecast is None:
            return None

        main = forecast["weather"].lower()
        temp = forecast["temp"]

        # 악천후
        if "thunderstorm" in main:
            return ("WARNING!", "Thunderstorm")

        if "snow" in main:
            return ("WARNING!", "Snow coming!")

        if "rain" in main or "drizzle" in main:
            return ("WARNING!", "Rain coming!")

        # 식물 기준 미래 온도
        if self.plant:

            if temp < self.plant["temp_min"]:
                return (
                    "WARNING!",
                    f"Too Cold {temp:.0f}C"
                )

            if temp > self.plant["temp_max"]:
                return (
                    "WARNING!",
                    f"Too Hot {temp:.0f}C"
                )

        return None
