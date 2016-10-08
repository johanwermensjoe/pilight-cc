from pilightcc.ui.window import MainWindow
from pilightcc.services.manager import ServiceManager


def exit_app():
    service_manager.shutdown()
    pass


if __name__ == '__main__':
    service_manager = ServiceManager()
    service_manager.start()
    window = MainWindow(exit_app)
    window.show()
