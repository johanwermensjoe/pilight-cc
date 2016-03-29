""" Service Manager module. """

from services.capture.capture import CaptureService
from services.hyperion.hyperion import HyperionService
from services.audioeffect.audioeffect import AudioEffectService

from settings.settings import SettingsManager


class ServiceManager(object):
    """ Service Manager class.
    Maintains and controls all services.
    """

    def __init__(self):
        """ Constructor """
        # Init the settings.
        self.settings_manager = SettingsManager()

        # Setup all services.
        self.__services = []

        settings_connector = self.settings_manager.create_connector()
        self.hyperion_service = HyperionService(settings_connector)
        self.hyperion_service.enable(True)
        self.__services.append(self.hyperion_service)

        settings_connector = self.settings_manager.create_connector()
        self.capture_service = CaptureService(self.hyperion_service,
                                              settings_connector)
        self.capture_service.enable(True)
        self.__services.append(self.capture_service)

        # settings_connector = self.settings_manager.create_connector()
        # self.audio_effect_service = AudioEffectService(self.hyperion_service,
        #                                                settings_connector)
        # self.__services.append(self.audio_effect_service)

    def start(self):
        """ Start services. """
        self.hyperion_service.start()
        self.capture_service.start()
        # self.audio_effect_service.start()

    def shutdown(self):
        """ Shutdown services and save settings. """
        # Shutdown services.
        for service in self.__services:
            service.shutdown()
            service.join()

        # Save all settings to storage.
        self.settings_manager.save_settings()