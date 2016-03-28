""" Service module. """

# Multiprocessing
from multiprocessing import Process
from multiprocessing import Value
from multiprocessing import Event

import time


class BaseService(Process):
    """ Base Service class.
    Should have subclass with implementations for
    _run_service, _on_shutdown and _load_settings.
    """

    def __init__(self, settings_connector=None, enable_flag=None):
        """ Constructor
        - hyperion_service      : hyperion service to send messages
        - settings_connector    : connector for settings updates
        """
        super(BaseService, self).__init__()
        self.state = State()
        self.__shutdown_signal = Event()
        self.__enable_flag = enable_flag
        self.__settings_connector = settings_connector
        self._load_settings(settings_connector)

    def run(self):
        """ Service execution method.
        Should not be overridden.
        """
        while True:
            if self.__shutdown_signal.is_set():
                self._on_shutdown()
                break

            if self.__enable_flag:
                # Check if the capture service is enabled or block until it is.
                self.__settings_connector.get_flag(self.__enable_flag).wait()

            if self.__settings_connector:
                # Reload settings if needed.
                if self.__settings_connector.signal.is_set():
                    # Clear alert before to avoid missing updates.
                    self.__settings_connector.signal.clear()
                    self._load_settings(self.__settings_connector)

            self._run_service()

    def _run_service(self):
        """ To be implemented by subclass.
        Called periodically by the process, with settings updated
        and enable flag checked before every run.
        """
        raise NotImplementedError("Please Implement this method")

    def _on_shutdown(self):
        """ To be implemented by subclass.
        Called if the service is signaled to shutdown.
        """
        raise NotImplementedError("Please Implement this method")

    def _load_settings(self, settings_connector):
        """ To be implemented by subclass.
        Called periodically by the process if some setting has been changed.
        Responsible for caching any setting needed during execution.
        - settings_connector    : connector to the settings to load
        """
        raise NotImplementedError("Please Implement this method")

    def shutdown(self):
        """ Signal the service to shutdown.
        Can be called from any process.
        """
        self.__shutdown_signal.set()


class State(object):
    """ State class.
    A process/thread safe state.
    """

    def __init__(self):
        """ Constructor """
        self.__value = Value("i")

    def set_value(self, new_value):
        """ Setter for state code. """
        self.__value.value = new_value

    def get_value(self):
        """ Getter for state code. """
        return self.__value.value


class DelayTimer(object):
    """ DelayTimer class.
    Provides a real time delay that depends on the time of the last delay.
    """

    def __init__(self, delay):
        """ Constructor
        - delay : delay between calls in seconds
        """
        self.__delay = delay
        self.__last_time = 0

    def start(self):
        """ Set the start of the execution of the caller process.
        """
        self.__last_time = time.clock()

    def delay(self):
        """ Delay the calling process for the time left of the delay.
        """
        delta = self.__delay - (time.clock() - self.__last_time)
        if delta > 0:
            time.sleep(delta)
