# Raspberry Pi Face Labs — Camera Module 3

Dự án học tập: phát hiện và đếm khuôn mặt nhìn tương đối thẳng bằng Haar Cascade OpenCV. Không nhận diện danh tính. Không cần huấn luyện model. Góc nghiêng, che mặt hoặc ánh sáng kém có thể làm đếm sai; không dùng số đếm này cho hệ thống an ninh.

## 1. Quy tắc hai lab

Lab 1 giữ nguyên: số mặt 0–5 tương ứng số LED sáng; >5 mặt sáng cả 5.

| Có khuôn mặt | Khoảng cách siêu âm | Góc servo Lab 2 |
|---|---|---|
| Không | Bất kỳ | 0° |
| Có | Nhỏ hơn 10 cm | 90° |
| Có | Đúng 10 cm hoặc lớn hơn | 0° |
| Có | Không đo được / số đo không hợp lệ | 0° |

Servo giữ góc, không quay qua lại liên tục. Khi mất một trong hai điều kiện thì về 0°. Ngưỡng dùng số đo gốc, giao diện làm tròn 2 chữ số nên 9.999 cm có thể hiển thị 10.00 nhưng vẫn nhỏ hơn 10. Cảm biến chỉ phát hiện vật cản gần, không xác định vật đó là người có khuôn mặt trong camera. Đặt cảm biến và camera phù hợp mục đích bài lab; một người ở xa và vật cản gần vẫn có thể thỏa cả hai điều kiện.

Nút trên web chọn một lab hoạt động tại một thời điểm. Lab trước được đóng trước khi khởi tạo lab mới. Khi thoát ứng dụng, servo ngắt PWM, không bảo đảm cơ khí về 0°.

## 2. Phần cứng và đấu dây (Raspberry Pi 4)

Cần Pi 4, Camera Module 3 + cáp CSI 15 chân phù hợp Pi 4, 5 LED, 5 điện trở 220–330Ω, servo SG90, HC-SR04, điện trở chia áp 1kΩ và 2kΩ, nguồn 5V riêng phù hợp servo, breadboard và dây. Pi 5/Zero dùng đầu cáp camera khác.

Tắt Pi và rút nguồn trước khi nối camera/GPIO. Cắm Camera v3 vào cổng CSI CAMERA, không vào cổng DISPLAY. Lắp cáp đúng chiều tiếp điểm theo hướng dẫn phần cứng của Pi.

| Thiết bị | GPIO BCM | Chân vật lý Pi 4 |
|---|---|---|
| LED 1 | 17 | 11 |
| LED 2 | 27 | 13 |
| LED 3 | 22 | 15 |
| LED 4 | 23 | 16 |
| LED 5 | 24 | 18 |
| Tín hiệu servo (cam/vàng) | 18 | 12 |
| HC-SR04 Trigger | 5 | 29 |
| HC-SR04 Echo qua chia áp | 6 | 31 |
| GND chung | GND | 6 (hoặc chân GND khác) |

Mỗi LED: GPIO → điện trở → anode LED (chân dài); cathode LED (chân ngắn) → GND. Servo: dây đỏ → +5V nguồn ngoài, dây nâu/đen → GND nguồn ngoài. Nối GND nguồn ngoài với GND Pi. Không đưa +5V vào GPIO và không cấp servo từ chân 3.3V. Có thể nối cả 5 LED, servo và siêu âm; các thiết bị dùng GPIO khác nhau. Điều chỉnh xung servo trong config.py theo thông số servo; giảm phạm vi nếu servo chạm giới hạn cơ khí.

### Đấu HC-SR04

- VCC → 5V Pi (chân vật lý 2 hoặc 4); GND → GND chung.
- TRIG → GPIO5 (chân vật lý 29).
- ECHO → điện trở 1kΩ → điểm nối GPIO6 (chân vật lý 31).
- Từ điểm nối GPIO6 → điện trở 2kΩ → GND.

Không nối Echo 5V trực tiếp vào Pi. Chia áp 1kΩ/2kΩ giảm Echo xuống khoảng 3.33V. Nếu đã dùng GPIO23/24 cho siêu âm trong bài khác, đổi dây theo bảng để tránh trùng LED 4/5.

## 3. Cài trên Pi

Khuyến nghị Raspberry Pi OS 64-bit có camera stack hoạt động. Trên Debian có repository Raspberry Pi như máy của bạn, kiểm tra các gói sau có sẵn. Không cài đè OpenCV/Picamera2 bằng pip trong môi trường chạy thật.

```bash
sudo apt update
sudo apt install -y python3-venv python3-picamera2 python3-opencv opencv-data python3-flask python3-gpiozero python3-lgpio python3-numpy rpicam-apps
rpicam-hello --list-cameras
rpicam-hello -t 5000
```

Nếu không có màn hình, chỉ cần `rpicam-hello --list-cameras`; thử `rpicam-still --nopreview -o camera_test.jpg`. Cần thấy camera IMX708. Đóng các ứng dụng camera khác trước khi chạy.

Chép thư mục dự án đã giải nén vào Pi, ví dụ `~/raspberry_face_labs`:

```bash
cd ~/raspberry_face_labs
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
GPIOZERO_PIN_FACTORY=lgpio python app.py --lab lab1
```

Mở `http://<IP-cua-Pi>:5000` trên máy cùng mạng. Dùng `hostname -I` để xem IP Pi. Nhấn Ctrl+C ở terminal để thoát. Có thể chạy trực tiếp Lab 2:

```bash
GPIOZERO_PIN_FACTORY=lgpio python app.py --lab lab2
```

Không chạy nhiều tiến trình hoặc nhiều worker vì chúng sẽ tranh camera và GPIO. Flask ở đây dành cho lab trong mạng nội bộ, không mở port ra Internet. Servo dùng PWM phần mềm qua lgpio nên có thể rung dưới tải; nếu cần ổn định hơn có thể thay driver bằng PCA9685 trong riêng file lab2_servo.py.

## 4. Mô phỏng không cần Pi

Trên PC có Python (Windows dùng `python` thay `python3`):

```bash
python3 -m venv .venv-mock
source .venv-mock/bin/activate
pip install -r requirements-mock.txt
python app.py --mock
```

Windows PowerShell kích hoạt bằng `.venv-mock\Scripts\Activate.ps1`. Mở http://localhost:5000. Số mặt GIẢ LẬP tuần tự 0–6, mỗi mức 2 giây; khoảng cách Lab 2 giả lập luân phiên 5 cm / 15 cm mỗi 4 giây; không đọc camera và không tạo GPIO. Kiểm tra giao diện, chuyển lab, LED/servo mô phỏng.

## 5. Cấu trúc và luồng

- app.py: Flask, trả HTML, JSON, luồng JPEG; điểm khởi chạy.
- templates/index.html: ảnh camera, số mặt, LED/góc servo, nút chọn lab. JavaScript gửi JSON tới `/api/lab` và đọc `/api/status`.
- camera.py: chỉ mở/đọc/đóng Camera v3 bằng Picamera2, bật autofocus liên tục.
- detector.py: ảnh BGR → xám → cân bằng histogram → detectMultiScale → danh sách khung mặt.
- service.py: một thread camera cho mọi người xem; đếm mặt → gọi hardware.update(count) → vẽ khung → nén JPEG → lưu kết quả mới nhất. Lock bảo vệ chuyển lab và điều khiển GPIO.
- hardware/lab1_leds.py: chỉ chứa quy tắc LED.
- hardware/lab2_servo.py: kết hợp số mặt và khoảng cách để điều khiển servo.
- hardware/ultrasonic.py: đọc HC-SR04 với timeout, trả None khi mất Echo; không chờ vô hạn. Đo xung bằng Python trên Linux có sai số, cần kiểm tra ngưỡng trên Pi thật.
- hardware/__init__.py: registry các lab.
- config.py: chân GPIO, kích thước ảnh, xung servo, GPIO siêu âm, ngưỡng 10 cm và port.

Camera → OpenCV → số mặt → hardware.update(số mặt). Cùng khung ảnh được vẽ và truyền đến `<img>` qua `/video_feed`; trạng thái đi riêng bằng JSON. Không chạy detection cho từng trình duyệt. Khi đóng trình duyệt, lab vẫn tiếp tục trên Pi. Nếu luồng gặp lỗi, LED tắt, servo ngắt PWM và web báo lỗi; sửa nguyên nhân rồi khởi chạy lại.

| Endpoint | Phương thức | Công dụng |
|---|---|---|
| / | GET | Giao diện |
| /video_feed | GET | MJPEG có khung mặt |
| /api/status | GET | JSON số mặt, lab, phần cứng, lỗi |
| /api/lab | POST | JSON `{"lab":"lab1"}` hoặc `{"lab":"lab2"}` |

## 6. Thêm lab phần cứng mới

Tạo `hardware/lab3_xxx.py` có class với 4 hàm: `__init__(mock=False)` khởi tạo phần cứng; `update(face_count)` thực hiện quy tắc; `status()` trả dict trạng thái JSON; `close()` đưa thiết bị về trạng thái an toàn và giải phóng GPIO. Chế độ mock không được truy cập phần cứng.

Import class và thêm vào LABS trong hardware/__init__.py. CLI tự nhận lab mới. Thêm nút tương ứng trên HTML và phần hiển thị trạng thái; không cần sửa camera/detector/service. Cập nhật thông báo tên lab hợp lệ trong app.py nếu muốn mô tả lab mới. Tránh dùng chân GPIO đang được thiết bị khác sử dụng.

## 7. Kiểm tra và lỗi thường gặp

```bash
python -m unittest discover -s tests -v
```

Các test dùng mô phỏng, kiểm tra quy tắc 0–6 mặt, khoảng cách dưới/đúng/trên 10 cm, mất dữ liệu cảm biến, đổi lab, JSON sai và phát MJPEG. Chưa thay thế thử nghiệm trên Pi thật. Thử thật: lần lượt đưa 0–5 người vào khung, rồi kiểm tra >5; chuyển sang Lab 2, thử có/không có mặt kết hợp vật cản ở <10, =10 và >10 cm; kiểm tra mất Echo thì servo về 0°; thử hai trình duyệt, sau đó Ctrl+C để xác nhận tắt LED/ngắt PWM.

- Thiếu cascade: `sudo apt install opencv-data`; hoặc đặt file OpenCV `haarcascade_frontalface_default.xml` trong thư mục models cạnh app.py.
- Không import picamera2/cv2: tạo venv với --system-site-packages, không dùng venv cũ bị lỗi.
- Camera busy: đóng rpicam và tiến trình app cũ. Camera không xuất hiện: kiểm tra cáp sau khi tắt nguồn.
- GPIO Permission denied: kiểm tra nhóm gpio bằng `groups`; nếu nhóm tồn tại, `sudo usermod -aG gpio "$USER"`, rồi đăng xuất/đăng nhập lại.
- Pi reset lúc servo quay: kiểm tra nguồn servo riêng và GND chung.
- Code có null bytes / Structure needs cleaning: thay thẻ nhớ lỗi trước khi cài dự án.

Tài liệu kỹ thuật: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf và https://www.raspberrypi.com/documentation/accessories/camera.html
