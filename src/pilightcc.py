from gi.repository import Gtk

from hyperion.hyperion import Hyperion

_HYP_SERVER_IP_ADDRESS = "10.0.0.68"
_HYP_SERVER_PORT = 19445

def hello(button):
    hyp = Hyperion(_HYP_SERVER_IP_ADDRESS, _HYP_SERVER_PORT)
    print("Sending")
    hyp.sendColor(0x00FF0000, 50, 1000)

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
