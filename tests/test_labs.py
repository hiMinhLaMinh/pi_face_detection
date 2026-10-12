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
                "cv2": Mock(),
                "camera": SimpleNamespace(PiCamera=Mock(return_value=camera)),
                "detector": SimpleNamespace(FaceDetector=Mock(return_value=detector)),
            }),
            patch("app.LedLab", return_value=lab),
            patch("app.ShutterButton") as shutter_factory,
            patch("app.apply_filter", return_value="filtered"),
            patch.object(lab, "update", wraps=lab.update) as update,
            patch.object(lab, "close", wraps=lab.close) as close,
            patch("app.time.sleep"),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            shutter_factory.return_value.consume_press.return_value = False
            with self.assertRaisesRegex(RuntimeError, "camera disconnected"):
                run(device="/dev/video2", preview=False)
            self.assertEqual([call.args[0] for call in update.call_args_list], [3, 0])
            self.assertIn("Khuôn mặt: 3 | LED sáng: 3/", output.getvalue())
            self.assertIn("Khuôn mặt: 0 | LED sáng: 0/", output.getvalue())
            close.assert_called_once()
            shutter_factory.return_value.close.assert_called_once()
        camera.close.assert_called_once()
        self.assertFalse(any(lab.status()["leds"]))

    def test_preview_draws_faces_and_cleans_up_on_quit(self):
        for key, visible in ((ord("q"), 1), (ord("Q"), 1), (-1, 0)):
            with self.subTest(key=key, visible=visible):
                camera = Mock()
                camera.read.return_value = "frame"
                detector = Mock()
                detector.detect.return_value = [(10, 20, 40, 50)]
                cv2 = Mock()
                cv2.waitKey.return_value = key
                cv2.getWindowProperty.return_value = visible
                lab = LedLab(mock=True)
                with (
                    patch.dict(sys.modules, {
                        "cv2": cv2,
                        "camera": SimpleNamespace(PiCamera=Mock(return_value=camera)),
                        "detector": SimpleNamespace(FaceDetector=Mock(return_value=detector)),
                    }),
                    patch("app.LedLab", return_value=lab),
                    patch("app.ShutterButton") as shutter_factory,
                    patch("app.apply_filter", return_value=SimpleNamespace(copy=lambda: "frame")),
                    patch.object(lab, "close", wraps=lab.close) as close,
                    patch("sys.stdout", new_callable=io.StringIO),
                ):
                    shutter_factory.return_value.consume_press.return_value = False
                    run()
                    close.assert_called_once()
                cv2.rectangle.assert_called_once_with("frame", (10, 20), (50, 70), (0, 255, 0), 2)
                cv2.imshow.assert_called_once_with("Face Detection - USB Webcam", "frame")
                overlay = cv2.putText.call_args_list[0].args[1]
                self.assertEqual(overlay, f"Faces: 1 | LEDs: 1/{len(LED_PINS)}")
                cv2.destroyAllWindows.assert_called_once()
                camera.close.assert_called_once()
                self.assertFalse(any(lab.status()["leds"]))

    def test_button_saves_filtered_frames_and_preserves_led_counts(self):
        camera = Mock()
        camera.read.side_effect = ["raw1", "raw2", "raw3", RuntimeError("disconnected")]
        detector = Mock()
        detector.detect.side_effect = [[(0, 0, 40, 40)] * n for n in (3, 0, 6)]
        shutter = Mock()
        shutter.consume_press.side_effect = [True, False, True]
        lab = LedLab(mock=True)
        with (
            patch.dict(sys.modules, {
                "cv2": Mock(),
                "camera": SimpleNamespace(PiCamera=Mock(return_value=camera)),
                "detector": SimpleNamespace(FaceDetector=Mock(return_value=detector)),
            }),
            patch("app.LedLab", return_value=lab),
            patch("app.ShutterButton", return_value=shutter) as shutter_factory,
            patch("app.apply_filter", side_effect=["filtered1", "filtered2", "filtered3"]) as filtering,
            patch("app.save_photo", return_value="photos/snapshot.jpg") as save,
            patch.object(lab, "update", wraps=lab.update) as update,
            patch("app.time.sleep"),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            with self.assertRaisesRegex(RuntimeError, "disconnected"):
                run(preview=False, filter_name="pixelate")
            shutter_factory.assert_called_once_with(25)
            self.assertEqual([call.args[0] for call in update.call_args_list], [3, 0, 6])
            self.assertIn("Khuôn mặt: 6 | LED sáng: 5/5", output.getvalue())
            self.assertEqual([call.args for call in save.call_args_list],
                             [("filtered1", "pixelate"), ("filtered3", "pixelate")])
            self.assertEqual([call.args[0] for call in filtering.call_args_list],
                             ["raw1", "raw2", "raw3"])
        camera.close.assert_called_once()
        shutter.close.assert_called_once()
        self.assertFalse(any(lab.status()["leds"]))

    def test_keyboard_capture_and_save_failure_keeps_running(self):
        camera = Mock()
        camera.read.return_value = "raw"
        detector = Mock()
        detector.detect.return_value = []
        cv2 = Mock()
        cv2.waitKey.side_effect = [ord("s"), ord("Q")]
        cv2.getWindowProperty.return_value = 1
        shutter = Mock()
        shutter.consume_press.return_value = False
        lab = LedLab(mock=True)
        filtered = SimpleNamespace(copy=lambda: "display")
        with (
            patch.dict(sys.modules, {
                "cv2": cv2,
                "camera": SimpleNamespace(PiCamera=Mock(return_value=camera)),
                "detector": SimpleNamespace(FaceDetector=Mock(return_value=detector)),
            }),
            patch("app.LedLab", return_value=lab),
            patch("app.ShutterButton", return_value=shutter),
            patch("app.apply_filter", return_value=filtered),
            patch("app.save_photo", side_effect=OSError("disk full")) as save,
            patch("app.time.sleep"),
            patch("sys.stdout", new_callable=io.StringIO),
            self.assertLogs(level="ERROR") as logs,
        ):
            run()
            save.assert_called_once_with(filtered, "glasses")
            self.assertEqual(camera.read.call_count, 2)
            self.assertIn("disk full", "\n".join(logs.output))
        cv2.destroyAllWindows.assert_called_once()
        camera.close.assert_called_once()
        shutter.close.assert_called_once()

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
