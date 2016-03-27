import unittest

from services.hyperion.hyperion import HyperionService

_HYP_SERVER_IP_ADDRESS = "10.0.0.68"
_HYP_SERVER_PORT = 19445
_HYP_DURATION = 500
_HYP_PRIORITY = 1000


class HyperionTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            print "\nHyperion connection:"
            cls.__hyp = HyperionService(_HYP_SERVER_IP_ADDRESS, _HYP_SERVER_PORT)
            print "Successfully connected to hyperion server: {0}:{1}".format(
                _HYP_SERVER_IP_ADDRESS, str(_HYP_SERVER_PORT))
        except Exception as err:
            raise unittest.SkipTest(
                "Connection could not be established to: {0}:{1} - {2}".format(
                    _HYP_SERVER_IP_ADDRESS, str(_HYP_SERVER_PORT), err.message))

    def test_color_request(self):
        print "\nHyperion color request:"
        try:
            self.__hyp.send_color(0x00FF0000, _HYP_PRIORITY, _HYP_DURATION)
            print "Successfully sent color request."
        except Exception as err:
            self.fail("Color request failed: {0}".format(err.message))

    def test_image_request(self):
        print "\nHyperion image request:"
        try:
            self.__hyp.send_image(1, 1, bytearray([0x00, 0xFF, 0x00]), _HYP_PRIORITY,
                                  _HYP_DURATION)
            print "Successfully sent image request."
        except Exception as err:
            self.fail("Color image failed: {0}".format(err.message))


if __name__ == '__main__':
    unittest.main()
