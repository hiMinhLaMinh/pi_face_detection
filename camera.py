import cv2
from config import CAMERA_DEVICE, WIDTH, HEIGHT

class PiCamera:
    """Mở, đọc và đóng webcam USB bằng OpenCV."""

    def __init__(self, device=CAMERA_DEVICE):
        self.camera = cv2.VideoCapture(device, cv2.CAP_V4L2)
        try:
            if not self.camera.isOpened():
                raise RuntimeError(f"Không mở được webcam USB {device}")
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
