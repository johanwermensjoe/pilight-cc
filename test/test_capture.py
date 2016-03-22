import unittest

import capture.capture as capture
from timeit import timeit


class MyTestCase(unittest.TestCase):
    def test_capture_format(self):
        pb = capture.get_pixel_buffer()
        print "\nCapture format:"
        print "Channels: " + str(pb.get_n_channels())
        self.assertEqual(pb.get_n_channels(), 3)
        print "Byte length: " + str(pb.get_byte_length())
        self.assertEqual(pb.get_byte_length(),
                         pb.get_n_channels() * pb.get_height() * pb.get_width())
        print "Sample bits: " + str(pb.get_bits_per_sample())
        self.assertEqual(pb.get_bits_per_sample(), 8)

    def test_capture_scaling(self):
        pb = capture.get_pixel_buffer()
        pb2 = capture.scale_pixel_buffer(pb, pb.get_width() / 2,
                                         pb.get_height() / 2)
        self.assertEqual(pb.get_byte_length(), pb2.get_byte_length() * 4)

    def test_capture_rate(self):
        def test():
            pb = capture.get_pixel_buffer()
            capture.scale_pixel_buffer(pb, pb.get_width() / 2,
                                       pb.get_height() / 2)

        fps = 100 / timeit(test, number=100)
        print "\nAvg fps: " + str(fps)
        self.assertGreaterEqual(fps, 30)


if __name__ == '__main__':
    unittest.main()
