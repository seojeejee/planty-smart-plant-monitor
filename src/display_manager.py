"""LCD 화면 상태 머신 (시간 기반 자동 사이클)"""

from time import time, sleep
import config

class DisplayManager:
    """LCD/LED/부저 출력 통합 관리"""

    # 화면 상태
    STATE_NORMAL = "normal"
    STATE_ALERT = "alert"
    STATE_SELECTING = "selecting"
    STATE_PROFILE = "profile"

    def __init__(self, lcd, led, buzzer):
        self.lcd = lcd
        self.led = led
        self.buzzer = buzzer

        self.state = self.STATE_NORMAL
        self.state_start = time()

        # 외부 데이터
        self.temp = None
        self.humi = None
        self.status = "unknown"
        self.plant_name = ""

        self.current_weather = None
        self.alert_message = None
        self.preview_plant_name = ""

    # ──────────────────────────────
    # 데이터 업데이트
    # ──────────────────────────────

    def update_sensor(self, temp, humi, status, plant_name=""):
        self.temp = temp
        self.humi = humi
        self.status = status
        self.plant_name = plant_name

    def update_weather(self, weather):
        self.current_weather = weather

    # ──────────────────────────────
    # 경고 출력
    # ──────────────────────────────

    def trigger_alert(self, alert_msg):
        print(f"⚠️ ALERT 발생: {alert_msg}")

        self.state = self.STATE_ALERT
        self.state_start = time()
        self.alert_message = alert_msg

        # LCD에 즉시 표시
        self.lcd.show_alert(alert_msg)

        # LED + LCD + 부저 동기 경고
        for _ in range(3):

            # ON
            self.lcd.display_on()
            self.led.all_on()

            self.buzzer.beep_once(duration=0.25)

            sleep(0.05)

            # OFF
            self.lcd.display_off()
            self.led.all_off()

            sleep(0.20)

        # 마지막 상태
        self.lcd.display_on()
        self.led.all_off()

    # ──────────────────────────────
    # 프로필 선택
    # ──────────────────────────────

    def start_selecting(self, plant_name):
        print(f"🔄 Selecting: {plant_name}")

        self.state = self.STATE_SELECTING
        self.state_start = time()
        self.preview_plant_name = plant_name

    def update_selecting(self, plant_name):
        self.state_start = time()
        self.preview_plant_name = plant_name

    def confirm_profile(self, plant_name):
        print(f"✅ Confirmed: {plant_name}")

        self.state = self.STATE_PROFILE
        self.state_start = time()
        self.preview_plant_name = plant_name

    def is_selecting(self):
        return self.state == self.STATE_SELECTING

    # ──────────────────────────────
    # 메인 상태 머신
    # ──────────────────────────────

    def tick(self):

        elapsed = time() - self.state_start

        # 경고 상태
        if self.state == self.STATE_ALERT:

            self.lcd.show_alert(self.alert_message)

            if elapsed >= config.LCD_ALERT_DURATION:
                self._goto_normal()

        # 선택 상태
        elif self.state == self.STATE_SELECTING:

            self.lcd.show_selecting(
                self.preview_plant_name
            )

            if elapsed >= config.PROFILE_SELECT_TIMEOUT:
                print("⏰ Selection timeout")
                self._goto_normal()

        # 변경 완료 상태
        elif self.state == self.STATE_PROFILE:

            self.lcd.show_profile_changed(
                self.preview_plant_name
            )

            if elapsed >= config.LCD_PROFILE_DURATION:
                self._goto_normal()

        # 평상시 상태
        else:

            cycle_total = (
                config.LCD_PLANT_DURATION
                + config.LCD_WEATHER_DURATION
            )

            # 수정됨: 부동소수점 오차로 인한 화면 스킵을 방지하기 위해 int()로 명시적 형변환
            cycle = int(elapsed) % cycle_total

            # 식물 상태
            if cycle < config.LCD_PLANT_DURATION:

                self.lcd.show_plant_status(
                    self.status,
                    self.temp,
                    self.humi,
                    self.plant_name
                )

            # 현재 날씨
            else:

                self.lcd.show_weather(
                    self.current_weather
                )

    def _goto_normal(self):
        self.state = self.STATE_NORMAL
        self.state_start = time()
