from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from filters import FILTERS, apply_filter
from hardware.shutter import ShutterButton
from photos import PHOTOS_DIR, save_photo

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None


class CaptureTests(unittest.TestCase):
    def test_press_is_consumed_once_and_button_closed(self):
        button = Mock()
        factory = Mock(return_value=button)
        with patch.dict(sys.modules, {"gpiozero": SimpleNamespace(Button=factory)}):
            shutter = ShutterButton(25)
        factory.assert_called_once_with(25, pull_up=True, bounce_time=0.2)
        self.assertFalse(shutter.consume_press())
        button.when_pressed()
        self.assertTrue(shutter.consume_press())
        self.assertFalse(shutter.consume_press())
        shutter.close()
        button.close.assert_called_once()

    def test_photo_paths_unique_and_write_failure_reported(self):
        self.assertEqual(PHOTOS_DIR, Path(__file__).resolve().parents[1] / "photos")
        fake_cv2 = Mock()
        fake_cv2.imwrite.return_value = True
        frame = object()
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {"cv2": fake_cv2}):
            path1 = save_photo(frame, "blur", directory)
            path2 = save_photo(frame, "blur", directory)
            self.assertNotEqual(path1, path2)
            self.assertEqual(path1.parent, Path(directory))
            self.assertEqual(path1.suffix, ".jpg")
            self.assertIs(fake_cv2.imwrite.call_args.args[1], frame)
            fake_cv2.imwrite.return_value = False
            with self.assertRaises(OSError):
                save_photo(frame, "blur", directory)


@unittest.skipIf(cv2 is None, "Cần OpenCV và NumPy để kiểm tra ảnh thực tế")
class ImageTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.random.default_rng(42).integers(0, 256, (100, 120, 3), dtype=np.uint8)
        self.boxes = [(20, 20, 60, 60)]

    def test_filters_only_change_face_regions_and_keep_original(self):
        original = self.frame.copy()
        outside = np.ones(self.frame.shape[:2], dtype=bool)
        outside[20:80, 20:80] = False
        for name in FILTERS:
            with self.subTest(filter=name):
                result = apply_filter(self.frame, self.boxes, name)
                np.testing.assert_array_equal(self.frame, original)
                np.testing.assert_array_equal(result[outside], original[outside])
                self.assertEqual(result.shape, original.shape)
                if name == "none":
                    np.testing.assert_array_equal(result, original)
                else:
                    self.assertFalse(np.array_equal(result[20:80, 20:80], original[20:80, 20:80]))
                if name == "grayscale":
                    np.testing.assert_array_equal(result[20:80, 20:80, 0], result[20:80, 20:80, 1])

    def test_empty_and_out_of_bounds_boxes(self):
        for name in FILTERS:
            np.testing.assert_array_equal(apply_filter(self.frame, [], name), self.frame)
            result = apply_filter(self.frame, [(-10, -10, 30, 30), (200, 200, 10, 10), (0, 0, 0, 0)], name)
            self.assertEqual(result.shape, self.frame.shape)
        with self.assertRaises(ValueError):
            apply_filter(self.frame, self.boxes, "invalid")

    def test_saved_jpeg_has_filtered_pixels(self):
        filtered = apply_filter(self.frame, self.boxes, "grayscale")
        with tempfile.TemporaryDirectory() as directory:
            path = save_photo(filtered, "grayscale", directory)
            loaded = cv2.imread(str(path))
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.shape, filtered.shape)
            # JPEG có sai số; kiểm tra vùng trong mặt, xa biên chuyển màu.
            region = loaded[30:70, 30:70].astype(float)
            self.assertLess(np.mean(np.abs(region[:, :, 0] - region[:, :, 1])), 3)


if __name__ == "__main__":
    unittest.main()
