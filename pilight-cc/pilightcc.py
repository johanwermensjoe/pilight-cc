import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from services.manager import ServiceManager


def hello(button):
    pass


service_manager = ServiceManager()

builder = Gtk.Builder()
builder.add_from_file("../res/pilightcc.glade")
handlers = {
    "onDeleteWindow": Gtk.main_quit,
    "onButtonPressed": hello
}
builder.connect_signals(handlers)
window = builder.get_object("window1")
window.show_all()
Gtk.main()
