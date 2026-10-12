# Thêm lab mới vào registry này; camera và Flask không cần sửa.
from .lab1_leds import LedLab
from .lab2_servo import ServoLab
LABS = {"lab1": LedLab, "lab2": ServoLab}
