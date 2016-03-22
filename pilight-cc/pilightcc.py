import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
from timeit import timeit
from hyperion.hyperion import Hyperion

_HYP_SERVER_IP_ADDRESS = "10.0.0.68"
_HYP_SERVER_PORT = 19445
_HYP_SERVER_RECONNECT_TIMEOUT = 30

_HYP_COLOR_PRIORITY = 50

_HYP_CAPTURE_PRIORITY = 100
_HYP_CAPTURE_FRAMERATE = 30
_HYP_CAPTURE_IMAGE_HEIGHT = 64
_HYP_CAPTURE_IMAGE_WIDTH = 64



hyp = Hyperion(_HYP_SERVER_IP_ADDRESS, _HYP_SERVER_PORT)
# hyp.sendImage(pb.get_width(), pb.get_height(), pb.get_pixels(), 50)
# hyp.sendImage(pb.get_width(), pb.get_height(), pb.get_pixels(), 50, 500)
hyp.clearall()

# def hello(button):
#     hyp = Hyperion(_HYP_SERVER_IP_ADDRESS, _HYP_SERVER_PORT)
#     print("Sending")
#     # hyp.sendColor(0x00FF0000, 50, 1000)
#     pb = get_pixel_buffer()
#     hyp.sendImage(pb.get_width(), pb.get_height(), pb.get_pixels(), 50, 1000)
#
# builder = Gtk.Builder()
# builder.add_from_file("../res/pilightcc.glade")
# handlers = {
#     "onDeleteWindow": Gtk.main_quit,
#     "onButtonPressed": hello
# }
# builder.connect_signals(handlers)
# window = builder.get_object("window1")
# window.show_all()
# Gtk.main()
