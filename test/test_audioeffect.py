import unittest
from timeit import timeit

from services.capture.capture import CaptureService


class AudioEffectTestCase(unittest.TestCase):
    def test_audio_capture(self):
        pass

    def test_effect_calculation(self):
        pass

    def test_capture_rate(self):
        def capture_and_calculate():
            pass

        fps = 100 / timeit(capture_and_calculate, number=100)
        print "\nCapture rate:"
        print "Avg fps: {0}".format(str(fps))
        self.assertGreaterEqual(fps, 60)


if __name__ == '__main__':
    unittest.main()
