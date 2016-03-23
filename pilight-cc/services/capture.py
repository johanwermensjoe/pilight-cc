""" Screen capture service module. """

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf

from multiprocessing import Lock


class CaptureService:
    def __init__(self, framerate, scale_width, scale_height):
        self.__framerate = framerate
        self.__scale_height = scale_height
        self.__scale_width = scale_width
        self.__data = None
        self.__lock = Lock()

    def get_pixel_buffer(self):
        try:
            self.__lock.acquire()
            return self.__data
            self.__lock.release()
        finally:
            pass

    def execute(self):
        while True:
            # TODO use timer
            self.__update_pixel_buffer()

    def __update_pixel_buffer(self):
        pixel_buffer = scale_pixel_buffer(get_pixel_buffer(),
                                          self.__scale_width,
                                          self.__scale_height)
        self.__lock.acquire()
        self.__data = pixel_buffer
        self.__lock.release()


def get_pixel_buffer():
    win = Gdk.get_default_root_window()
    h = win.get_height()
    w = win.get_width()
    return Gdk.pixbuf_get_from_window(win, 0, 0, w, h)
    # o_gdk_pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Ccolorspace.RGB, False, 8, 1, 1)
    # o_gdk_pixbuf.get_from_drawable(Gdk.get_default_root_window(), Gdk.colormap_get_system(), i_x, i_y, 0, 0, 1, 1)
    # return tuple(o_gdk_pixbuf.get_pixels_array().tolist()[0][0])


def scale_pixel_buffer(pixel_buffer, width, height):
    return pixel_buffer.scale_simple(width, height,
                                     GdkPixbuf.InterpType.BILINEAR)
