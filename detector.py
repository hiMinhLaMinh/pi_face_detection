from pathlib import Path
import cv2

class FaceDetector:
    def __init__(self):
        # pip OpenCV và apt OpenCV lưu cascade ở các đường dẫn khác nhau.
        roots = [Path(__file__).parent / "models",
                 Path("/usr/share/opencv4/haarcascades"),
                 Path("/usr/share/opencv/haarcascades")]
        if hasattr(cv2, "data"):
            roots.insert(0, Path(cv2.data.haarcascades))
        for root in roots:
            path = root / "haarcascade_frontalface_default.xml"
            if path.is_file():
                self.model = cv2.CascadeClassifier(str(path))
                if not self.model.empty():
                    break
        else:
            raise RuntimeError("Thiếu Haar cascade. Cài opencv-data theo README.")

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        return self.model.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
