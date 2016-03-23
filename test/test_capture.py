import unittest

import services.capture as capture
from timeit import timeit


class CaptureTestCase(unittest.TestCase):
    def test_capture_format(self):
        pb = capture.get_pixel_buffer()
        print "\nCapture format:"
        print "Size: {0}x{1}".format(pb.get_width(), pb.get_height())
        print "Channels: {0}".format(str(pb.get_n_channels()))
        self.assertEqual(pb.get_n_channels(), 3)
        print "Byte length: {0}".format(str(pb.get_byte_length()))
        self.assertEqual(pb.get_byte_length(),
                         pb.get_n_channels() * pb.get_height() * pb.get_width())
        print "Sample bits: {0}".format(str(pb.get_bits_per_sample()))
        self.assertEqual(pb.get_bits_per_sample(), 8)

    def test_capture_scaling(self):
        scale = 2
        pb = capture.get_pixel_buffer()
        pb2 = capture.scale_pixel_buffer(pb, pb.get_width() / scale,
                                         pb.get_height() / scale)
        self.assertEqual(pb.get_byte_length(),
                         pb2.get_byte_length() * scale**2)

    def test_capture_rate(self):
        def capture_and_scale():
            pb = capture.get_pixel_buffer()
            capture.scale_pixel_buffer(pb, pb.get_width() / 2,
                                       pb.get_height() / 2)

        fps = 100 / timeit(capture_and_scale, number=100)
        print "\nCapture rate:"
        print "Avg fps: {0}".format(str(fps))
        self.assertGreaterEqual(fps, 30)


if __name__ == '__main__':
    unittest.main()
