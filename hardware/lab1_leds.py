from config import LED_PINS

class LedLab:
    name = "Lab 1 — Đếm mặt và bật LED"

    def __init__(self, mock=False):
        self.leds = []
        self.count = 0
        if not mock:
            from gpiozero import LED
            try:
                for pin in LED_PINS:
                    self.leds.append(LED(pin))
            except Exception:
                self.close()
                raise

    def update(self, face_count):
        # 0 mặt: tắt hết; 1..5 mặt: bật tương ứng; >5: bật cả 5.
        self.count = min(max(int(face_count), 0), len(LED_PINS))
        for i, led in enumerate(self.leds):
            led.value = i < self.count

    def status(self):
        return {"leds": [i < self.count for i in range(len(LED_PINS))]}

    def close(self):
        for led in self.leds:
            led.off()
            led.close()
        self.leds = []
        self.count = 0
