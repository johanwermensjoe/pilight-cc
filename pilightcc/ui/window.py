from gi import require_version

require_version('Gtk', '3.0')
from gi.repository import Gtk


class MainWindow(object):

    def __init__(self, on_exit_app):
        self.__on_exit_app = on_exit_app
        builder = Gtk.Builder()
        builder.add_from_file("../res/pilightcc.glade")
        handlers = {}
        builder.connect_signals(handlers)
        self.__window = builder.get_object("main_win")
        self.__window.connect("delete-event", self.__on_exit)

    def __on_exit(self, action, value):
        self.__on_exit_app()
        Gtk.main_quit()

    def show(self):
        self.__window.show_all()
        Gtk.main()
