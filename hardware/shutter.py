"""Nút nhấn chỉ gửi yêu cầu; việc lưu ảnh nằm trong vòng lặp camera."""
from queue import Empty, SimpleQueue


class ShutterButton:
    def __init__(self, pin):
        from gpiozero import Button
        self.requests = SimpleQueue()
        self.button = Button(pin, pull_up=True, bounce_time=0.2)
        try:
            self.button.when_pressed = self.request_capture
        except Exception:
            self.button.close()
            raise

    def request_capture(self):
        self.requests.put(True)

    def consume_press(self):
        try:
            return self.requests.get_nowait()
        except Empty:
            return False

    def close(self):
        self.button.close()
