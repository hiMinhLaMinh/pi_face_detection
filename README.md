# Đếm khuôn mặt bằng webcam USB và bật LED

Chương trình chạy trên Raspberry Pi, dùng OpenCV Haar Cascade để phát hiện khuôn mặt. Cửa sổ webcam hiển thị khung xanh quanh mỗi mặt, số mặt và số LED sáng; terminal cũng in kết quả. Không nhận diện danh tính và không cần huấn luyện model.

## Quy tắc

- 0 mặt: tắt tất cả LED.
- 1–5 mặt: bật tương ứng 1–5 LED đầu tiên.
- Trên 5 mặt: sáng cả 5 LED; terminal vẫn in số mặt thực tế phát hiện được.
- Nhấn Q trong cửa sổ, đóng cửa sổ, Ctrl+C hoặc lỗi xử lý: đóng webcam/cửa sổ, tắt LED và giải phóng GPIO.

Ánh sáng kém, mặt nghiêng, che mặt hoặc mặt quá nhỏ có thể làm đếm sai. Số đếm có thể dao động giữa các khung hình.

## Đấu dây

Tắt nguồn Pi trước khi đấu GPIO. Cắm webcam vào cổng USB.

| LED | GPIO BCM | Chân vật lý Pi 4 |
|---|---|---|
| 1 | 17 | 11 |
| 2 | 27 | 13 |
| 3 | 22 | 15 |
| 4 | 23 | 16 |
| 5 | 24 | 18 |

Mỗi LED: GPIO → điện trở 220–330Ω → anode LED (chân dài); cathode (chân ngắn) → GND chung (ví dụ chân vật lý 6). Không nối LED trực tiếp vào GPIO khi thiếu điện trở.

Số LED được giới hạn bởi số chân trong `LED_PINS` ở `config.py`. Muốn hiển thị nhiều hơn 5 mặt bằng LED, cần thêm LED, điện trở và chân GPIO phù hợp vào danh sách.

## Cài và chạy trên Raspberry Pi

Với Raspberry Pi OS 64-bit có desktop, chạy từ terminal trong phiên desktop của Pi (màn hình gắn với Pi hoặc desktop qua VNC):

```bash
sudo apt update
sudo apt install -y git python3-venv python3-opencv opencv-data python3-gpiozero python3-lgpio python3-numpy v4l-utils
```

Clone repo của nhóm và vào thư mục chứa `app.py`, sau đó chạy:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
GPIOZERO_PIN_FACTORY=lgpio python app.py
```

Webcam mặc định là `/dev/video0`. Nếu thiết bị thu hình ở node khác:

```bash
GPIOZERO_PIN_FACTORY=lgpio python app.py --device /dev/video2
```

Mặc định chương trình mở cửa sổ webcam. Nếu chạy bằng SSH terminal không có giao diện đồ họa, dùng:

```bash
GPIOZERO_PIN_FACTORY=lgpio python app.py --no-preview
```

Trong cửa sổ, nhấn `Q` hoặc nút đóng để dừng. Sử dụng OpenCV có hỗ trợ GUI từ gói `python3-opencv`; bản `opencv-python-headless` không mở được cửa sổ.

Không phải mọi `/dev/video*` đều là node thu hình; chọn node của webcam có danh sách định dạng ảnh. Đóng ứng dụng khác đang dùng webcam. Không cần Picamera2, Flask, web server, servo hoặc cảm biến siêu âm.

Ví dụ terminal (chỉ in dòng mới khi số mặt thay đổi):

```text
Webcam USB: /dev/video0
Có 5 LED. Nhấn Q trong cửa sổ, đóng cửa sổ hoặc Ctrl+C để dừng.
Khuôn mặt: 0 | LED sáng: 0/5
Khuôn mặt: 2 | LED sáng: 2/5
Khuôn mặt: 6 | LED sáng: 5/5
```

Chạy thật cần quyền truy cập webcam và GPIO. Kiểm tra nhóm `video`/`gpio` của tài khoản nếu gặp lỗi quyền truy cập. Không dùng `pip` cài đè OpenCV trong môi trường chạy thật này.

## Mô phỏng trên máy tính

Không cần cài thêm thư viện hoặc có webcam/GPIO:

```bash
python3 app.py --mock
```

Số mặt giả lập bắt đầu từ 0, tăng mỗi 2 giây, lần lượt 0–6 rồi lặp lại với cấu hình 5 LED. Chế độ này chỉ in terminal và không mở cửa sổ; đây là kiểm tra logic, không phải phát hiện mặt từ camera thật.

## Cấu trúc và luồng

```text
app.py                   Vòng lặp, kết quả terminal và cửa sổ có khung mặt
camera.py                Đọc webcam USB qua OpenCV VideoCapture
detector.py              Ảnh BGR → xám → cân bằng histogram → Haar Cascade
config.py                GPIO LED, độ phân giải và thiết bị webcam
hardware/__init__.py     Export class LedLab
hardware/lab1_leds.py    Bật LED theo số mặt, tắt và đóng GPIO
tests/test_labs.py       Kiểm tra LED, luồng xử lý và giải phóng thiết bị
requirements-mock.txt    Ghi chú: mô phỏng chỉ dùng thư viện chuẩn
.gitignore               Bỏ qua cache, venv và file sinh ra khi chạy
```

Luồng chạy: `webcam → detector.detect(frame) → số mặt → leds.update(count) → terminal + cửa sổ webcam`. Chạy trong một vòng lặp, không cần thread hoặc nén JPEG. `PiCamera` giữ tên class từ phiên bản cũ nhưng hiện đọc webcam USB.

## Kiểm tra và lỗi thường gặp

```bash
python3 -m unittest discover -s tests -v
```

Test dùng thiết bị giả; cần thử camera và LED trên Pi thật trước buổi trình bày.

- Không mở được webcam: kiểm tra node, quyền truy cập và ứng dụng khác đang dùng camera.
- Không đọc được ảnh: kiểm tra định dạng webcam hỗ trợ; thử bỏ thiết lập FPS trong `camera.py` hoặc giảm độ phân giải trong `config.py`.
- Thiếu cascade: cài `opencv-data`, hoặc đặt `haarcascade_frontalface_default.xml` vào thư mục `models/` cạnh `app.py`.
- Không import được `cv2`/`gpiozero`: kích hoạt venv tạo bằng `--system-site-packages`.
- Không mở được cửa sổ: chạy trong desktop của Pi/VNC và dùng OpenCV có GUI; khi chỉ có SSH terminal, thêm `--no-preview`.
- Không có mặt trong ảnh: thử đứng gần hơn, nhìn thẳng và tăng ánh sáng.

Tài liệu OpenCV: https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
