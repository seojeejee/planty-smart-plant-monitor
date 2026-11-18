"""Planty 메인 실행 파일"""

import warnings
warnings.filterwarnings("ignore")

from time import sleep, time
import config
from sensors import DHTSensor, Switch
from actuators import LEDController, Buzzer, LCD
from weather import WeatherChecker
from display_manager import DisplayManager
from gpio_handle import close_handle


class Planty:
    """식물 상태 모니터링 메인 클래스"""

    def __init__(self, start_plant="foliage"):

        # 프로필 리스트
        self.profile_keys = list(config.PLANT_PROFILES.keys())

        try:
            self.current_idx = self.profile_keys.index(start_plant)
        except ValueError:
            self.current_idx = 0

        self.preview_idx = self.current_idx
        self.profile = config.PLANT_PROFILES[
            self.profile_keys[self.current_idx]
        ]

        # 모듈 초기화
        self.dht = DHTSensor()
        self.sw_move = Switch(
            config.PIN_SWITCH_MOVE,
            "MOVE"
        )
        self.sw_confirm = Switch(
            config.PIN_SWITCH_CONFIRM,
            "CONFIRM"
        )

        self.led = LEDController()
        self.buzzer = Buzzer()
        self.lcd = LCD()

        self.weather = WeatherChecker(
            self.profile
        )

        self.display = DisplayManager(
            self.lcd,
            self.led,
            self.buzzer
        )

        # 타이밍
        self.last_sensor_time = 0
        self.last_weather_time = 0

        # 위험 상태 변화 감지
        self.last_status = "unknown"

        # 초기 화면
        self.lcd.show_welcome()
        sleep(2)

        print(
            f"✅ 초기화 완료! 식물: {self.profile['name']}"
        )

    # ──────────────────────────────
    # 상태 평가
    # ──────────────────────────────

    def evaluate_status(self, temp, humi):

        if temp is None or humi is None:
            return "unknown"

        t_ok = (
            self.profile["temp_min"]
            <= temp
            <= self.profile["temp_max"]
        )

        h_ok = (
            self.profile["humi_min"]
            <= humi
            <= self.profile["humi_max"]
        )

        if t_ok and h_ok:
            return "happy"

        elif t_ok or h_ok:
            return "soso"

        else:
            return "help"

    # ──────────────────────────────
    # 위험 원인 분석
    # ──────────────────────────────

    def get_stress_reason(self, temp, humi):

        reasons = []

        if temp < self.profile["temp_min"]:
            reasons.append("Temp Low")

        elif temp > self.profile["temp_max"]:
            reasons.append("Temp High")

        if humi < self.profile["humi_min"]:
            reasons.append("Humi Low")

        elif humi > self.profile["humi_max"]:
            reasons.append("Humi High")

        if len(reasons) >= 2:
            return "Temp&Humi"

        if reasons:
            return reasons[0]

        return "Plant Stress"

    # ──────────────────────────────
    # 스위치 처리
    # ──────────────────────────────

    def handle_switches(self):

        if self.sw_move.was_pressed():

            if self.display.is_selecting():

                self.preview_idx = (
                    self.preview_idx + 1
                ) % len(self.profile_keys)

                preview_name = (
                    config.PLANT_PROFILES[
                        self.profile_keys[
                            self.preview_idx
                        ]
                    ]["name"]
                )

                self.display.update_selecting(
                    preview_name
                )

            else:

                self.preview_idx = (
                    self.current_idx + 1
                ) % len(self.profile_keys)

                preview_name = (
                    config.PLANT_PROFILES[
                        self.profile_keys[
                            self.preview_idx
                        ]
                    ]["name"]
                )

                self.display.start_selecting(
                    preview_name
                )

        if self.sw_confirm.was_pressed():

            if self.display.is_selecting():

                self.current_idx = self.preview_idx

                key = self.profile_keys[
                    self.current_idx
                ]

                self.profile = (
                    config.PLANT_PROFILES[key]
                )

                self.weather.set_plant(
                    self.profile
                )

                # 상태 초기화
                self.last_status = "unknown"

                self.display.confirm_profile(
                    self.profile["name"]
                )

                print(
                    f" 식물 변경: {self.profile['name']}"
                )

    # ──────────────────────────────
    # 센서 처리
    # ──────────────────────────────

    def handle_sensor(self):

        now = time()

        if (
            now - self.last_sensor_time
            < config.SENSOR_INTERVAL
        ):
            return

        self.last_sensor_time = now

        temp, humi = self.dht.read()

        status = self.evaluate_status(
            temp,
            humi
        )

        if status != "unknown":
            self.led.show_status(status)

        # 위험 상태 진입 시 경고
        if (
            status == "help"
            and self.last_status != "help"
        ):

            reason = self.get_stress_reason(
                temp,
                humi
            )

            self.display.trigger_alert(
                ("WARNING!", reason)
            )

        self.last_status = status

        self.display.update_sensor(
            temp,
            humi,
            status,
            self.profile["name"]
        )

        if temp is not None and humi is not None:

            print(
                f"T:{temp}°C  H:{humi}%  → {status}"
            )

    # ──────────────────────────────
    # 날씨 처리
    # ──────────────────────────────

    def handle_weather(self):

        now = time()

        if (
            now - self.last_weather_time
            < config.WEATHER_INTERVAL
        ):
            return

        self.last_weather_time = now

        current = self.weather.get_current()

        if current:

            self.display.update_weather(
                current
            )

            print(
                f" 현재: "
                f"{current['weather']} "
                f"{current['temp']}°C"
            )

        alert = self.weather.check_alert()

        if alert:
            self.display.trigger_alert(
                alert
            )

    # ──────────────────────────────
    # 메인 루프
    # ──────────────────────────────

    def run(self):

        print(
            "Planty 시작! (Ctrl+C로 종료)"
        )

        self.handle_weather()

        try:

            while True:

                self.handle_switches()
                self.handle_sensor()
                self.handle_weather()
                self.display.tick()

                sleep(
                    config.LOOP_INTERVAL
                )

        except KeyboardInterrupt:

            print("\n종료 중...")

        finally:

            self.cleanup()

    def cleanup(self):

        self.led.cleanup()
        self.buzzer.cleanup()
        self.lcd.cleanup()

        self.dht.cleanup()

        self.sw_move.cleanup()
        self.sw_confirm.cleanup()

        close_handle()

        print(" 정리 완료!")


if __name__ == "__main__":

    planty = Planty(
        start_plant="foliage"
    )

    planty.run()
