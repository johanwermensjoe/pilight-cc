""" Service Manager module. """

# Processes
from subprocess import Popen
from os import path

# Services
from pilightcc.services.capture import capture
from pilightcc.services.audio import audio
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
        ServiceId.CAPTURE: path.abspath(capture.__file__).rstrip('c'),
        ServiceId.AUDIO_EFFECT: path.abspath(audio.__file__).rstrip(
            'c')
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
        # self.get_service(ServiceId.CAPTURE).enable(True)
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