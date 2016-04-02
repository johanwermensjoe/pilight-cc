""" Screen capture service module. """

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf

# Service
from services.service import BaseService
from services.service import DelayTimer

# Application
from hyperion.hyperion import HyperionConnector
from hyperion.hyperion import HyperionError
from settings.settings import Setting


class CaptureService(BaseService):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    __IMAGE_DURATION = 500

    __ERROR_DELAY = 5

    def __init__(self):
        """ Constructor
        """
        self.state.set_value(CaptureService.StateValue.OK)
        self.__hyperion_connector = None
        self.__delay_timer = DelayTimer(1 / self.__frame_rate)

    def __update_pixel_buffer(self):
        self.__data = self.scale_pixel_buffer(
            self.get_pixel_buffer(),
            self.__scale_width,
            self.__scale_height)

    def _run_service(self):
        self.__delay_timer.start()

        # Check that an hyperion connection is available.
        if not self.__hyperion_connector:
            try:
                self.__hyperion_connector = HyperionConnector(self.__ip_address,
                                                              self.__port)
                self._update_state(CaptureService.StateValue.OK)
            except HyperionError as err:
                self._update_state(CaptureService.StateValue.ERROR, err.msg)
                self._safe_delay(CaptureService.__ERROR_DELAY)
                return

        try:
            # Capture and pass to hyperion service.
            self.__update_pixel_buffer()
            self.__hyperion_connector.send_image(self.__scale_width,
                                                 self.__scale_height,
                                                 self.__data.get_pixels(),
                                                 self.__priority,
                                                 CaptureService.__IMAGE_DURATION)
        except HyperionError as err:
            del self.__hyperion_connector
            self._update_state(CaptureService.StateValue.ERROR, err.msg)

        # Wait until next run.
        self.__delay_timer.delay()

    def _load_settings(self, settings):
        self.__ip_address = settings[Setting.HYPERION_IP_ADDRESS]
        self.__port = settings[Setting.HYPERION_PORT]
        self.__scale_width = settings[Setting.CAPTURE_SCALE_WIDTH]
        self.__scale_height = settings[Setting.CAPTURE_SCALE_HEIGHT]
        self.__priority = settings[Setting.CAPTURE_PRIORITY]
        self.__frame_rate = settings[Setting.CAPTURE_FRAME_RATE]

    @staticmethod
    def get_pixel_buffer():
        win = Gdk.get_default_root_window()
        h = win.get_height()
        w = win.get_width()
        return Gdk.pixbuf_get_from_window(win, 0, 0, w, h)

    # @staticmethod
    # def get_pixel_buffer():
    #     from PyQt5.QtWidgets import QApplication
    #     app = QApplication([])
    #     return QApplication.screens()[0].grabWindow(
    #         QApplication.desktop().winId()).toImage()

    @staticmethod
    def scale_pixel_buffer(pixel_buffer, width, height):
        return pixel_buffer.scale_simple(width, height,
                                         GdkPixbuf.InterpType.BILINEAR)


if __name__ == '__main__':
    capture_service = CaptureService()
    capture_service.run()
