""" Settings module. """

import os

from multiprocessing import Manager

from ConfigParser import RawConfigParser


class Setting(object):
    REV = 'rev'

    CAPTURE_ENABLE = 'uCaptureEnable'
    CAPTURE_SCALE_WIDTH = 'cWidth'
    CAPTURE_SCALE_HEIGHT = 'cHeight'
    CAPTURE_PRIORITY = 'cPriority'
    CAPTURE_FRAME_RATE = 'cFrameRate'

    HYPERION_IP_ADDRESS = 'hIpAddress'
    HYPERION_PORT = 'hPort'

    AUDIO_EFFECT_ENABLE = 'uAudioEffectEnable'
    AUDIO_EFFECT_SPOTIFY_ENABLE = 'aeSpotifyAutoEnable'
    AUDIO_EFFECT_PRIORITY = 'aePriority'
    AUDIO_EFFECT_FRAME_RATE = 'aeFrameRate'


class SettingsManager:
    """ Class which contains all settings.
    """

    class _BaseSetting(object):
        def __init__(self, default, section, hidden):
            self.default = default
            self.section = section
            self.hidden = hidden

    class _Section(object):
        CAPTURE = "CAPTURE"
        HYPERION = "HYPERION"
        AUDIO = "AUDIO"

    _CONFIG_PATH = "pilight-cc.config"

    _CONF = {
        # Hidden temporary settings.
        Setting.REV: _BaseSetting(0, None, True),

        Setting.CAPTURE_ENABLE: _BaseSetting(False, None, True),
        Setting.AUDIO_EFFECT_ENABLE: _BaseSetting(False, None, True),

        # Persistent settings.
        Setting.CAPTURE_SCALE_WIDTH: _BaseSetting(64, _Section.CAPTURE, False),
        Setting.CAPTURE_SCALE_WIDTH: _BaseSetting(64, _Section.CAPTURE, False),
        Setting.CAPTURE_PRIORITY: _BaseSetting(900, _Section.CAPTURE, False),
        Setting.CAPTURE_FRAME_RATE: _BaseSetting(30, _Section.CAPTURE, False),

        Setting.HYPERION_IP_ADDRESS: _BaseSetting("127.0.0.1",
                                                  _Section.HYPERION,
                                                  False),
        Setting.HYPERION_PORT: _BaseSetting(19945, _Section.HYPERION, False),

        Setting.AUDIO_EFFECT_SPOTIFY_ENABLE: _BaseSetting(False, _Section.AUDIO,
                                                          False),
        Setting.AUDIO_EFFECT_PRIORITY: _BaseSetting(800, _Section.AUDIO, False),
        Setting.AUDIO_EFFECT_FRAME_RATE: _BaseSetting(60, _Section.AUDIO, False)
    }

    def __init__(self):
        """ Constructor
        """
        self.__manager = Manager()
        self.__settings = self.__manager.dict()
        self.read_settings()

    def get_setting(self, key):
        """ Get a setting value.
        - key   : the key of the setting
        """
        return self.__settings[key]

    def set_setting(self, key, value):
        """ Set a setting value.
        - key   : the key of the setting
        - value : the value of the setting
        """
        self.__settings[key] = value

    def __save_config(self):
        """
        Save the current config file to storage.
        """
        try:
            config = RawConfigParser()

            for key, value in self.__settings.iteritems():
                setting = SettingsManager._CONF[key]

                # Create section if needed.
                if not config.has_section(setting.section):
                    config.add_section(setting.section)

                config.set(setting.section, key, value)

            # Writing configuration file to "configPath".
            with open(SettingsManager._CONFIG_PATH, 'wb') as config_file:
                config.write(config_file)

        except IOError:
            raise Exception()

    def __read_config(self):
        """
        Read config file, using default values for missing settings.
        """
        # Parse config file.
        config = RawConfigParser(allow_no_value=True)
        if os.path.exists(SettingsManager._CONFIG_PATH):
            config.read(SettingsManager._CONFIG_PATH)

        # Make sure the required values are set.
        self.__settings = {}
        for key, setting in SettingsManager._CONF.iteritems():
            val = config.get(setting.section, key)
            if not val:
                # Use default value instead.
                val = setting.default

            self.__settings[key] = val
