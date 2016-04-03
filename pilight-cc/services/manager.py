""" Service Manager module. """

from subprocess import call

from services.service import ServiceConnector

from settings.settings import SettingsManager

from os.path import abspath, dirname, join


class ServiceId(object):
    CAPTURE = 'capture'
    AUDIO_EFFECT = 'audioeffect'


class ServiceManager(object):
    """ Service Manager class.
    Maintains and controls all services and settings.
    """

    __SERVICE_PATH = {
        ServiceId.CAPTURE: join(abspath(dirname(__file__)), "services",
                                "capture", "capture.py"),
        ServiceId.AUDIO_EFFECT: join(abspath(dirname(__file__)), "services",
                                     "audioeffect", "audioeffect.py")
    }

    __MIN_PORT = 40000
    __MAX_PORT = 50000

    def __init__(self):
        """ Constructor """
        # Init the settings.
        self.settings_manager = SettingsManager()
        self.__services = {}

    def __create_service(self, service_id):
        # Start the service.
        connector = ServiceConnector(ServiceManager.__MIN_PORT,
                                     ServiceManager.__MAX_PORT, True)
        self.__services[service_id] = connector
        call(["python", ServiceManager.__SERVICE_PATH[service_id],
              connector.get_port()])
        return ServiceConnector(connector)

    def start(self):
        """ Start services. """
        self.__create_service(ServiceId.CAPTURE)
        self.__create_service(ServiceId.AUDIO_EFFECT)

        # Update settings.
        self.get_service(ServiceId.CAPTURE).update_settings(self.settings_manager.)

        # Enable initially.
        self.get_service(ServiceId.CAPTURE).enable(True)

    def shutdown(self):
        """ Shutdown services and save settings. """
        # Shutdown services.
        for service in self.__services:
            service.shutdown()

        # Save all settings to storage.
        self.settings_manager.save_settings()

    def get_service(self, service_id):
        """ Getter for service connectors.
        - id    : the service id
        """
        return self.__services[service_id]
