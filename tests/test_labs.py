import time
import unittest
from app import create_app
from service import FaceService

class LabTests(unittest.TestCase):
    def setUp(self):
        self.service = FaceService(mock=True)
        self.client = create_app(self.service).test_client()

    def tearDown(self):
        self.service.close()

    def test_rules_and_switch(self):
        for count in range(7):
            self.service.hardware.update(count)
            self.assertEqual(sum(self.service.hardware.status()['leds']), min(count, 5))
        self.service.select_lab('lab2')
        self.service.hardware.mock_distance_provider = lambda: 5.0
        for count in range(7):
            self.service.hardware.update(count)
            self.assertEqual(self.service.hardware.status()['servo_angle'], 90 if count else 0)
        self.service.select_lab('lab1')
        self.assertEqual(sum(self.service.hardware.status()['leds']), 0)

    def test_distance_and_face_gate(self):
        self.service.select_lab('lab2')
        lab = self.service.hardware
        for distance in (None, float('nan'), float('inf'), -1, 0, 5, 9.99, 10, 10.01, 15, 401):
            for faces in (0, 1, 5):
                with self.subTest(distance=distance, faces=faces):
                    lab.mock_distance_provider = lambda: distance
                    lab.update(faces)
                    expected = 90 if faces > 0 and distance in (5, 9.99) else 0
                    self.assertEqual(lab.status()['servo_angle'], expected)
        # Sau khi đã mở, mất dữ liệu khoảng cách phải về 0°.
        lab.mock_distance_provider = lambda: 5
        lab.update(1)
        self.assertEqual(lab.angle, 90)
        lab.mock_distance_provider = lambda: None
        lab.update(1)
        self.assertEqual(lab.angle, 0)
        self.assertFalse(lab.status()['distance_valid'])

    def test_ultrasonic_timeout(self):
        from hardware.ultrasonic import Ultrasonic
        class Pin:
            value = False
            def on(self): self.value = True
            def off(self): self.value = False
        sensor = Ultrasonic.__new__(Ultrasonic)
        sensor.trigger = Pin()
        sensor.echo = Pin()
        sensor.last_trigger = 0
        start = time.monotonic()
        self.assertIsNone(sensor.read_cm())  # Không nhận Echo.
        self.assertLess(time.monotonic() - start, 0.5)
        self.assertFalse(sensor.trigger.value)
        sensor.echo.value = True  # Echo giữ HIGH.
        self.assertIsNone(sensor.read_cm())

    def test_api_validation(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        for body in ({'lab':'x'}, {'lab':[]}, [], None):
            self.assertEqual(self.client.post('/api/lab', json=body).status_code, 400)
        response = self.client.post('/api/lab', json={'lab':'lab2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['hardware']['servo_angle'], 0)
        self.assertEqual(self.client.get('/video_feed').status_code, 503)

    def test_mock_stream(self):
        self.service.start()
        deadline = time.monotonic() + 5
        while self.service.snapshot()['updated'] is None and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(self.service.snapshot()['running'], self.service.snapshot())
        stream = self.client.get('/video_feed', buffered=False)
        self.assertEqual(stream.status_code, 200)
        self.assertIn(b'Content-Type: image/jpeg', next(iter(stream.response)))
        stream.close()
        self.assertEqual(self.client.post('/api/lab', json={'lab':'lab2'}).status_code, 200)

if __name__ == '__main__':
    unittest.main()
