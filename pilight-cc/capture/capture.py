""" Screen capture module. """

import gi

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GdkPixbuf


def get_pixel_buffer():
    win = Gdk.get_default_root_window()
    h = win.get_height()
    w = win.get_width()
    pb = Gdk.pixbuf_get_from_window(win, 0, 0, w, h)
    return pb
    # o_gdk_pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Ccolorspace.RGB, False, 8, 1, 1)
    # o_gdk_pixbuf.get_from_drawable(Gdk.get_default_root_window(), Gdk.colormap_get_system(), i_x, i_y, 0, 0, 1, 1)
    # return tuple(o_gdk_pixbuf.get_pixels_array().tolist()[0][0])


def scale_pixel_buffer(pixel_buffer, width, height):
    return pixel_buffer.scale_simple(width, height,
                                        GdkPixbuf.InterpType.BILINEAR)
