""" Audio Effect service module. """

# Service
from services.service import ServiceLauncher
from services.service import BaseService
from services.service import DelayTimer

# Application
from hyperion.hyperion import HyperionConnector
from hyperion.hyperion import HyperionError
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

    def __init__(self, port):
        """ Constructor
        """
        super(AudioEffectService, self).__init__(port, True)
        self._update_state(AudioEffectService.StateValue.OK)
        self.__delay_timer = DelayTimer()
        self.__disconnect()

        # Register settings.
        hyperion_unit = self._register_setting_unit(self.__disconnect())
        hyperion_unit.add('_ip_address', Setting.HYPERION_IP_ADDRESS)
        hyperion_unit.add('_port', Setting.HYPERION_PORT)

        audio_effect_unit = self._register_setting_unit(self.__update_timer)
        audio_effect_unit.add('_frame_rate', Setting.AUDIO_EFFECT_FRAME_RATE)

        std_unit = self._register_setting_unit()
        std_unit.add('_priority', Setting.AUDIO_EFFECT_PRIORITY)

    def __disconnect(self):
        self.__hyperion_connector = None

    def __update_timer(self):
        self.__delay_timer.set_delay(1 / self.__frame_rate)

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

    @staticmethod
    def read_audio():
        pass

    @staticmethod
    def calculate_effect():
        pass


if __name__ == '__main__':
    ServiceLauncher.parse_args_and_execute("AudioEffect", AudioEffectService)
