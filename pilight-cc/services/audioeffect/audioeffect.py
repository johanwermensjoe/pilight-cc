""" Audio Effect service module. """

# Service
from hyperion.hypjson import HyperionJson
from services.audioeffect.audioanalyzer import AudioAnalyser
from services.service import ServiceLauncher
from services.service import BaseService
from services.service import DelayTimer

# Application
from hyperion.hypproto import HyperionProto
from hyperion.hypproto import HyperionError
from settings.settings import Setting


class AudioEffectService(BaseService):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    __IMAGE_DURATION = 500

    __ERROR_DELAY = 5

    def __init__(self, port):
        """ Constructor
        """
        super(AudioEffectService, self).__init__(port, True)
        self._update_state(AudioEffectService.StateValue.OK)

        # Register settings.
        hyperion_unit = self._register_setting_unit(
            self.__update_hyperion_connector())
        hyperion_unit.add('_ip_address', Setting.HYPERION_IP_ADDRESS)
        hyperion_unit.add('_port', Setting.HYPERION_PORT)

        audio_effect_unit = self._register_setting_unit(
            self.__update_audio_analyser())
        audio_effect_unit.add('_frame_rate', Setting.AUDIO_EFFECT_FRAME_RATE)
        audio_effect_unit.add('_led_count', Setting.LED_COUNT)
        audio_effect_unit.add('_led_start_corner', Setting.LED_START_CORNER)
        audio_effect_unit.add('_led_direction', Setting.LED_DIRECTION)

        std_unit = self._register_setting_unit()
        std_unit.add('_priority', Setting.AUDIO_EFFECT_PRIORITY)

    def _setup(self):
        self.__update_hyperion_connector()
        self.__update_audio_analyser()

    def _enable(self, enable):
        if enable:
            self.__hyperion_connector.connect()
            self.__audio_analyser.start()
        else:
            self.__hyperion_connector.disconnect()
            self.__audio_analyser.stop()

    def __update_hyperion_connector(self):
        if self.__hyperion_connector is not None:
            self.__hyperion_connector.disconnect()
        self.__hyperion_connector = HyperionJson(
            self._ip_address, self._port, self._priority)

    def __update_audio_analyser(self):
        if self.__audio_analyser is not None:
            self.__audio_analyser.stop()
        # TODO Args
        self.__audio_analyser = AudioAnalyser()

    def _run_service(self):
        try:
            # Check that an hyperion connection is available.
            if not self.__hyperion_connector.is_connected():
                self.__hyperion_connector.connect()
                self._update_state(AudioEffectService.StateValue.OK)

            # Capture __audio.
            # TODO
            self.read_audio()

            # Calculate send_effect frame.
            # TODO
            self.calculate_effect()

            # Send message.
            # TODO
        except HyperionError as err:
            self._update_state(AudioEffectService.StateValue.ERROR, err.msg)
            self._safe_delay(AudioEffectService.__ERROR_DELAY)

    @staticmethod
    def read_audio():
        pass

    @staticmethod
    def calculate_effect():
        pass


if __name__ == '__main__':
    ServiceLauncher.parse_args_and_execute("AudioEffect", AudioEffectService)
