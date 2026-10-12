"""Đo HC-SR04 với timeout: mất Echo không làm treo camera/web."""
import time
from config import ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN

class Ultrasonic:
    def __init__(self):
        from gpiozero import DigitalOutputDevice, DigitalInputDevice
        self.trigger = None
        self.echo = None
        try:
            self.trigger = DigitalOutputDevice(ULTRASONIC_TRIGGER_PIN, initial_value=False)
            self.echo = DigitalInputDevice(ULTRASONIC_ECHO_PIN, pull_up=False)
        except Exception:
            self.close()
            raise
        self.last_trigger = 0

    def read_cm(self):
        # HC-SR04 cần khoảng nghỉ giữa hai lần phát xung.
        time.sleep(max(0, 0.06 - (time.monotonic() - self.last_trigger)))
        if self.echo.value:
            return None  # Echo bị giữ HIGH / dây nối có vấn đề.
        self.trigger.on()
        time.sleep(0.00001)  # Xung Trigger 10 microsecond.
        self.trigger.off()
        self.last_trigger = time.monotonic()
        deadline = self.last_trigger + 0.03
        while not self.echo.value:
            if time.monotonic() >= deadline:
                return None
        start = time.monotonic()
        while self.echo.value:
            if time.monotonic() >= deadline:
                return None
        distance = (time.monotonic() - start) * 34300 / 2
        return distance if 0 < distance <= 400 else None

    def close(self):
        if self.trigger is not None:
            self.trigger.off()
            self.trigger.close()
            self.trigger = None
        if self.echo is not None:
            self.echo.close()
            self.echo = None
