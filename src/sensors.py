"""입력 센서 모듈 (DHT11: adafruit, Switch: lgpio)"""

import warnings
warnings.filterwarnings("ignore")

import board
import adafruit_dht
import lgpio
from time import sleep
import config
from gpio_handle import get_handle

H = get_handle()


class DHTSensor:
    """DHT11 온습도 센서 (BCM 4)"""

    def __init__(self):
        self.dht = adafruit_dht.DHT11(board.D4)
        self.last_temp = None
        self.last_humi = None
        print("DHT11 초기화 완료!")

    def read(self):
        try:
            temp = self.dht.temperature
            humi = self.dht.humidity
            if temp is not None and humi is not None:
                self.last_temp = temp
                self.last_humi = humi
                return temp, humi
        except RuntimeError:
            pass
        return self.last_temp, self.last_humi

    def cleanup(self):
        try:
            self.dht.exit()
        except Exception:
            pass


class Switch:
    """푸시 스위치 (pull-up, 눌리면 LOW)"""

    def __init__(self, pin, name=""):
        self.pin = pin
        self.name = name
        lgpio.gpio_claim_input(H, self.pin, lgpio.SET_PULL_UP)
        self._last_state = self.is_pressed()
        print(f"Switch '{name}' 초기화 완료!")

    def is_pressed(self):
        return lgpio.gpio_read(H, self.pin) == 0

    def was_pressed(self):
        """누름 이벤트 (한 번만 True 반환)"""
        current = self.is_pressed()
        pressed_event = (not self._last_state) and current
        self._last_state = current
        if pressed_event:
            sleep(0.03)  # 디바운스
        return pressed_event

    def cleanup(self):
        pass
