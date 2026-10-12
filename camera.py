import cv2
from config import WIDTH, HEIGHT

class PiCamera:
    """Đọc webcam USB; giữ tên class để tương thích với service.py."""

    def __init__(self):
        self.camera = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
        try:
            if not self.camera.isOpened():
                raise RuntimeError("Không mở được webcam USB /dev/video0")
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, 15)
        except Exception:
            self.camera.release()
            raise

    def read(self):
        ok, frame = self.camera.read()
        if not ok or frame is None:
            raise RuntimeError("Không đọc được ảnh từ webcam USB")
        return frame

    def close(self):
        self.camera.release()
