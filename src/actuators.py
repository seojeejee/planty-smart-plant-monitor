"""출력 장치 제어 (LED, Buzzer, LCD - lgpio)"""

import warnings
warnings.filterwarnings("ignore")

import lgpio
from time import sleep
import config
from gpio_handle import get_handle

H = get_handle()


class LEDController:
    """3색 LED 제어"""

    def __init__(self):
        self.red    = config.PIN_LED_RED
        self.yellow = config.PIN_LED_YELLOW
        self.green  = config.PIN_LED_GREEN

        for pin in [self.red, self.yellow, self.green]:
            lgpio.gpio_claim_output(H, pin, 0)

        print("LED 초기화 완료!")

    def all_off(self):
        lgpio.gpio_write(H, self.red, 0)
        lgpio.gpio_write(H, self.yellow, 0)
        lgpio.gpio_write(H, self.green, 0)

    def all_on(self):
        lgpio.gpio_write(H, self.red, 1)
        lgpio.gpio_write(H, self.yellow, 1)
        lgpio.gpio_write(H, self.green, 1)

    def show_status(self, status):
        self.all_off()
        if status == "happy":
            lgpio.gpio_write(H, self.green, 1)
        elif status == "soso":
            lgpio.gpio_write(H, self.yellow, 1)
        elif status == "help":
            lgpio.gpio_write(H, self.red, 1)

    def blink(self, color, times=3, interval=0.2):
        pin = {"red": self.red, "yellow": self.yellow, "green": self.green}[color]
        for _ in range(times):
            lgpio.gpio_write(H, pin, 1)
            sleep(interval)
            lgpio.gpio_write(H, pin, 0)
            sleep(interval)

    def alert_blink(self, times=3, interval=0.2):
        """경보용 - 3색 동시 깜빡임"""
        for _ in range(times):
            self.all_on()
            sleep(interval)
            self.all_off()
            sleep(interval)

    def cleanup(self):
        self.all_off()


class Buzzer:
    """부저 제어 (lgpio PWM)"""

    def __init__(self):
        self.pin = config.PIN_BUZZER
        lgpio.gpio_claim_output(H, self.pin, 0)
        print("Buzzer 초기화 완료!")

    def beep(self, freq=None, duration=None):
        if freq is None:
            freq = config.BUZZER_FREQ_HIGH
        if duration is None:
            duration = config.BUZZER_DURATION

        try:
            lgpio.tx_pwm(H, self.pin, freq, 50)
            sleep(duration)
            lgpio.tx_pwm(H, self.pin, 0, 0)
        except Exception:
            half_period = 1.0 / (2 * freq)
            cycles = int(freq * duration)
            for _ in range(cycles):
                lgpio.gpio_write(H, self.pin, 1)
                sleep(half_period)
                lgpio.gpio_write(H, self.pin, 0)
                sleep(half_period)
        lgpio.gpio_write(H, self.pin, 0)

    def beep_once(self, freq=None, duration=0.2):
        """짧은 비프 1회 (경보 깜빡임 동기용)"""
        if freq is None:
            freq = config.BUZZER_FREQ_VHIGH
        try:
            lgpio.tx_pwm(H, self.pin, freq, 50)
            sleep(duration)
            lgpio.tx_pwm(H, self.pin, 0, 0)
        except Exception:
            pass
        lgpio.gpio_write(H, self.pin, 0)

    def alert(self, freq=None, beeps=None, on_time=0.2, off_time=0.15):
        """경보용 - 짧은 비프 N회"""
        if freq is None:
            freq = config.BUZZER_FREQ_VHIGH
        if beeps is None:
            beeps = config.BUZZER_ALERT_BEEPS
        for _ in range(beeps):
            try:
                lgpio.tx_pwm(H, self.pin, freq, 50)
                sleep(on_time)
                lgpio.tx_pwm(H, self.pin, 0, 0)
            except Exception:
                pass
            sleep(off_time)
        lgpio.gpio_write(H, self.pin, 0)

    def cleanup(self):
        try:
            lgpio.tx_pwm(H, self.pin, 0, 0)
        except Exception:
            pass
        lgpio.gpio_write(H, self.pin, 0)


class LCD:
    """GPIO 직접 연결 LCD (8bit 모드)"""

    LCD_CMD = 0
    LCD_CHR = 1

    LCD_LINE_1 = 0x80
    LCD_LINE_2 = 0xC0

    E_PULSE = 0.0005
    E_DELAY = 0.0005

    def __init__(self):
        self.rs = config.LCD_RS
        self.e  = config.LCD_E

        self.data_pins = [
            config.LCD_DB0, config.LCD_DB1,
            config.LCD_DB2, config.LCD_DB3,
            config.LCD_DB4, config.LCD_DB5,
            config.LCD_DB6, config.LCD_DB7,
        ]
        self.is_on = True
        self._last_line1 = None
        self._last_line2 = None

        for pin in [self.rs, self.e] + self.data_pins:
            lgpio.gpio_claim_output(H, pin, 0)

        self._init_lcd()
        print("LCD 초기화 완료! (8bit 모드)")

    def _init_lcd(self):
        sleep(0.05)
        self._send(0x38, self.LCD_CMD)
        sleep(0.005)
        self._send(0x38, self.LCD_CMD)
        sleep(0.001)
        self._send(0x38, self.LCD_CMD)

        self._send(0x38, self.LCD_CMD)
        self._send(0x0C, self.LCD_CMD)
        self._send(0x06, self.LCD_CMD)
        self._send(0x01, self.LCD_CMD)
        sleep(0.002)

    def _pulse_enable(self):
        lgpio.gpio_write(H, self.e, 0)
        sleep(self.E_DELAY)
        lgpio.gpio_write(H, self.e, 1)
        sleep(self.E_PULSE)
        lgpio.gpio_write(H, self.e, 0)
        sleep(self.E_DELAY)

    def _send(self, data, mode):
        lgpio.gpio_write(H, self.rs, mode)
        for i in range(8):
            bit = 1 if (data & (1 << i)) else 0
            lgpio.gpio_write(H, self.data_pins[i], bit)
        self._pulse_enable()

    def clear(self):
        self._send(0x01, self.LCD_CMD)
        sleep(0.002)
        self._last_line1 = None
        self._last_line2 = None

    def _print_line(self, row, text):
        addr = self.LCD_LINE_1 if row == 0 else self.LCD_LINE_2
        self._send(addr, self.LCD_CMD)
        text = str(text).center(16)[:16]
        for char in text:
            self._send(ord(char), self.LCD_CHR)

    def show(self, line1="", line2=""):
        """똑같은 내용이면 다시 그리지 않음 (깜빡임 방지)"""
        if not self.is_on:
            return
        if line1 == self._last_line1 and line2 == self._last_line2:
            return
        self.clear()
        self._print_line(0, line1)
        self._print_line(1, line2)
        self._last_line1 = line1
        self._last_line2 = line2

    # ───────── 화면별 메서드 ─────────

    def show_welcome(self):
        self.show("Hello, friend!", "Nice to see u!")

    def show_plant_status(self, status, temp, humi, plant_name=""):
        """식물 상태 화면"""
        if temp is None or humi is None:
            self.show("Planty Ready", plant_name)
            return
        messages = {
            "happy": "I'm happy! :)",
            "soso":  "Feeling so-so",
            "help":  "Help me! T_T",
        }
        line1 = messages.get(status, "Planty Ready")
        line2 = f"T:{temp:.0f}C H:{humi:.0f}%"
        self.show(line1, line2)

    def show_weather(self, weather):
        """현재 날씨 화면"""
        if weather is None:
            self.show("Weather", "No Data")
            return
        line1 = f"Sky: {weather['weather']}"
        line2 = f"T:{weather['temp']:.0f}C H:{weather['humi']:.0f}%"
        self.show(line1, line2)

    def show_alert(self, alert_msg):
        """날씨 경보 화면 - (line1, line2) 튜플"""
        if isinstance(alert_msg, tuple):
            self.show(alert_msg[0], alert_msg[1])
        else:
            self.show("WARNING!", str(alert_msg)[:16])

    def show_selecting(self, plant_name):
        """프로필 선택 중 (MOVE 버튼 눌렀을 때)"""
        self.show("Select Plant?", plant_name)

    def show_profile_changed(self, plant_name):
        """프로필 확정 시 (CONFIRM 후 2초)"""
        self.show("Plant Changed!", plant_name)

    def display_off(self):
        """LCD 표시만 끔 (데이터는 유지 → 빠른 깜빡임용)"""
        self._send(0x08, self.LCD_CMD)

    def display_on(self):
        """LCD 표시 다시 켜기"""
        self._send(0x0C, self.LCD_CMD)

    def turn_off(self):
        self.clear()
        self.is_on = False

    def turn_on(self):
        self.is_on = True

    def cleanup(self):
        self.clear()
