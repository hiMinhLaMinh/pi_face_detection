import argparse
from contextlib import ExitStack
import logging
import time

from config import CAMERA_DEVICE, LED_PINS
from hardware import LedLab


def run(mock=False, device=CAMERA_DEVICE, preview=True):
    """Đếm mặt, cập nhật LED, terminal và cửa sổ webcam."""
    with ExitStack() as resources:
        leds = LedLab(mock=mock)
        resources.callback(leds.close)
        if not mock:
            import cv2
            from camera import PiCamera
            from detector import FaceDetector
            camera = PiCamera(device=device)
            resources.callback(camera.close)
            detector = FaceDetector()
            if preview:
                resources.callback(cv2.destroyAllWindows)
                window = "Face Detection - USB Webcam"
                cv2.namedWindow(window, cv2.WINDOW_NORMAL)

        print("MÔ PHỎNG" if mock else f"Webcam USB: {device}", flush=True)
        controls = "Nhấn Q trong cửa sổ, đóng cửa sổ hoặc Ctrl+C để dừng." if preview and not mock else "Nhấn Ctrl+C để dừng."
        print(f"Có {len(LED_PINS)} LED. {controls}", flush=True)
        started = time.monotonic()
        previous_count = None
        while True:
            if mock:
                # Mỗi mức tồn tại 2 giây; thử cả trường hợp vượt số LED.
                count = int((time.monotonic() - started) / 2) % (len(LED_PINS) + 2)
            else:
                frame = camera.read()
                boxes = detector.detect(frame)
                count = len(boxes)
            leds.update(count)
            lit = sum(leds.status()["leds"])
            if count != previous_count:
                print(f"Khuôn mặt: {count} | LED sáng: {lit}/{len(LED_PINS)}", flush=True)
                previous_count = count
            if preview and not mock:
                for x, y, w, h in boxes:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Font OpenCV mặc định không hỗ trợ tiếng Việt có dấu.
                cv2.putText(frame, f"Faces: {count} | LEDs: {lit}/{len(LED_PINS)}",
                            (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Q: quit", (15, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow(window, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    break
                if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
            time.sleep(0.06)


def main():
    parser = argparse.ArgumentParser(description="Đếm mặt từ webcam USB và bật LED")
    parser.add_argument("--mock", action="store_true", help="Mô phỏng cả camera và LED")
    parser.add_argument("--device", default=CAMERA_DEVICE, help="Thiết bị webcam, ví dụ /dev/video0")
    parser.add_argument("--no-preview", action="store_true", help="Chỉ dùng terminal, phù hợp SSH không có màn hình")
    args = parser.parse_args()
    try:
        run(mock=args.mock, device=args.device, preview=not args.no_preview)
    except KeyboardInterrupt:
        print("\nĐã dừng và giải phóng thiết bị.")
    except Exception:
        logging.exception("Không chạy được; kiểm tra webcam, GPIO và thư viện")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
