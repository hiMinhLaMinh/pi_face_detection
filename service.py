import threading
import time
import logging
from hardware import LABS

class FaceService:
    def __init__(self, mock=False, lab="lab1"):
        self.mock = mock
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.stop_event = threading.Event()
        self.lab = lab
        self.hardware = LABS[lab](mock=mock)
        self.faces = 0
        self.jpeg = None
        self.sequence = 0
        self.updated = None
        self.error = None
        self.thread = None
        self.running = False

    def select_lab(self, lab):
        with self.lock:
            if lab == self.lab and self.hardware is not None:
                return
            if self.hardware is not None:
                self.hardware.close()
            self.hardware = None
            self.lab = lab
            try:
                self.hardware = LABS[lab](mock=self.mock)
                # Dùng số mặt mới nhất nếu luồng camera đang hoạt động.
                self.hardware.update(self.faces if self.running else 0)
            except Exception:
                if self.hardware is not None:
                    self.hardware.close()
                    self.hardware = None
                raise

    def snapshot(self):
        with self.lock:
            return {"lab": self.lab, "faces": self.faces,
                    "mock": self.mock, "running": self.running,
                    "updated": self.updated, "error": self.error,
                    "hardware": self.hardware.status() if self.hardware else {}}

    def start(self):
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        import cv2
        camera = None
        try:
            if not self.mock:
                from camera import PiCamera
                from detector import FaceDetector
                detector = FaceDetector()
                camera = PiCamera()
            with self.lock:
                self.running = True
            while not self.stop_event.is_set():
                if self.mock:
                    import numpy as np
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    count = int(time.monotonic() / 2) % 7
                    cv2.putText(frame, "SIMULATION: " + str(count) + " faces",
                                (30, 220), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (100, 220, 100), 2)
                else:
                    frame = camera.read()
                    boxes = detector.detect(frame)
                    count = len(boxes)
                    for x, y, w, h in boxes:
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, "Faces: " + str(count), (15, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                ok, jpeg = cv2.imencode(".jpg", frame,
                                       [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ok:
                    raise RuntimeError("Không mã hóa được JPEG")
                with self.condition:
                    if self.hardware is not None:
                        self.hardware.update(count)
                    self.faces = count
                    self.jpeg = jpeg.tobytes()
                    self.sequence += 1
                    self.updated = time.time()
                    self.condition.notify_all()
                self.stop_event.wait(0.06)
        except Exception as exc:
            logging.exception("Camera / detection / hardware stopped")
            with self.condition:
                self.error = str(exc)
        finally:
            with self.condition:
                self.running = False
                self.faces = 0
                self.jpeg = None
                if self.hardware is not None:
                    self.hardware.close()
                    self.hardware = None
                self.condition.notify_all()
            if camera is not None:
                camera.close()

    def stream(self):
        sequence = -1
        while not self.stop_event.is_set():
            with self.condition:
                self.condition.wait_for(
                    lambda: self.sequence != sequence or not self.running, timeout=2)
                if not self.running:
                    return
                if self.jpeg is None or self.sequence == sequence:
                    continue
                sequence = self.sequence
                jpeg = self.jpeg
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"

    def close(self):
        self.stop_event.set()
        with self.condition:
            self.condition.notify_all()
        if self.thread is not None:
            self.thread.join(timeout=5)
        with self.lock:
            if self.hardware is not None:
                self.hardware.close()
                self.hardware = None
