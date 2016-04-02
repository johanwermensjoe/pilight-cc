""" Service module. """

# Multiprocessing
from multiprocessing import Event

from time import sleep, clock

from zmq import Context
import zmq


class BaseService(object):
    """ Base Service class.
    Should have subclass with implementations for
    _run_service, _on_shutdown and _load_settings.
    Implementation for _init_service is optional.
    """

    # The delay interval for shutdown monitoring, safe delays.
    __SAFE_DELAY_INCREMENT = 0.5

    def __init__(self, port, enable_settings=False):
        """ Constructor
        - port      : the 0mq communication port
        """
        self.state = State()
        self.__require_settings = enable_settings

        # Setup the 0mq channel.
        context = Context()
        self.__socket = context.socket(zmq.PAIR)
        self.__socket.bind("tcp://*:%s" % port)

    def run(self):
        """ Service execution method.
        Should not be overridden.
        """
        self._init_service()
        while True:
            if self.__shutdown:
                self._on_shutdown()
                break
            if self.__require_settings:
                # Reload settings if needed.
                if self.__settings_connector.signal.is_set():
                    # Clear alert before to avoid missing updates.
                    self._load_settings(self.__settings_connector)

            self._run_service()

    def _init_service(self):
        """ Can be implemented by subclass.
        Called initially by the process before the first call to _run_service.
        """
        pass

    def _run_service(self):
        """ To be implemented by subclass.
        Called periodically by the process, with settings updated
        and enable flag checked before every run.
        """
        raise NotImplementedError("Please implement this method")

    def _on_shutdown(self):
        """ To be implemented by subclass.
        Called if the service is signaled to shutdown.
        """
        raise NotImplementedError("Please implement this method")

    def _load_settings(self, settings):
        """ To be implemented by subclass.
        Called periodically by the process if some setting has been changed.
        Responsible for caching any setting needed during execution.
        - settings    : the updated settings
        """
        raise NotImplementedError("Please implement this method")

    def _safe_delay(self, delay):
        while delay > BaseService.__SAFE_DELAY_INCREMENT:
            sleep(BaseService.__SAFE_DELAY_INCREMENT)
            delay -= BaseService.__SAFE_DELAY_INCREMENT
            if self.__shutdown_signal.is_set():
                return
        sleep(delay)


class ServiceConnector(object):

    __HOST_ADDRESS = "127.0.0.1"
    __MAX_TRIES = 100

    def __init__(self, min_port, max_port):
        # Setup the 0mq channel to the started service.
        context = Context()
        self.__socket = context.socket(zmq.PAIR)
        self.__port = self.__socket.bind_to_random_port(
            ServiceConnector.__HOST_ADDRESS, min_port, max_port,
            ServiceConnector.__MAX_TRIES)

    def get_port(self):
        """ Return the bound port. """
        return self.__port

    def shutdown(self):
        """ Signal the service to shutdown.
        Can be called from any process.
        """
        self.connect()
        self.__shutdown_signal.set()
        self.enable(True)

    def enable(self, enable):
        """ Signal the service to be enabled/disabled.
        Can be called from any process.
        - enable    : true to enable / false to disable
        """
        if enable:
            self.__enable_signal.set()
        else:
            self.__enable_signal.clear()


class State(object):
    def __init__(self):
        """ Constructor """
        self.__state = {'value': None, 'msg': None}

    def set_value(self, new_value):
        """ Setter for state code. """
        self.__state['value'] = new_value

    def set_message(self, message):
        """ Setter for state code. """
        self.__state['msg'] = message

    def get_state(self):
        """ Getter for state. """
        return self.__state


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
        self.__last_time = clock()

    def delay(self):
        """ Delay the calling process for the time left of the delay.
        """
        delta = self.__delay - (clock() - self.__last_time)
        if delta > 0:
            sleep(delta)
        # Update the time of the last call.
        self.__last_time = clock()
