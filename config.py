# Số GPIO theo BCM, không phải số chân vật lý.
LED_PINS = [17, 27, 22, 23, 24]
SERVO_PIN = 18
SERVO_MIN_PULSE = 0.0005
SERVO_MAX_PULSE = 0.0025
WIDTH, HEIGHT = 640, 480
PORT = 8000

# Dùng GPIO riêng, không trùng 5 LED của Lab 1.
ULTRASONIC_TRIGGER_PIN = 5  # Chân vật lý 29
ULTRASONIC_ECHO_PIN = 6    # Chân vật lý 31, Echo PHẢI qua chia áp
FACE_DISTANCE_THRESHOLD_CM = 10.0
