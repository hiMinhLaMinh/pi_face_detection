"""Lưu khung ảnh đã áp dụng filter cạnh app.py."""
from datetime import datetime
from pathlib import Path
from uuid import uuid4

PHOTOS_DIR = Path(__file__).resolve().parent / "photos"


def save_photo(frame, filter_name, directory=PHOTOS_DIR):
    import cv2
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = directory / f"{timestamp}_{filter_name}_{uuid4().hex[:8]}.jpg"
    if not cv2.imwrite(str(path), frame):
        raise OSError(f"Không lưu được ảnh: {path}")
    return path
