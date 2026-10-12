import math
import time
from config import (SERVO_PIN, SERVO_MIN_PULSE, SERVO_MAX_PULSE,
                    FACE_DISTANCE_THRESHOLD_CM)

class ServoLab:
    name = "Lab 2 — Có mặt và khoảng cách <10 cm thì servo 90°"

    def __init__(self, mock=False):
        self.servo = None
        self.sensor = None
        self.angle = 0
        self.distance_cm = None
        self.face_present = False
        self.mock = mock
        # Test có thể gán hàm trả khoảng cách; mặc định mô phỏng 5/15 cm.
        self.mock_distance_provider = lambda: 5.0 if int(time.monotonic()/4) % 2 == 0 else 15.0
        if not mock:
            from gpiozero import AngularServo
            from .ultrasonic import Ultrasonic
            try:
                self.sensor = Ultrasonic()
                self.servo = AngularServo(
                    SERVO_PIN, min_angle=0, max_angle=180, initial_angle=0,
                    min_pulse_width=SERVO_MIN_PULSE,
                    max_pulse_width=SERVO_MAX_PULSE)
            except Exception:
                self.close()
                raise

    def update(self, face_count):
        self.face_present = face_count > 0
        distance = self.mock_distance_provider() if self.mock else self.sensor.read_cm()
        # None, NaN, vô cực, số âm và 0 đều không phải phép đo hợp lệ.
        valid = (isinstance(distance, (int, float)) and
                 math.isfinite(distance) and 0 < distance <= 400)
        self.distance_cm = float(distance) if valid else None
        allowed = (self.face_present and self.distance_cm is not None and
                   self.distance_cm < FACE_DISTANCE_THRESHOLD_CM)
        target = 90 if allowed else 0
        if target != self.angle:
            if self.servo is not None:
                self.servo.angle = target
            self.angle = target

    def status(self):
        return {"servo_angle": self.angle,
                "distance_cm": round(self.distance_cm, 2) if self.distance_cm is not None else None,
                "distance_valid": self.distance_cm is not None,
                "threshold_cm": FACE_DISTANCE_THRESHOLD_CM,
                "face_present": self.face_present,
                "condition_met": self.angle == 90}

    def close(self):
        if self.servo is not None:
            self.servo.detach()
            self.servo.close()
            self.servo = None
        if self.sensor is not None:
            self.sensor.close()
            self.sensor = None
