import argparse
from contextlib import ExitStack
import logging
import time

from config import BUTTON_PIN, CAMERA_DEVICE, LED_PINS
from filters import DEFAULT_FILTERS, FILTERS, apply_filters
from hardware import LedLab
from hardware.shutter import ShutterButton
from photos import save_photo


def run(mock=False, device=CAMERA_DEVICE, preview=True, filter_names=DEFAULT_FILTERS, button_pin=BUTTON_PIN):
    """Đếm mặt, cập nhật LED, terminal và cửa sổ webcam."""
    if len(filter_names) != 3 or any(name not in FILTERS or name == "none" for name in filter_names):
        raise ValueError("Chọn 3 filter: glasses, grayscale, blur hoặc pixelate")
    filter_label = "+".join(filter_names)
    if button_pin in LED_PINS:
        raise ValueError("GPIO của nút bấm không được trùng GPIO LED")
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
            shutter = ShutterButton(button_pin)
            resources.callback(shutter.close)
            if preview:
                resources.callback(cv2.destroyAllWindows)
                window = "Face Detection - USB Webcam"
                cv2.namedWindow(window, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window, 1280, 720)

        print("MÔ PHỎNG" if mock else f"Webcam USB: {device}", flush=True)
        controls = "Nhấn Q trong cửa sổ, đóng cửa sổ hoặc Ctrl+C để dừng." if preview and not mock else "Nhấn Ctrl+C để dừng."
        print(f"Có {len(LED_PINS)} LED. {controls}", flush=True)
        if not mock:
            keyboard = " | S: chụp trong cửa sổ" if preview else ""
            print(f"Filters: {filter_label} | Nút chụp: GPIO{button_pin}{keyboard}", flush=True)
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
                filtered = apply_filters(frame, boxes, filter_names)
                capture = shutter.consume_press()
            leds.update(count)
            lit = sum(leds.status()["leds"])
            if count != previous_count:
                print(f"Khuôn mặt: {count} | LED sáng: {lit}/{len(LED_PINS)}", flush=True)
                previous_count = count
            if preview and not mock:
                # Chụp bản có filter; khung mặt/chữ chỉ nằm trên bản hiển thị.
                display = filtered.copy()
                for x, y, w, h in boxes:
                    cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Font OpenCV mặc định không hỗ trợ tiếng Việt có dấu.
                cv2.putText(display, f"Faces: {count} | LEDs: {lit}/{len(LED_PINS)}",
                            (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display, f"Filters: {filter_label}", (15, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                cv2.putText(display, "S: photo | Q: quit", (15, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow(window, display)
                key = cv2.waitKey(1) & 0xFF
                capture = capture or key in (ord("s"), ord("S"))
                if key in (ord("q"), ord("Q")):
                    break
                if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                    break
            if not mock and capture:
                try:
                    path = save_photo(filtered, "_".join(filter_names))
                    print(f"Đã lưu ảnh: {path}", flush=True)
                except Exception:
                    logging.exception("Không lưu được ảnh; chương trình vẫn tiếp tục")
            time.sleep(0.06)


def main():
    parser = argparse.ArgumentParser(description="Đếm mặt, bật LED, áp dụng filter và chụp ảnh")
    parser.add_argument("--mock", action="store_true", help="Mô phỏng cả camera và LED")
    parser.add_argument("--device", default=CAMERA_DEVICE, help="Thiết bị webcam, ví dụ /dev/video0")
    parser.add_argument("--no-preview", action="store_true", help="Chỉ dùng terminal, phù hợp SSH không có màn hình")
    parser.add_argument("--filter", "--filters", nargs=3,
                        choices=[name for name in FILTERS if name != "none"],
                        default=DEFAULT_FILTERS,
                        help="3 hiệu ứng theo thứ tự (mặc định: grayscale blur glasses)")
    parser.add_argument("--button-pin", type=int, choices=range(28), default=BUTTON_PIN, help="GPIO BCM của nút chụp (mặc định: 25)")
    args = parser.parse_args()
    if args.button_pin in LED_PINS:
        parser.error("GPIO của nút bấm không được trùng GPIO LED")
    try:
        run(mock=args.mock, device=args.device, preview=not args.no_preview,
            filter_names=args.filter, button_pin=args.button_pin)
    except KeyboardInterrupt:
        print("\nĐã dừng và giải phóng thiết bị.")
    except Exception:
        logging.exception("Không chạy được; kiểm tra webcam, GPIO và thư viện")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
