""" Screen capture service module. """

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf

# Multiprocessing
from multiprocessing import Process
from threading import Timer

from services.manager import State

from settings.settings import Flag
from settings.settings import Setting


class CaptureService(Process):
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
        self.__state = State()
        self.__state.set_value(CaptureService.StateValue.OK)
        self.__settings_connector = settings_connector
        self.__hyperion_service = hyperion_service
        self.__load_settings()

    def __update_pixel_buffer(self):
        self.__data = self.scale_pixel_buffer(
            self.get_pixel_buffer(),
            self.__scale_width,
            self.__scale_height)

    def __load_settings(self):
        # Clear alert before to avoid missing updates.
        self.__settings_connector.signal.clear()

        # Load the updated settings.
        self.__scale_width = self.__settings_connector.get_setting(
            Setting.CAPTURE_SCALE_WIDTH)
        self.__scale_height = self.__settings_connector.get_setting(
            Setting.CAPTURE_SCALE_HEIGHT)
        self.__priority = self.__settings_connector.get_setting(
            Setting.CAPTURE_PRIORITY)
        self.__frame_rate = self.__settings_connector.get_setting(
            Setting.CAPTURE_FRAME_RATE)

    def run(self):
        # Check if the capture service is enabled or block until it is.
        self.__settings_connector.get_flag(Flag.CAPTURE_ENABLE).wait()

        # Schedule the next run.
        Timer(1 / self.__frame_rate, self.__run).start()

        # Reload settings if needed.
        if self.__settings_connector.signal.is_set():
            self.__load_settings()

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
