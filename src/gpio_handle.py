"""Share one lgpio chip handle across the sensor and actuator modules."""

import lgpio

_handle = None


def get_handle():
    global _handle
    if _handle is None:
        _handle = lgpio.gpiochip_open(0)
    return _handle


def close_handle():
    global _handle
    if _handle is not None:
        lgpio.gpiochip_close(_handle)
        _handle = None
