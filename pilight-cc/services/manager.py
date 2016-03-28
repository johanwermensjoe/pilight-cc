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
        # Setup all services.
        self.settings_manager = SettingsManager()

        settings_connector = self.settings_manager.create_connector()
        self.hyperion_service = HyperionService(settings_connector)
        self.hyperion_service.start()

        settings_connector = self.settings_manager.create_connector()
        self.capture_service = CaptureService(self.hyperion_service,
                                              settings_connector)
        self.capture_service.start()

        settings_connector = self.settings_manager.create_connector()
        self.audio_effect_service = AudioEffectService(self.hyperion_service,
                                                       settings_connector)
        self.audio_effect_service.start()