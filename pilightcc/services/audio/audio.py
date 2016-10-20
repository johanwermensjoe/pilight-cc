""" Audio service module. """

# Service
from pilightcc.services.service import BaseService
from pilightcc.services.service import ServiceLauncher
from threading import Lock, Event

# Application
from pilightcc.services.audio.audioanalyzer import AudioAnalyserError
from pilightcc.services.audio.audioeffect import LevelEffect
from pilightcc.hyperion.hypjson import HyperionJson
from pilightcc.hyperion.hypproto import HyperionError
from pilightcc.settings.settings import Setting, LedCorner, LedDir


class AudioService(BaseService):
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
        super(AudioService, self).__init__(port, True)
        self._update_state(AudioService.StateValue.OK)
        self.__lock = Lock()
        self._new_data_event = Event()
        self.__hyperion_connector = None
        self.__audio_analyser = None
        self.__audio_effect = None

        # Register settings.
        self._register_settings_unit(
            [Setting.HYPERION_IP_ADDRESS, Setting.HYPERION_JSON_PORT],
            self.__update_hyperion_connector)

        self._register_settings_unit(
            [Setting.AUDIO_FRAME_RATE, Setting.LED_COUNT_TOP,
             Setting.LED_COUNT_BOTTOM, Setting.LED_COUNT_SIDE,
             Setting.LED_START_CORNER, Setting.LED_DIRECTION],
            self.__update_audio_effect)

        self._register_settings_unit([Setting.AUDIO_PRIORITY])

    def _setup(self):
        self.__update_hyperion_connector()
        self.__update_audio_effect()

    def _enable(self, enable):
        if enable:
            try:
                self.__hyperion_connector.connect()
            except HyperionError:
                pass
            self.__audio_analyser.start()
        else:
            self.__hyperion_connector.disconnect()
            self.__audio_analyser.stop()

    def __update_hyperion_connector(self):
        if self.__hyperion_connector is not None:
            self.__hyperion_connector.disconnect()
        self.__hyperion_connector = HyperionJson(
            self._get_setting(Setting.HYPERION_IP_ADDRESS),
            self._get_setting(Setting.HYPERION_JSON_PORT))

    def __update_audio_effect(self):
        if self.__audio_analyser is not None:
            self.__audio_analyser.stop()
        # self.__audio_effect = SpectrumEffect(self._get_settings())
        self.__audio_effect = LevelEffect(self._get_settings())
        self.__audio_analyser = self.__audio_effect.get_new_analyser(
            self.__update_audio_data)

    def __update_audio_data(self, data):
        with self.__lock:
            self._data = data
            self._new_data_event.set()

    def _run_service(self):
        try:
            # Check that an hyperion connection is available.
            if not self.__hyperion_connector.is_connected():
                self.__hyperion_connector.connect()
                self._update_state(AudioService.StateValue.OK)

            # Capture audio.
            if not self.__audio_analyser.is_running():
                self.__audio_analyser.start()
                self.__audio_effect.reset()

            if self._new_data_event.wait(
                    AudioService.__AUDIO_ANALYSER_TIMEOUT):
                # Only update if not timed out.
                with self.__lock:
                    data = self._data
                    self._new_data_event.clear()

                # Calculate send_effect frame.
                led_data = self.__audio_effect.get_effect(data)

                # Send message.
                self.__hyperion_connector.send_colors(
                    led_data, self._get_setting(Setting.AUDIO_PRIORITY),
                    self.__IMAGE_DURATION)
            else:
                # AudioAnalyser is not sending updates.
                self.__audio_analyser.stop()
                raise AudioAnalyserError("AudioAnalyser error")

        except (HyperionError, AudioAnalyserError) as err:
            self._update_state(AudioService.StateValue.ERROR, err.msg)
            self._safe_delay(AudioService.__ERROR_DELAY)


if __name__ == '__main__':
    ServiceLauncher.parse_args_and_execute("Audio", AudioService)
