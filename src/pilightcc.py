from gi.repository import Gtk

import message_pb2


def hello(button):
    print("Hello World!\n")
    msg = message_pb2.ColorRequest()
    msg.priority = 50
    msg.RgbColor = 0x00FF0000
    msg.duration = 1000
    print(": " + msg.SerializeToString())

builder = Gtk.Builder()
builder.add_from_file("res/pilightcc.glade")
handlers = {
    "onDeleteWindow": Gtk.main_quit,
    "onButtonPressed": hello
}
builder.connect_signals(handlers)
window = builder.get_object("window1")
window.show_all()
Gtk.main()
