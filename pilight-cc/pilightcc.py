import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from services.manager import ServiceManager


def hello(button):
    pass


def exit_app(a, b):
    service_manager.shutdown()
    Gtk.main_quit()


if __name__ == '__main__':
    service_manager = ServiceManager()
    service_manager.start()

    builder = Gtk.Builder()
    builder.add_from_file("../res/pilightcc.glade")
    handlers = {
        "onDeleteWindow": exit_app,
        "onButtonPressed": hello
    }
    builder.connect_signals(handlers)
    window = builder.get_object("window1")
    window.show_all()
    Gtk.main()
