import argparse
from contextlib import ExitStack
import logging
import time

from config import CAMERA_DEVICE, LED_PINS
from hardware import LedLab


def run(mock=False, device=CAMERA_DEVICE):
    """Đếm khuôn mặt, cập nhật LED và in kết quả khi số mặt thay đổi."""
    with ExitStack() as resources:
        leds = LedLab(mock=mock)
        resources.callback(leds.close)
        if not mock:
            from camera import PiCamera
            from detector import FaceDetector
            camera = PiCamera(device=device)
            resources.callback(camera.close)
            detector = FaceDetector()

        print("MÔ PHỎNG" if mock else f"Webcam USB: {device}", flush=True)
        print(f"Có {len(LED_PINS)} LED. Nhấn Ctrl+C để dừng.", flush=True)
        started = time.monotonic()
        previous_count = None
        while True:
            if mock:
                # Mỗi mức tồn tại 2 giây; thử cả trường hợp vượt số LED.
                count = int((time.monotonic() - started) / 2) % (len(LED_PINS) + 2)
            else:
                count = len(detector.detect(camera.read()))
            leds.update(count)
            if count != previous_count:
                lit = sum(leds.status()["leds"])
                print(f"Khuôn mặt: {count} | LED sáng: {lit}/{len(LED_PINS)}", flush=True)
                previous_count = count
            time.sleep(0.06)


def main():
    parser = argparse.ArgumentParser(description="Đếm mặt từ webcam USB và bật LED")
    parser.add_argument("--mock", action="store_true", help="Mô phỏng cả camera và LED")
    parser.add_argument("--device", default=CAMERA_DEVICE, help="Thiết bị webcam, ví dụ /dev/video0")
    args = parser.parse_args()
    try:
        run(mock=args.mock, device=args.device)
    except KeyboardInterrupt:
        print("\nĐã dừng và giải phóng thiết bị.")
    except Exception:
        logging.exception("Không chạy được; kiểm tra webcam, GPIO và thư viện")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
