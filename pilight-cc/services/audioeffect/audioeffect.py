""" Audio Effect service module. """

from services.service import BaseService
from services.service import DelayTimer

from settings.settings import Flag
from settings.settings import Setting


class AudioEffectService(BaseService):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    _IMAGE_DURATION = 500

    def __init__(self, hyperion_service, settings_connector):
        """ Constructor
        - hyperion_service      : hyperion service to send messages
        - settings_connector    : connector for settings updates
        """
        super(AudioEffectService, self).__init__(settings_connector,
                                                 Flag.AUDIO_EFFECT_ENABLE)
        self.state.set_value(AudioEffectService.StateValue.OK)
        self.__hyperion_service = hyperion_service
        self.__delay_timer = DelayTimer(1 / self.__frame_rate)

    def _load_settings(self, settings_connector):
        # Load the settings.
        self.__priority = settings_connector.get_setting(
            Setting.AUDIO_EFFECT_PRIORITY)
        self.__frame_rate = settings_connector.get_setting(
            Setting.AUDIO_EFFECT_FRAME_RATE)

    def _on_shutdown(self):
        # TODO
        pass

    def _run_service(self):
        self.__delay_timer.start()

        # Capture audio.
        # TODO
        self.read_audio()

        # Calculate effect frame.
        # TODO
        self.calculate_effect()

        # Send message.
        # TODO

        # Wait until next run.
        self.__delay_timer.delay()

    @staticmethod
    def read_audio():
        pass

    @staticmethod
    def calculate_effect():
        pass
