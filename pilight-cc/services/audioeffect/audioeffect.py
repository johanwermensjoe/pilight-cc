""" Audio Effect service module. """

from hyperion.hyperion import HyperionConnector
from hyperion.hyperion import HyperionError
from services.service import BaseService
from services.service import DelayTimer
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

    __ERROR_DELAY = 5

    def __init__(self):
        """ Constructor
        """
        self._state.set_value(AudioEffectService.StateValue.OK)
        self.__hyperion_connector = None
        self.__delay_timer = DelayTimer(1 / self.__frame_rate)

    def _run_service(self):
        self.__delay_timer.start()

        # Check that an hyperion connection is available.
        if not self.__hyperion_connector:
            try:
                self.__hyperion_connector = HyperionConnector(self.__ip_address,
                                                              self.__port)
                self._update_state(AudioEffectService.StateValue.OK)
            except HyperionError as err:
                self._update_state(AudioEffectService.StateValue.ERROR, err.msg)
                self._safe_delay(AudioEffectService.__ERROR_DELAY)
                return

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

    def _load_settings(self, settings_connector):
        # Load the settings.
        self.__priority = settings_connector.get_setting(
            Setting.AUDIO_EFFECT_PRIORITY)
        self.__frame_rate = settings_connector.get_setting(
            Setting.AUDIO_EFFECT_FRAME_RATE)

    @staticmethod
    def read_audio():
        pass

    @staticmethod
    def calculate_effect():
        pass


if __name__ == '__main__':
    audio_effect_service = AudioEffectService()
    audio_effect_service.run()
