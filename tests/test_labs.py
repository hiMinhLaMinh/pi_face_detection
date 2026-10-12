import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app import run
from config import LED_PINS
from hardware import LedLab


class LedTests(unittest.TestCase):
    def test_led_count_and_reset(self):
        lab = LedLab(mock=True)
        for count in range(len(LED_PINS) + 2):
            lab.update(count)
            expected = min(count, len(LED_PINS))
            self.assertEqual(lab.status()["leds"],
                             [i < expected for i in range(len(LED_PINS))])
        lab.update(0)
        self.assertFalse(any(lab.status()["leds"]))

    def test_gpio_outputs_and_shutdown(self):
        pins = [Mock() for _ in LED_PINS]
        with patch.dict(sys.modules, {"gpiozero": SimpleNamespace(LED=Mock(side_effect=pins))}):
            lab = LedLab()
        lab.update(3)
        self.assertEqual([pin.value for pin in pins],
                         [i < 3 for i in range(len(LED_PINS))])
        lab.close()
        for pin in pins:
            pin.off.assert_called_once()
            pin.close.assert_called_once()

    def test_camera_counts_reach_leds_and_failure_cleans_up(self):
        camera = Mock()
        camera.read.side_effect = ["frame1", "frame2", RuntimeError("camera disconnected")]
        detector = Mock()
        detector.detect.side_effect = [[(0, 0, 40, 40)] * 3, []]
        lab = LedLab(mock=True)
        with (
            patch.dict(sys.modules, {
                "camera": SimpleNamespace(PiCamera=Mock(return_value=camera)),
                "detector": SimpleNamespace(FaceDetector=Mock(return_value=detector)),
            }),
            patch("app.LedLab", return_value=lab),
            patch.object(lab, "update", wraps=lab.update) as update,
            patch.object(lab, "close", wraps=lab.close) as close,
            patch("app.time.sleep"),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            with self.assertRaisesRegex(RuntimeError, "camera disconnected"):
                run(device="/dev/video2")
            self.assertEqual([call.args[0] for call in update.call_args_list], [3, 0])
            self.assertIn("Khuôn mặt: 3 | LED sáng: 3/", output.getvalue())
            self.assertIn("Khuôn mặt: 0 | LED sáng: 0/", output.getvalue())
            close.assert_called_once()
        camera.close.assert_called_once()
        self.assertFalse(any(lab.status()["leds"]))

    def test_ctrl_c_cleans_up_mock_leds(self):
        lab = LedLab(mock=True)
        with (
            patch("app.LedLab", return_value=lab),
            patch.object(lab, "close", wraps=lab.close) as close,
            patch("app.time.sleep", side_effect=KeyboardInterrupt),
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            with self.assertRaises(KeyboardInterrupt):
                run(mock=True)
            close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
