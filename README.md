# Đếm mặt, bật LED, áp dụng filter và chụp ảnh

Chương trình chạy trên Raspberry Pi, dùng OpenCV Haar Cascade để phát hiện khuôn mặt. Cửa sổ webcam hiển thị filter trên mỗi mặt, khung xanh, số mặt và số LED sáng; terminal cũng in kết quả. Nút vật lý GPIO25 chụp ảnh có filter và lưu vào thư mục `photos/` cạnh `app.py`. Không nhận diện danh tính và không cần huấn luyện model.

## Quy tắc

- 0 mặt: tắt tất cả LED.
- 1–5 mặt: bật tương ứng 1–5 LED đầu tiên.
- Trên 5 mặt: sáng cả 5 LED; terminal vẫn in số mặt thực tế phát hiện được.
- Đếm mặt từ ảnh gốc trước khi áp dụng filter, nên quy tắc LED không đổi.
- Mỗi lần nhấn nút chụp lưu một khung hình có filter; giữ nút không chụp liên tục.
- Nhấn Q trong cửa sổ, đóng cửa sổ, Ctrl+C hoặc lỗi xử lý: đóng webcam/cửa sổ/nút, tắt LED và giải phóng GPIO.

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

### Nút chụp ảnh

Nối một phía nút nhấn với **GPIO25 (chân vật lý 22)**, phía còn lại với **GND** (ví dụ chân vật lý 6). Code dùng pull-up nội và chống dội 0.2 giây qua `gpiozero.Button`; không cần điện trở pull-up ngoài. Với nút 4 chân, chọn hai chân thuộc hai phía chỉ nối thông nhau khi nhấn. Không nối nút này với nguồn 5V.

Có thể đổi chân bằng `--button-pin`, nhưng không được trùng GPIO LED. Nút hoạt động cả khi dùng `--no-preview`. Tài liệu đấu nút: https://gpiozero.readthedocs.io/en/stable/api_input.html#button

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
GPIOZERO_PIN_FACTORY=lgpio python app.py --filter hat.png bow.png glasses.png
```

Webcam mặc định là `/dev/video0`. Nếu thiết bị thu hình ở node khác:

```bash
GPIOZERO_PIN_FACTORY=lgpio python app.py --device /dev/video2 --filter hat.png bow.png glasses.png
```

Mặc định chương trình mở cửa sổ webcam. Nếu chạy bằng SSH terminal không có giao diện đồ họa, dùng:

```bash
GPIOZERO_PIN_FACTORY=lgpio python app.py --no-preview --filter hat.png bow.png glasses.png
```

Trong cửa sổ, nhấn `S` để thử chụp bằng bàn phím, `Q` hoặc nút đóng để dừng. Sử dụng OpenCV có hỗ trợ GUI từ gói `python3-opencv`; bản `opencv-python-headless` không mở được cửa sổ.

## Phụ kiện PNG và lưu ảnh

Đặt 3 ảnh PNG **8-bit RGBA có nền trong suốt** cạnh `app.py`:

```text
face_detection_raspberry/
├── app.py
├── hat.png       # Mũ
├── bow.png       # Nơ
├── glasses.png   # Kính
└── photos/
```

Thứ tự sau `--filter` là **mũ, nơ, kính**; tên file có thể khác:

```bash
GPIOZERO_PIN_FACTORY=lgpio python app.py --filter mu.png no.png kinh.png
```

Hoặc dùng tên mặc định `hat.png`, `bow.png`, `glasses.png` rồi chạy `python app.py`. Đường dẫn tương đối được tìm cạnh `app.py`, không phụ thuộc thư mục terminal. Ảnh phụ kiện không có sẵn trong dự án; cần thêm PNG trước khi chạy thật.

Cả 3 phụ kiện được chồng lên mỗi khuôn mặt: mũ trên đầu, nơ dưới cằm, kính ở vùng mắt. Ảnh được giữ tỷ lệ và ghép theo alpha; phần vượt biên khung hình được cắt. Vị trí dựa trên khung Haar Cascade, không có landmark, nên có thể lệch khi mặt nghiêng. Có thể chỉnh tỷ lệ và vị trí trong `filters.py`.

Cửa sổ mặc định 1280×720. Nút GPIO25 hoặc phím `S` lưu cả khung ảnh có 3 phụ kiện vào `photos/` cạnh `app.py`, không kèm khung xanh hay chữ. Tên ảnh có thời gian và mã riêng để tránh ghi đè. Nếu lưu lỗi, chương trình báo lỗi và tiếp tục chạy. `.gitignore` bỏ qua ảnh chụp.

Ví dụ terminal (chỉ in dòng mới khi số mặt thay đổi):

```text
Webcam USB: /dev/video0
Có 5 LED. Nhấn Q trong cửa sổ, đóng cửa sổ hoặc Ctrl+C để dừng.
Filters: hat.png+bow.png+glasses.png | Nút chụp: GPIO25 | S: chụp trong cửa sổ
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

Số mặt giả lập bắt đầu từ 0, tăng mỗi 2 giây, lần lượt 0–6 rồi lặp lại với cấu hình 5 LED. Chế độ này chỉ in terminal, không mở cửa sổ, áp dụng filter hoặc chụp ảnh; đây là kiểm tra logic LED, không phải phát hiện mặt từ camera thật.

## Cấu trúc và luồng

```text
app.py                   Vòng lặp, kết quả terminal và cửa sổ có khung mặt
camera.py                Đọc webcam USB qua OpenCV VideoCapture
detector.py              Ảnh BGR → xám → cân bằng histogram → Haar Cascade
filters.py               Tải PNG một lần, ghép mũ/nơ/kính theo alpha
photos.py                Lưu ảnh JPEG có tên duy nhất trong photos/
photos/                  Thư mục ảnh chụp
config.py                GPIO LED/nút, độ phân giải và thiết bị webcam
hardware/__init__.py     Export class LedLab
hardware/lab1_leds.py    Bật LED theo số mặt, tắt và đóng GPIO
hardware/shutter.py      Nhận sự kiện nhấn nút, xếp yêu cầu chụp vào hàng đợi
tests/test_labs.py       Kiểm tra LED, luồng xử lý và giải phóng thiết bị
tests/test_filters_photos.py  Kiểm tra filter, nút chụp và ảnh lưu
requirements-mock.txt    Ghi chú: mô phỏng chỉ dùng thư viện chuẩn
.gitignore               Bỏ qua cache, venv và file sinh ra khi chạy
```

Luồng chạy: `webcam → phát hiện mặt trên ảnh gốc → cập nhật LED → áp dụng filter → hiển thị / lưu khi có yêu cầu`. Callback nút chỉ gửi yêu cầu, vòng lặp camera xử lý và lưu ảnh. `PiCamera` giữ tên class từ phiên bản cũ nhưng hiện đọc webcam USB.

## Lỗi thường gặp

Phiên bản phụ kiện PNG chưa chạy unittest; các test trong `tests/` thuộc phiên bản hiệu ứng trước và chưa cập nhật. Kiểm tra webcam, LED, nút và phụ kiện trên Pi trước khi trình bày.

- Thiếu PNG: đặt ảnh đúng tên cạnh `app.py` hoặc truyền tên qua `--filter`.
- PNG không hợp lệ: dùng PNG 8-bit RGBA có alpha; nền trắng không phải nền trong suốt.
- Không mở được webcam: kiểm tra node, quyền truy cập và ứng dụng khác đang dùng camera.
- Không đọc được ảnh: kiểm tra định dạng webcam hỗ trợ; thử bỏ thiết lập FPS trong `camera.py` hoặc giảm độ phân giải trong `config.py`.
- Thiếu cascade: cài `opencv-data`, hoặc đặt `haarcascade_frontalface_default.xml` vào thư mục `models/` cạnh `app.py`.
- Không import được `cv2`/`gpiozero`: kích hoạt venv tạo bằng `--system-site-packages`.
- Không mở được cửa sổ: chạy trong desktop của Pi/VNC và dùng OpenCV có GUI; khi chỉ có SSH terminal, thêm `--no-preview`.
- Không có mặt trong ảnh: thử đứng gần hơn, nhìn thẳng và tăng ánh sáng.
- Nhấn nút không chụp: kiểm tra GPIO25–GND và hai phía nút; thử phím S để xác nhận phần lưu ảnh.
- Không lưu được ảnh: kiểm tra quyền ghi thư mục dự án và dung lượng còn trống.

Tài liệu OpenCV: https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html
