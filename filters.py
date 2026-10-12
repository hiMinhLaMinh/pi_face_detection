"""Filter chỉ tác động lên vùng mặt; detection luôn dùng ảnh gốc."""

FILTERS = ("none", "glasses", "grayscale", "blur", "pixelate")


def apply_filter(frame, boxes, name):
    if name not in FILTERS:
        raise ValueError(f"Filter không hợp lệ: {name}")
    result = frame.copy()
    if name == "none":
        return result

    import cv2
    height, width = frame.shape[:2]
    for x, y, w, h in boxes:
        x, y, w, h = int(x), int(y), int(w), int(h)
        left, top = max(0, x), max(0, y)
        right, bottom = min(width, x + w), min(height, y + h)
        if right <= left or bottom <= top:
            continue
        # Luôn lấy vùng ảnh gốc để các mặt chồng nhau không bị lọc nhiều lần.
        face = frame[top:bottom, left:right]
        fh, fw = face.shape[:2]
        if name == "grayscale":
            gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
            filtered = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif name == "blur":
            filtered = cv2.GaussianBlur(face, (0, 0), sigmaX=max(3, min(fw, fh) / 8))
        elif name == "pixelate":
            small = cv2.resize(face, (max(1, fw // 12), max(1, fh // 12)),
                               interpolation=cv2.INTER_AREA)
            filtered = cv2.resize(small, (fw, fh), interpolation=cv2.INTER_NEAREST)
        else:  # Kính được đặt tương đối theo khung mặt, không dùng landmark mắt.
            filtered = face.copy()
            cy = int(fh * 0.38)
            axes = (max(1, int(fw * 0.18)), max(1, int(fh * 0.10)))
            for cx in (int(fw * 0.28), int(fw * 0.72)):
                cv2.ellipse(filtered, (cx, cy), axes, 0, 0, 360, (20, 20, 20), -1)
            cv2.line(filtered, (int(fw * 0.45), cy), (int(fw * 0.55), cy),
                     (20, 20, 20), max(1, fw // 30))
        result[top:bottom, left:right] = filtered
    return result
