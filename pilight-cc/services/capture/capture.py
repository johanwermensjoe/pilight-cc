""" Screen capture service module. """

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from gi.repository import GdkPixbuf

# Multiprocessing
from multiprocessing import Process
from threading import Timer

from services.manager import State


class CaptureService(Process):
    """ Capture Service class.
    """

    class State(object):
        """ State class.
        """
        OK = 1
        ERROR = 2

    def __init__(self, hyperion_service, settings_listener):
        """ Constructor
        - input_queue       : queue for waiting messages
        - settings_listener : listener for settings updates
        - state             : state object for the service
        """
        self.__hyperion_service = hyperion_service
        self.__state = State()
        self.__settings_listener = settings_listener

    def run(self):
        # Capture and pass to hyperion service.
        # TODO

        # Read settings for enable status.
        # TODO

        # Schedule the next run.
        Timer(1 / self.__frame_rate, self.__run).start()

    def __send_frame(self):
        self.__update_pixel_buffer()
        self.__hyperion_service.send_image(64, 64, self.__data.get_pixels(),
                                           900, 500)

    def __update_pixel_buffer(self):
        pixel_buffer = CaptureService.scale_pixel_buffer(
            CaptureService.get_pixel_buffer(),
            self.__scale_width,
            self.__scale_height)
        self.__data = pixel_buffer

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
