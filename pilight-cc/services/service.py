""" Service module. """

# Multiprocessing
from threading import Thread
from threading import Lock

# Delay
from time import sleep, clock

# Communication
from zmq import PAIR
from zmq import NOBLOCK
from zmq import ZMQError
from zmq import Context

# Initialization
from argparse import ArgumentParser


class BaseService(object):
    """ BaseService class.
    Subclasses should implement _run_service.
    Implementations for _on_shutdown and _handle_message are optional.
    State codes 0-5 are reserved for BaseService.
    """

    class __SettingUnit(object):
        def __init__(self, owner, callback=None):
            self.__owner = owner
            self.__callback = callback
            self.__id_key_pairs = []

        def add(self, id, key):
            self.__id_key_pairs.append((id, key))
            setattr(self.__owner, id, None)

        def has_changes(self, settings):
            for (prop, key) in self.__id_key_pairs:
                if getattr(self.__owner, prop) != settings[key]:
                    return True
            return False

        def update(self, settings):
            for (prop, key) in self.__id_key_pairs:
                setattr(self.__owner, prop, settings[key])
            if self.__callback:
                self.__callback()

    # The delay interval for shutdown monitoring, safe delays.
    __SAFE_DELAY_INCREMENT = 0.5

    __HOST_ADDRESS = "tcp://127.0.0.1"

    def __init__(self, port, enable_settings=False):
        """ Constructor
        - port      : the 0mq communication port
        """
        # Setup the 0mq channel.
        self.__context = Context()
        self.__socket = self.__context.socket(PAIR)
        print "Service started on: tcp://127.0.0.1:{0}".format(port)
        self.__socket.connect("{0}:{1}".format(BaseService.__HOST_ADDRESS,
                                               port))

        # Initialize state.
        self.__require_settings = enable_settings
        self.__enable = False
        self.__shutdown = False
        self._state = None
        self._update_state()

        # Setup setting handling.
        self.__setting_units = []

    def __load_settings(self, settings):
        for setting_unit in self.__setting_units:
            if setting_unit.has_changes(settings):
                setting_unit.update(settings)

    def __del__(self):
        self.__socket.close()
        self.__context.destroy()

    def __handle_std_message(self, msg):
        """ Handle standard message types.
        - msg   : the message (None is allowed)
        """
        if msg:
            print "Message received: {0} - {1}".format(msg.type, msg.data)
            if msg.type == ServiceMessage.Type.ENABLE:
                self.__enable = msg.data
                self._update_state()
            elif msg.type == ServiceMessage.Type.KILL:
                self.__shutdown = True
                self._update_state()
                self._on_shutdown()
            elif msg.type == ServiceMessage.Type.SETTINGS:
                self.__load_settings(msg.data)
            else:
                self._handle_message(msg)

    def run(self):
        """ Service execution method.
        Should not be overridden.
        """
        # Wait for initial settings if required.
        if self.__require_settings:
            while not self.__shutdown:
                print "Waiting for initial settings"
                start_msg = ServiceMessage.wait_for_message(self.__socket)
                self.__handle_std_message(start_msg)
                if start_msg.type == ServiceMessage.Type.SETTINGS:
                    break

        # Main loop, exit on leave.
        while not self.__shutdown:
            # Check for any incoming messages, wait if disabled.
            if self.__enable:
                # Run service.
                self._run_service()
                msg = ServiceMessage.check_for_message(self.__socket)
            else:
                msg = ServiceMessage.wait_for_message(self.__socket)

            self.__handle_std_message(msg)

    def _on_shutdown(self):
        """ To be implemented by subclass.
        Called if the service is signaled to shutdown.
        """
        pass

    def _handle_message(self, msg):
        """ Can be implemented by subclass.
        Called when a message of unknown type is received.
        - msg   : the received message
        """
        pass

    def _run_service(self):
        """ To be implemented by subclass.
        Called periodically by the process, with settings updated
        and enable flag checked before every run.
        """
        raise NotImplementedError("Please implement this method")

    def _register_setting_unit(self, callback=None):
        setting_unit = BaseService.__SettingUnit(self, callback)
        self.__setting_units.append(setting_unit)
        return setting_unit

    def _send_message(self, msg):
        msg.send(self.__socket)

    def _update_state(self, value=None, msg=None):
        # Use previous value if none was given.
        if not value:
            try:
                value = self._state.get_value()
            except AttributeError:
                pass
        # Only update if new state is different.
        new_state = ServiceState(self.__enable, self.__shutdown, value, msg)
        print "State updated: {0}".format(new_state)
        if self._state != new_state:
            self._state = new_state
            self._send_message(ServiceMessage(ServiceMessage.Type.STATE,
                                              self._state.to_data()))

    def _safe_delay(self, delay):
        while delay > BaseService.__SAFE_DELAY_INCREMENT:
            # Delay for ony a small increment.
            sleep(BaseService.__SAFE_DELAY_INCREMENT)
            delay -= BaseService.__SAFE_DELAY_INCREMENT

            # Check and handle any messages.
            msg = ServiceMessage.check_for_message(self.__socket)
            self.__handle_std_message(msg)
            if self.__shutdown:
                return
        # Sleep for any remaining delay.
        sleep(delay)


class ServiceLauncher(object):
    """ Service launcher class.
    """

    @staticmethod
    def parse_args_and_execute(name, service):
        """ Parses arguments. """
        parser = ArgumentParser(description="The " + name + " service.")
        parser.add_argument('--port', type=int, required=True,
                            help="communication port")
        args = parser.parse_args()

        print "Service started"
        service(args.port).run()
        print "Service terminated"


class ServiceConnector(object):
    """ Service connector class.
    """

    __HOST_ADDRESS = "tcp://127.0.0.1"

    def __init__(self, spawn_monitor=False):
        # Setup the 0mq channel to the started service.
        self.__context = Context()
        self.__socket = self.__context.socket(PAIR)
        self.__port = self.__socket.bind_to_random_port(
            ServiceConnector.__HOST_ADDRESS)

        # Setup state access.
        self.__state_lock = Lock()
        self.__state = ServiceState(False, False)

        # Spawn a monitor thread.
        if spawn_monitor:
            thread = Thread(target=self.__monitor_state)
            thread.daemon = True
            thread.start()

    def __del__(self):
        self.__socket.close()
        self.__context.destroy()

    def __monitor_state(self):
        while True:
            msg = ServiceMessage.wait_for_message(self.__socket,
                                                  ServiceMessage.Type.STATE)
            self.__update_state(msg.data)

    def __update_state(self, data):
        try:
            self.__state_lock.acquire()
            self.__state = ServiceState.from_data(data)
            print "State received: {0}".format(self.__state)
        finally:
            self.__state_lock.release()

    def get_state(self):
        try:
            self.__state_lock.acquire()
            return self.__state
        finally:
            self.__state_lock.release()

    def get_port(self):
        """ Return the bound port. """
        return self.__port

    def shutdown(self):
        """ Signal the service to shutdown.
        Can be called from any process.
        """
        ServiceMessage(ServiceMessage.Type.KILL).send(self.__socket)

    def enable(self, enable):
        """ Signal the service to be enabled/disabled.
        Can be called from any process.
        - enable    : true to enable / false to disable
        """
        ServiceMessage(ServiceMessage.Type.ENABLE, enable).send(self.__socket)

    def update_settings(self, settings):
        """ Signal the service to update its settings.
        Can be called from any process.
        - settings  : the updated settings dictionary
        """
        ServiceMessage(ServiceMessage.Type.SETTINGS, settings).send(
            self.__socket)


class ServiceMessage(object):
    """ Service message class.
    """

    class Type(object):
        ENABLE = 0
        KILL = 1
        SETTINGS = 2
        STATE = 3

    def __init__(self, _type, data=None):
        self.type = _type
        self.data = data

    def __to_msg(self):
        return {'type': self.type, 'data': self.data}

    def send(self, zmq_socket):
        zmq_socket.send_json(self.__to_msg())

    @classmethod
    def from_message(cls, msg):
        return cls(msg['type'], msg['data'])

    @classmethod
    def wait_for_message(cls, zmq_socket, _type=None):
        while True:
            service_message = cls.from_message(zmq_socket.recv_json())
            # Return message if the _type isn't requested or matches.
            if not _type or service_message.type == _type:
                return service_message

    @classmethod
    def check_for_message(cls, zmq_socket):
        try:
            return cls.from_message(zmq_socket.recv_json(NOBLOCK))
        except ZMQError:
            return None


class ServiceState(object):
    """ Service state class.
    """

    def __init__(self, enable, shutdown, value=None, msg=None):
        """ Constructor """
        self.__enable = enable
        self.__shutdown = shutdown
        self.__value = value
        self.__msg = msg

    def __eq__(self, other):
        if isinstance(other, ServiceState):
            return self.__enable == other.__enable and \
                   self.__shutdown == other.__shutdown and \
                   self.__value == other.__value and \
                   self.__msg == other.__msg
        return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        state_str = " State: Not set"
        if self.__value:
            state_str = " State: value={0}".format(self.__value)
            if self.__msg:
                state_str += " msg={0}".format(self.__msg)
        return "Service [enable={0} shutdown={1}{2}]".format(self.__enable,
                                                             self.__shutdown,
                                                             state_str)

    def is_enabled(self):
        """ Getter for service enable state. """
        return self.__enable

    def is_shutting_down(self):
        """ Getter for service shutdown state. """
        return self.__shutdown

    def get_value(self):
        """ Getter for service state value. """
        return self.__value

    def get_message(self):
        """ Getter for service state message. """
        return self.__msg

    def to_data(self):
        return {
            'service': {'enable': self.__enable, 'shutdown': self.__shutdown},
            'value': self.__value, 'msg': self.__msg}

    @classmethod
    def from_data(cls, data):
        return cls(data['service']['enable'], data['service']['shutdown'],
                   data['value'], data['msg'])


class DelayTimer(object):
    """ DelayTimer class.
    Provides a real time delay that depends on the time of the last delay.
    """

    def __init__(self, delay=0):
        """ Constructor
        - delay : delay between calls in seconds
        """
        self.__delay = delay
        self.__last_time = 0

    def set_delay(self, delay):
        """ Setter for the delay. """
        self.__delay = delay

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
