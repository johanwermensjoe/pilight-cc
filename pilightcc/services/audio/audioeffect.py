""" Audio Effect service module. """

# Service
from services.service import BaseService
from services.service import ServiceLauncher
from threading import Lock, Condition

# Application
from pilightcc.services.audio.audioanalyzer import AudioAnalyser, \
    AudioAnalyserError
from pilightcc.hyperion.hypjson import HyperionJson
from pilightcc.hyperion.hypproto import HyperionError
from pilightcc.settings.settings import Setting


class AudioEffectService(BaseService):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    __ERROR_DELAY = 5
    __AUDIO_ANALYSER_TIMEOUT = 1
    __IMAGE_DURATION = 500

    def __init__(self, port):
        """ Constructor
        """
        super(AudioEffectService, self).__init__(port, True)
        self._update_state(AudioEffectService.StateValue.OK)
        self.__cond = Condition()

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

    def __update_audio_data(self, data):
        with self.__cond:
            self.__data = data
            self.__cond.notify()

    def _run_service(self):
        try:
            # Check that an hyperion connection is available.
            if not self.__hyperion_connector.is_connected():
                self.__hyperion_connector.connect()
                self._update_state(AudioEffectService.StateValue.OK)

            # Capture audio.
            if not self.__audio_analyser.is_running():
                self.__audio_analyser.start()

            with self.__cond:
                if self.__cond.wait(
                        AudioEffectService.__AUDIO_ANALYSER_TIMEOUT):
                    # Only update if not timed out.
                    data = self.__data
                else:
                    # AudioAnalyser is not sending updates.
                    raise AudioAnalyserError("AudioAnalyser error")

            # Calculate send_effect frame.
            self.calculate_effect(data)

            # Send message.
            # TODO
        except (HyperionError, AudioAnalyserError) as err:
            self._update_state(AudioEffectService.StateValue.ERROR, err.msg)
            self._safe_delay(AudioEffectService.__ERROR_DELAY)

    @staticmethod
    def calculate_effect(data):
        pass


if __name__ == '__main__':
    ServiceLauncher.parse_args_and_execute("AudioEffect", AudioEffectService)
