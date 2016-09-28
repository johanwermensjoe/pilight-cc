""" Audio Effect service module. """

# Service
from pilightcc.services.service import BaseService
from pilightcc.services.service import ServiceLauncher
from threading import Lock, Event

# Application
from pilightcc.services.audio.audioanalyzer import AudioAnalyser, \
    AudioAnalyserError
from pilightcc.hyperion.hypjson import HyperionJson
from pilightcc.hyperion.hypproto import HyperionError
from pilightcc.settings.settings import Setting, LedCorner


class AudioEffectService(BaseService):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    __ERROR_DELAY = 5
    __AUDIO_ANALYSER_TIMEOUT = 5
    __IMAGE_DURATION = 500

    __EFFECT_MIN_AMP = -60
    __EFFECT_MAX_AMP = -20

    __PULSE_AUDIO_DEVICE = "alsa_output.usb-Propellerhead_Balance_0001002008080-00.analog-stereo.monitor"

    def __init__(self, port):
        """ Constructor
        """
        super(AudioEffectService, self).__init__(port, True)
        self._update_state(AudioEffectService.StateValue.OK)
        self.__lock = Lock()
        self._new_data_event = Event()
        self.__hyperion_connector = None
        self.__audio_analyser = None

        # Register settings.
        hyperion_unit = self._register_setting_unit(
            self.__update_hyperion_connector)
        hyperion_unit.add('_ip_address', Setting.HYPERION_IP_ADDRESS)
        hyperion_unit.add('_port', Setting.HYPERION_JSON_PORT)

        audio_effect_unit = self._register_setting_unit(
            self.__update_audio_analyser)
        audio_effect_unit.add('_frame_rate', Setting.AUDIO_EFFECT_FRAME_RATE)
        audio_effect_unit.add('_led_count_top', Setting.LED_COUNT_TOP)
        audio_effect_unit.add('_led_count_bottom', Setting.LED_COUNT_BOTTOM)
        audio_effect_unit.add('_led_count_side', Setting.LED_COUNT_SIDE)
        audio_effect_unit.add('_led_start_corner', Setting.LED_START_CORNER)
        audio_effect_unit.add('_led_direction', Setting.LED_DIRECTION)

        std_unit = self._register_setting_unit()
        std_unit.add('_priority', Setting.AUDIO_EFFECT_PRIORITY)

    def _setup(self):
        self.__update_hyperion_connector()
        self.__update_audio_analyser()

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
            self._ip_address, self._port)

    def __update_audio_analyser(self):
        if self.__audio_analyser is not None:
            self.__audio_analyser.stop()
        # TODO Args
        self.__audio_analyser = AudioAnalyser(self.__PULSE_AUDIO_DEVICE,
                                              self.__update_audio_data,
                                              interval=50)

    def __update_audio_data(self, data):
        with self.__lock:
            self._data = data
            self._new_data_event.set()

    def _run_service(self):
        try:
            # Check that an hyperion connection is available.
            if not self.__hyperion_connector.is_connected():
                self.__hyperion_connector.connect()
                self._update_state(AudioEffectService.StateValue.OK)

            # Capture audio.
            if not self.__audio_analyser.is_running():
                print("Starting AudioAnalyser")
                self.__audio_analyser.start()

            if self._new_data_event.wait(
                    AudioEffectService.__AUDIO_ANALYSER_TIMEOUT):
                # Only update if not timed out.
                with self.__lock:
                    data = self._data
                    self._new_data_event.clear()

                # Calculate send_effect frame.
                led_data = self.__calculate_effect(data)

                # Send message.
                self.__hyperion_connector.send_colors(led_data, self._priority)
            else:
                print("Error!")
                # AudioAnalyser is not sending updates.
                self.__audio_analyser.stop()
                raise AudioAnalyserError("AudioAnalyser error")

        except (HyperionError, AudioAnalyserError) as err:
            self._update_state(AudioEffectService.StateValue.ERROR, err.msg)
            self._safe_delay(AudioEffectService.__ERROR_DELAY)

    def __calculate_effect(self, data):
        """
        Calculate the LED effects from the spectrum data.
            :param data: the spectrum data
            :type data: list
            :return: the LED data as an array of repeated (r,g,b) values
            :rtype: bytearray
        """
        leds_per_channel = (self._led_count_top // 2 +
                            self._led_count_bottom // 2 +
                            self._led_count_side)

        # Divide into two channels and create effects.
        left_ch = AudioEffectService.prepare_audio_channel(
            data[0], leds_per_channel, AudioEffectService.__EFFECT_MIN_AMP,
            AudioEffectService.__EFFECT_MAX_AMP)
        left_ch_eff = AudioEffectService.create_basic_color_effect(
            left_ch, [255, 255, 255])

        # Second channel if needed.
        if len(data) > 1:
            right_ch = AudioEffectService.prepare_audio_channel(
                data[1], leds_per_channel, AudioEffectService.__EFFECT_MIN_AMP,
                AudioEffectService.__EFFECT_MAX_AMP)
            right_ch_eff = AudioEffectService.create_basic_color_effect(
                right_ch, [255, 255, 255])
        else:
            right_ch_eff = left_ch_eff

        # Join channels correctly.
        return self.__join_channel_effects(left_ch_eff, right_ch_eff)

    def __join_channel_effects(self, left_ch, right_ch):
        # Pre calculate some led counts.
        channel_count_top = self._led_count_bottom // 2
        channel_count_bottom = self._led_count_bottom // 2

        # Piece together the channels.
        joined = []
        joined += left_ch
        if channel_count_top * 2 < self._led_count_top:
            joined += [[0, 0, 0]]
        joined += right_ch[::-1]
        if channel_count_bottom * 2 < self._led_count_bottom:
            joined += [[0, 0, 0]]

        # Calculate the starting index.
        start = channel_count_bottom
        if self._led_start_corner == LedCorner.NW:
            start += self._led_count_side
        elif self._led_start_corner == LedCorner.NE:
            start += self._led_count_side + self._led_count_top
        elif self._led_start_corner == LedCorner.SE:
            start += self._led_count_side * 2 + self._led_count_top

        # Reorder the joined data.
        reordered = joined[start:]
        reordered += joined[:start]
        # return reordered
        return AudioEffectService.convert_effect_to_bytearray(reordered)

    @staticmethod
    def prepare_audio_channel(channel_data, channel_width, min_amp, max_amp):
        data = channel_data[:channel_width]
        return AudioEffectService.compress_audio(data, min_amp, max_amp)

    @staticmethod
    def compress_audio(data, min_amp, max_amp):
        diff = max_amp - min_amp
        return [(max(min_amp, min(max_amp, v)) - min_amp) / diff for v in
                data]

    @staticmethod
    def create_basic_color_effect(comp_data, color):
        return [[int(round(c * v)) for c in color] for v in comp_data]

    @staticmethod
    def convert_effect_to_bytearray(effect_data):
        return [c for color in effect_data for c in color]


if __name__ == '__main__':
    ServiceLauncher.parse_args_and_execute("AudioEffect", AudioEffectService)
