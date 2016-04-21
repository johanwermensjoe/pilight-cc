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
        Popen(["python", ServiceManager.__SERVICE_PATH[service_id], "--port",
               str(connector.get_port())])

    def start(self):
        """ Start services. """
        # Create services.
        self.__create_service(ServiceId.CAPTURE)
        # self.__create_service(ServiceId.AUDIO_EFFECT)

        # Update settings.
        self.get_service(ServiceId.CAPTURE).update_settings(
            self.settings_manager.get_settings())
        # self.get_service(ServiceId.AUDIO_EFFECT).update_settings(
        #     self.settings_manager.get_settings())

        # Enable services.
        self.get_service(ServiceId.CAPTURE).enable(True)
        # self.get_service(ServiceId.AUDIO_EFFECT).enable(True)

    def shutdown(self):
        """ Shutdown services and save settings. """
        print "Shutting down services"
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
