""" Base Service module. """

# Multiprocessing
from multiprocessing import Process

from services.manager import State


class BaseService(Process):
    """ Capture Service class.
    """

    def __init__(self, settings_connector=None, enable_flag=None):
        """ Constructor
        - hyperion_service      : hyperion service to send messages
        - settings_connector    : connector for settings updates
        """
        self.state = State()
        self.__settings_connector = settings_connector
        self.__enable_flag = enable_flag
        self.__load_settings()

    def __load_settings(self):
        """
        """
        raise NotImplementedError("Please Implement this method")

    def __run_service(self):
        """ To be implemented by subclass.
        Called periodically by the process, with settings
        and enable flag checked before every run.
        """
        raise NotImplementedError("Please Implement this method")

    def run(self):
        while True:
            if self.__enable_flag:
                # Check if the capture service is enabled or block until it is.
                self.__settings_connector.get_flag(self.__enable_flag).wait()

            if self.__settings_connector:
                # Reload settings if needed.
                if self.__settings_connector.signal.is_set():
                    # Clear alert before to avoid missing updates.
                    self.__settings_connector.signal.clear()
                    self.__load_settings()

            self.__run_service()
