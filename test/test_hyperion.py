import unittest

import capture.capture as capture
from hyperion.hyperion import Hyperion
from timeit import timeit


class HyperionTestCase(unittest.TestCase):
    def test_connection(self):
        ip = "10.0.0.68"
        port = 19445
        try:
            print "\nHyperion connection:"
            Hyperion(ip, port)
            print "Successfully connected to hyperion server: " + ip + ":" + str(
                port)
        except Exception:
            self.fail(
                "Connection could not be established to: " + ip + ":" + str(
                    port))


if __name__ == '__main__':
    unittest.main()
