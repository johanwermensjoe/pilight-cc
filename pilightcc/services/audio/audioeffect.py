""" Audio Effect module. """

from pilightcc.services.audio.audioanalyzer import AudioAnalyser
from pilightcc.settings.settings import Setting, LedCorner, LedDir


class BaseAudioEffect(object):
    _STD_MULTI_CH = True
    _STD_INTERVAL = 50

    _PULSE_AUDIO_DEVICE = "alsa_output.usb-Propellerhead_Balance_0001002008080-00.analog-stereo.monitor"  # TODO Remove

    def __init__(self, settings):
        self._settings = settings

    def _join_channel_effects(self, left_ch, right_ch):
        # Pre calculate some led counts.
        channel_count_top = self._settings[Setting.LED_COUNT_TOP] // 2
        channel_count_bottom = self._settings[Setting.LED_COUNT_BOTTOM] // 2

        # Piece together the channels. (Adding the right channel in reverse.)
        joined = []
        joined += left_ch
        joined += [[0, 0, 0]] if \
            channel_count_top * 2 < \
            self._settings[Setting.LED_COUNT_TOP] else []
        joined += right_ch[::-1]
        joined += [[0, 0, 0]] if \
            channel_count_bottom * 2 < \
            self._settings[Setting.LED_COUNT_BOTTOM] else []

        # Calculate the starting index.
        channels_offset = [channel_count_bottom,
                           self._settings[Setting.LED_COUNT_SIDE],
                           self._settings[Setting.LED_COUNT_TOP],
                           self._settings[Setting.LED_COUNT_SIDE]]

        corner_indices = {LedCorner.SW: 1, LedCorner.NW: 2,
                          LedCorner.NE: 3, LedCorner.SE: 4}

        # Set the effective corner index and channel order.
        corner_index = corner_indices.get(
            self._settings[Setting.LED_START_CORNER])
        if self._settings[Setting.LED_DIRECTION] == LedDir.CCW:
            corner_index = 1 - corner_index
            joined.reverse()

        start = sum(channels_offset[:corner_index])

        # Reorder the joined data.
        reordered = joined[start:] + joined[:start]

        return self._flatten_color_list(reordered)

    @staticmethod
    def _create_basic_color_effect(norm_data, color):
        return [[int(round(c * v)) for c in color] for v in norm_data]

    @staticmethod
    def _apply_linear_decay_effect(norm_data, prev_data, decay_amount):
        return [x if x >= y else y - decay_amount for (x, y) in
                zip(norm_data, prev_data)]

    @staticmethod
    def _normalize_data(data, min_value, max_value):
        diff = max_value - min_value
        return [(max(min_value, min(max_value, v)) - min_value) / diff for v in
                data]

    @staticmethod
    def _flatten_color_list(effect_data):
        return [c for color in effect_data for c in color]

    def reset(self):
        """ To be implemented by subclass.
        """
        pass

    def get_new_analyser(self, callback):
        """ To be implemented by subclass.
        """
        raise NotImplementedError("Please implement this method")

    def get_effect(self, data):
        """ To be implemented by subclass.
        Calculate the LED effects from the spectrum data.
            :param data: the analyser data
            :type data: list | dict
            :return: the LED data as a list of repeated (r,g,b) values
            :rtype: list
        """
        raise NotImplementedError("Please implement this method")


class SpectrumEffect(BaseAudioEffect):
    _EFFECT_MIN_AMP = -30
    _EFFECT_MAX_AMP = 0
    _EFFECT_DECAY = 0.3

    def __init__(self, settings):
        super(SpectrumEffect, self).__init__(settings)
        self.__prev_left_ch = None
        self.__prev_right_ch = None

    def reset(self):
        self.__prev_left_ch = None
        self.__prev_right_ch = None

    def get_new_analyser(self, callback):
        return AudioAnalyser(self._PULSE_AUDIO_DEVICE, callback,
                             mode=AudioAnalyser.Mode.SPECTRUM,
                             interval=self._STD_INTERVAL,
                             multichannel=self._STD_MULTI_CH,
                             threshold=self._EFFECT_MIN_AMP,
                             cutoff=self._EFFECT_MAX_AMP)

    def get_effect(self, data):
        leds_per_channel = (self._settings[Setting.LED_COUNT_TOP] // 2 +
                            self._settings[Setting.LED_COUNT_BOTTOM] // 2 +
                            self._settings[Setting.LED_COUNT_SIDE])

        # Divide into two channels and create effects.
        left_ch = self._normalize_data(
            data[0][:leds_per_channel], self._EFFECT_MIN_AMP,
            self._EFFECT_MAX_AMP)

        if self.__prev_left_ch is not None:
            left_ch = self._apply_linear_decay_effect(
                left_ch, self.__prev_left_ch,
                self._EFFECT_DECAY / self._settings[
                    Setting.AUDIO_FRAME_RATE])
        self.__prev_left_ch = left_ch

        left_ch_eff = self._create_basic_color_effect(
            left_ch, [0, 0, 255])

        # Second channel if needed.
        if len(data) > 1:
            right_ch = self._normalize_data(
                data[1][:leds_per_channel], self._EFFECT_MIN_AMP,
                self._EFFECT_MAX_AMP)

            if self.__prev_right_ch is not None:
                right_ch = self._apply_linear_decay_effect(
                    right_ch, self.__prev_right_ch,
                    self._EFFECT_DECAY / self._settings[
                        Setting.AUDIO_FRAME_RATE])
            self.__prev_right_ch = right_ch

            right_ch_eff = self._create_basic_color_effect(
                right_ch, [0, 0, 255])
        else:
            right_ch_eff = left_ch_eff

        # Join channels correctly.
        return self._join_channel_effects(left_ch_eff, right_ch_eff)


class LevelEffect(BaseAudioEffect):
    _EFFECT_MIN_AMP = -30
    _EFFECT_MAX_AMP = 0
    _EFFECT_FALLOFF = 20
    _EFFECT_DECAY_DELAY = 30

    def get_new_analyser(self, callback):
        return AudioAnalyser(self._PULSE_AUDIO_DEVICE, callback,
                             mode=AudioAnalyser.Mode.LEVEL,
                             interval=self._STD_INTERVAL,
                             multichannel=self._STD_MULTI_CH,
                             threshold=self._EFFECT_MIN_AMP,
                             cutoff=self._EFFECT_MAX_AMP,
                             peak_ttl=self._EFFECT_DECAY_DELAY,
                             peak_falloff=self._EFFECT_FALLOFF)

    def get_effect(self, data):
        leds_per_channel = (self._settings[Setting.LED_COUNT_TOP] // 2 +
                            self._settings[Setting.LED_COUNT_BOTTOM] // 2 +
                            self._settings[Setting.LED_COUNT_SIDE])

        # Divide into two channels and create effects.
        rms = self._normalize_data(data['rms'], self._EFFECT_MIN_AMP,
                                   self._EFFECT_MAX_AMP)
        peak = self._normalize_data(data['peak'], self._EFFECT_MIN_AMP,
                                    self._EFFECT_MAX_AMP)
        decay = self._normalize_data(data['decay'], self._EFFECT_MIN_AMP,
                                     self._EFFECT_MAX_AMP)

        left_ch_eff = self._create_level_color_effect(peak[0],
                                                      leds_per_channel,
                                                      [0, 0, 255])

        # Second channel if needed.
        if len(peak) > 1:
            right_ch_eff = self._create_level_color_effect(peak[1],
                                                           leds_per_channel,
                                                           [0, 0, 255])
        else:
            right_ch_eff = left_ch_eff

        # Join channels correctly.
        return self._join_channel_effects(left_ch_eff, right_ch_eff)

    @staticmethod
    def _create_level_color_effect(norm_level, channel_width, color):
        level = norm_level * channel_width
        return [color if i < level else [0, 0, 0] for i in range(channel_width)]
