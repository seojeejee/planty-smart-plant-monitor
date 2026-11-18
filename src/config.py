"""Planty 시스템 전역 설정 (모든 핀: BCM 번호)"""

import os

# ─────── API 설정 ───────
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CITY = "Asan"

# ─────── GPIO 핀 설정 (BCM) ───────
PIN_DHT            = 4       # DHT11
PIN_SWITCH_MOVE    = 22      # 푸시 스위치 - 프로필 이동  (wPi 3)
PIN_SWITCH_CONFIRM = 23      # 푸시 스위치 - 프로필 확정  (wPi 4)
PIN_LED_RED        = 24      # 빨강 LED   (wPi 5)
PIN_LED_YELLOW     = 25      # 노랑 LED   (wPi 6)
PIN_LED_GREEN      = 18      # 초록 LED   (wPi 1)
PIN_BUZZER         = 17      # 부저       (wPi 0)

# ─────── LCD GPIO (8bit 모드, BCM) ───────
LCD_RS  = 26
LCD_E   = 19
LCD_DB0 = 21
LCD_DB1 = 20
LCD_DB2 = 16
LCD_DB3 = 12
LCD_DB4 = 13
LCD_DB5 = 6
LCD_DB6 = 5
LCD_DB7 = 27

LCD_COLS = 16
LCD_ROWS = 2

# ─────── 부저 설정 ───────
BUZZER_FREQ_HIGH   = 2000
BUZZER_FREQ_MID    = 1000
BUZZER_FREQ_LOW    = 500
BUZZER_FREQ_VHIGH  = 4000     # 날씨 경보용
BUZZER_DURATION    = 3
BUZZER_ALERT_BEEPS = 3        # 경보 시 3회 비프

# ─────── 식물별 적정 환경 ───────
PLANT_PROFILES = {
    "succulent": {
        "name": "Succulent",
        "temp_min": 15, "temp_max": 30,
        "humi_min": 30, "humi_max": 50,
    },
    "foliage": {
        "name": "Foliage",
        "temp_min": 18, "temp_max": 28,
        "humi_min": 50, "humi_max": 70,
    },
    "herb": {
        "name": "Herb",
        "temp_min": 15, "temp_max": 25,
        "humi_min": 40, "humi_max": 60,
    },
}

# ─────── 업데이트 주기 (초) ───────
SENSOR_INTERVAL  = 1          # DHT 읽기
WEATHER_INTERVAL = 600        # 날씨 API (10분)
LOOP_INTERVAL    = 0.05       # 메인 루프 (스위치 빠른 반응)

# ─────── LCD 사이클 시간 (초) ───────
LCD_PLANT_DURATION     = 7    # 식물 상태 표시
LCD_WEATHER_DURATION   = 3    # 날씨 표시 (7~10초)
LCD_ALERT_DURATION     = 5    # 경보 인터럽트
LCD_PROFILE_DURATION   = 2    # 프로필 전환 완료 표시
PROFILE_SELECT_TIMEOUT = 5    # 프로필 선택 중 무입력 → 자동 취소

# ─────── 날씨 예보 ───────
FORECAST_HOURS = 3            # 향후 N시간 예보 체크
