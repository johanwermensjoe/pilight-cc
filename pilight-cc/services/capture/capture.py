""" Screen capture service module. """

# PyGI - Screen capture (Gtk).
from gi import require_version

require_version('Gdk', '3.0')

from gi.repository import Gdk
from gi.repository import GdkPixbuf

# Service
from services.service import ServiceLauncher
from services.service import BaseService
from services.service import DelayTimer

# Application
from hyperion.hypproto import HyperionProto
from hyperion.hypproto import HyperionError
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

    def __init__(self, port):
        """ Constructor
        """
        super(CaptureService, self).__init__(port, True)
        self._update_state(CaptureService.StateValue.OK)
        self.__delay_timer = DelayTimer()
        self.__disconnect()

        # Register settings.
        hyperion_unit = self._register_setting_unit(self.__disconnect())
        hyperion_unit.add('_ip_address', Setting.HYPERION_IP_ADDRESS)
        hyperion_unit.add('_port', Setting.HYPERION_PORT)

        capture_unit = self._register_setting_unit(self.__update_timer)
        capture_unit.add('_frame_rate', Setting.CAPTURE_FRAME_RATE)

        std_unit = self._register_setting_unit()
        std_unit.add('_scale_width', Setting.CAPTURE_SCALE_WIDTH)
        std_unit.add('_scale_height', Setting.CAPTURE_SCALE_HEIGHT)
        std_unit.add('_priority', Setting.CAPTURE_PRIORITY)

    def __disconnect(self):
        self.__hyperion_connector = None

    def __update_timer(self):
        self.__delay_timer.set_delay(1.0 / self._frame_rate)

    def __update_pixel_buffer(self):
        self.__data = self.scale_pixel_buffer(
            self.get_pixel_buffer(),
            self._scale_width,
            self._scale_height)

    def _run_service(self):
        self.__delay_timer.start()

        # Check that an hyperion connection is available.
        if self.__hyperion_connector is None:
            try:
                self.__hyperion_connector = HyperionProto(
                    self._ip_address, self._port)
                self._update_state(CaptureService.StateValue.OK)
            except HyperionError as err:
                self._update_state(CaptureService.StateValue.ERROR, err.msg)
                self._safe_delay(CaptureService.__ERROR_DELAY)
                return

        try:
            # Capture and pass to hyperion service.
            self.__update_pixel_buffer()
            self.__hyperion_connector.send_image(self._scale_width,
                                                 self._scale_height,
                                                 self.__data.get_pixels(),
                                                 self._priority,
                                                 CaptureService.__IMAGE_DURATION)
        except HyperionError as err:
            del self.__hyperion_connector
            self._update_state(CaptureService.StateValue.ERROR, err.msg)

        # Wait until next run.
        self.__delay_timer.delay()

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
    ServiceLauncher.parse_args_and_execute("Capture", CaptureService)
