""" Service Manager module. """

# Processes
from subprocess import Popen
from os.path import abspath

# Services
from pilightcc.services.capture import capture
from pilightcc.services.audio import audioeffect
from pilightcc.services.service import ServiceConnector

# Settings
from pilightcc.settings.settings import SettingsManager


class ServiceId(object):
    CAPTURE = 'capture'
    AUDIO_EFFECT = 'audioeffect'


class ServiceManager(object):
    """ Service Manager class.
    Maintains and controls all services and settings.
    """

    __SERVICE_PATH = {
        ServiceId.CAPTURE: abspath(capture.__file__).rstrip('c'),
        ServiceId.AUDIO_EFFECT: abspath(audioeffect.__file__).rstrip('c')
    }

    def __init__(self):
        """ Constructor """
        # Init the settings.
        self.settings_manager = SettingsManager()
        self.__service_connectors = {}

    def __create_service(self, service_id):
        # Start the service.
        connector = ServiceConnector(True)
        self.__service_connectors[service_id] = connector
        # self.__spawn_daemon("python", ServiceManager.__SERVICE_PATH[service_id],
        #                     "--port", str(connector.get_port()))
        Popen(["python", ServiceManager.__SERVICE_PATH[service_id], "--port",
               str(connector.get_port())])

        # Await initial state update to ensure that service has been started.
        connector.wait_for_update()  # TODO Detect error using timeout

    def start(self):
        """ Start services. """
        # Create services.
        self.__create_service(ServiceId.CAPTURE)
        self.__create_service(ServiceId.AUDIO_EFFECT)

        # Update settings.
        self.update_settings()

        # Enable services.
        #self.get_service(ServiceId.CAPTURE).enable(True)
        self.get_service(ServiceId.AUDIO_EFFECT).enable(True)

    def update_settings(self):
        """ Updates all services with the latest settings. """
        print("Manager: Sending settings")
        settings = self.settings_manager.get_settings()
        for service_connector in self.__service_connectors.itervalues():
            service_connector.update_settings(settings)

    def shutdown(self):
        """ Shutdown services and save settings. """
        print "Manager: Shutting down services"
        # Shutdown services.
        for service_connector in self.__service_connectors.itervalues():
            service_connector.shutdown()
        # Save all settings to storage.
        self.settings_manager.save_settings()

    def get_service(self, service_id):
        """ Getter for service connectors.
        - service_id    : the service id
        """
        return self.__service_connectors[service_id]

    # @staticmethod
    # def __spawn_daemon(path_to_executable, *args):
    #     import os
    #     """Spawn a completely detached subprocess (i.e., a daemon).
    #
    #     E.g. for mark:
    #     spawnDaemon("../bin/producenotify.py", "producenotify.py", "xx")
    #     """
    #     # fork the first time (to make a non-session-leader child process)
    #     try:
    #         pid = os.fork()
    #     except OSError, e:
    #         raise RuntimeError(
    #             "1st fork failed: %s [%d]" % (e.strerror, e.errno))
    #     if pid != 0:
    #         # parent (calling) process is all done
    #         return
    #
    #     # detach from controlling terminal (to make child a session-leader)
    #     os.setsid()
    #     try:
    #         pid = os.fork()
    #     except OSError, e:
    #         raise RuntimeError(
    #             "2nd fork failed: %s [%d]" % (e.strerror, e.errno))
    #         raise Exception, "%s [%d]" % (e.strerror, e.errno)
    #     if pid != 0:
    #         # child process is all done
    #         os._exit(0)
    #
    #     # grandchild process now non-session-leader, detached from parent
    #     # grandchild process must now close all open files
    #     try:
    #         maxfd = os.sysconf("SC_OPEN_MAX")
    #     except (AttributeError, ValueError):
    #         maxfd = 1024
    #
    #     for fd in range(maxfd):
    #         try:
    #             os.close(fd)
    #         except OSError:  # ERROR, fd wasn't open to begin with (ignored)
    #             pass
    #
    #     # redirect stdin, stdout and stderr to /dev/null
    #     os.open(os.devnull, os.O_RDWR)  # standard input (0)
    #     os.dup2(0, 1)
    #     os.dup2(0, 2)
    #
    #     # and finally let's execute the executable for the daemon!
    #     try:
    #         os.execv(path_to_executable, args)
    #     except Exception as e:
    #         # oops, we're cut off from the world, let's just give up
    #         os._exit(255)
