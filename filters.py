"""Chồng mũ, nơ và kính PNG lên mỗi khuôn mặt."""
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent
DEFAULT_FILTERS = ("hat.png", "bow.png", "glasses.png")


class FaceAccessories:
    """Thứ tự ảnh: mũ, nơ dưới cằm, kính. Tải ảnh một lần khi khởi chạy."""

    def __init__(self, paths=DEFAULT_FILTERS):
        import cv2
        if len(paths) != 3:
            raise ValueError("Cần 3 ảnh PNG theo thứ tự: mũ, nơ, kính")
        self.images = []
        self.names = []
        for filename in paths:
            path = Path(filename)
            if not path.is_absolute():
                path = ASSET_DIR / path
            if not path.is_file():
                raise FileNotFoundError(f"Thiếu phụ kiện PNG: {path}. Đặt ảnh cạnh app.py hoặc truyền --filter MU.png NO.png KINH.png")
            if path.suffix.lower() != ".png":
                raise ValueError(f"Phụ kiện phải là PNG: {path}")
            image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if image is None or image.ndim != 3 or image.shape[2] != 4 or image.dtype.name != "uint8":
                raise ValueError(f"Cần PNG 8-bit có nền trong suốt (RGBA): {path}")
            # Bỏ lề trong suốt để kích thước phụ kiện bám đúng khung mặt.
            points = cv2.findNonZero(image[:, :, 3])
            if points is None:
                raise ValueError(f"PNG hoàn toàn trong suốt: {path}")
            x, y, w, h = cv2.boundingRect(points)
            self.images.append(image[y:y+h, x:x+w])
            self.names.append(path.name)

    def apply(self, frame, boxes):
        result = frame.copy()
        for x, y, w, h in boxes:
            x, y, w, h = map(int, (x, y, w, h))
            if w <= 0 or h <= 0:
                continue
            for role, image in enumerate(self.images):
                target_w = max(1, int(w * (1.3, 0.65, 0.95)[role]))
                target_h = max(1, round(image.shape[0] * target_w / image.shape[1]))
                left = round(x + w / 2 - target_w / 2)
                if role == 0:  # Mũ: mép dưới ở gần đỉnh trán.
                    top = round(y + h * 0.12 - target_h)
                elif role == 1:  # Nơ: ngay dưới cằm.
                    top = round(y + h * 0.95)
                else:  # Kính: tâm ở vùng mắt.
                    top = round(y + h * 0.38 - target_h / 2)
                self._overlay(result, image, left, top, target_w, target_h)
        return result

    @staticmethod
    def _overlay(frame, image, x, y, width, height):
        import cv2
        fh, fw = frame.shape[:2]
        left, top = max(0, x), max(0, y)
        right, bottom = min(fw, x + width), min(fh, y + height)
        if left >= right or top >= bottom:
            return
        resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        part = resized[top-y:bottom-y, left-x:right-x]
        alpha = part[:, :, 3:4].astype("float32") / 255.0
        background = frame[top:bottom, left:right]
        frame[top:bottom, left:right] = (
            part[:, :, :3] * alpha + background * (1.0 - alpha)
        ).astype("uint8")
