""" Service Manager module. """

from subprocess import call

from services.service import ServiceConnector

from settings.settings import SettingsManager

from os.path import abspath, dirname, join


class ServiceManager(object):
    """ Service Manager class.
    Maintains and controls all services.
    """

    __CAPTURE_SERVICE = join(abspath(dirname(__file__)), "services", "capture",
                             "capture.py")
    __AUDIO_EFFECT_SERVICE = join(abspath(dirname(__file__)), "services",
                                  "audioeffect", "audioeffect.py")

    __MIN_PORT = 40000
    __MAX_PORT = 50000

    def __init__(self):
        """ Constructor """
        # Init the settings.
        self.settings_manager = SettingsManager()

        # Setup all services.
        self.__services = []

        self.capture_service = self.__create_service(
            ServiceManager.__CAPTURE_SERVICE)
        self.capture_service.enable(True)

        # self.audio_effect_service = AudioEffectService(self.hyperion_service,
        #                                                settings_connector)

    def __create_service(self, service_path, port):
        # Start the service.
        connector = ServiceConnector(ServiceManager.__MIN_PORT,
                                     ServiceManager.__MAX_PORT)
        self.__services.append(connector)
        call(["python", service_path, connector.get_port()])
        return ServiceConnector(connector)

    def start(self):
        """ Start services. """
        for service in self.__services:
            service.start()

    def shutdown(self):
        """ Shutdown services and save settings. """
        # Shutdown services.
        for service in self.__services:
            service.shutdown()

        # Save all settings to storage.
        self.settings_manager.save_settings()
