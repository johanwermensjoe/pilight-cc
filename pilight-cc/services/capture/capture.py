""" Screen capture service module. """

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf

# Multiprocessing
from threading import Timer
from services.baseservice import BaseService

from settings.settings import Flag
from settings.settings import Setting


class CaptureService(BaseService):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    _IMAGE_DURATION = 500

    def __init__(self, hyperion_service, settings_connector):
        """ Constructor
        - hyperion_service      : hyperion service to send messages
        - settings_connector    : connector for settings updates
        """
        super(CaptureService, self).__init__(settings_connector,
                                             Flag.CAPTURE_ENABLE)
        self.__state.set_value(CaptureService.StateValue.OK)
        self.__hyperion_service = hyperion_service

    def __load_settings(self):
        # Load the updated settings.
        self.__scale_width = self.__settings_connector.get_setting(
            Setting.CAPTURE_SCALE_WIDTH)
        self.__scale_height = self.__settings_connector.get_setting(
            Setting.CAPTURE_SCALE_HEIGHT)
        self.__priority = self.__settings_connector.get_setting(
            Setting.CAPTURE_PRIORITY)
        self.__frame_rate = self.__settings_connector.get_setting(
            Setting.CAPTURE_FRAME_RATE)

    def __update_pixel_buffer(self):
        self.__data = self.scale_pixel_buffer(
            self.get_pixel_buffer(),
            self.__scale_width,
            self.__scale_height)

    def __run_service(self):
        # Schedule the next run.
        # TODO
        Timer(1 / self.__frame_rate, self.__run).start()

        # Capture and pass to hyperion service.
        self.__update_pixel_buffer()
        self.__hyperion_service.send_image(self.__scale_width,
                                           self.__scale_height,
                                           self.__data.get_pixels(),
                                           self.__priority,
                                           CaptureService._IMAGE_DURATION)

    @staticmethod
    def get_pixel_buffer():
        win = Gdk.get_default_root_window()
        h = win.get_height()
        w = win.get_width()
        return Gdk.pixbuf_get_from_window(win, 0, 0, w, h)
        # o_gdk_pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Ccolorspace.RGB, False, 8, 1, 1)
        # o_gdk_pixbuf.get_from_drawable(Gdk.get_default_root_window(), Gdk.colormap_get_system(), i_x, i_y, 0, 0, 1, 1)
        # return tuple(o_gdk_pixbuf.get_pixels_array().tolist()[0][0])

    @staticmethod
    def scale_pixel_buffer(pixel_buffer, width, height):
        return pixel_buffer.scale_simple(width, height,
                                         GdkPixbuf.InterpType.BILINEAR)
