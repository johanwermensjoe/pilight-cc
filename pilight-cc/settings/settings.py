""" Settings module. """

# Threading
from threading import RLock
from threading import Lock

# Config parsing
from os.path import exists
from ConfigParser import RawConfigParser
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError


class Setting(object):
    """ Setting identifier class.
    """
    CAPTURE_SCALE_WIDTH = 'cWidth'
    CAPTURE_SCALE_HEIGHT = 'cHeight'
    CAPTURE_PRIORITY = 'cPriority'
    CAPTURE_FRAME_RATE = 'cFrameRate'

    HYPERION_IP_ADDRESS = 'hIpAddress'
    HYPERION_PORT = 'hPort'

    AUDIO_EFFECT_SPOTIFY_ENABLE = 'aeSpotifyAutoEnable'
    AUDIO_EFFECT_PRIORITY = 'aePriority'
    AUDIO_EFFECT_FRAME_RATE = 'aeFrameRate'


class SettingsManager:
    """ Class which contains all settings.
    """

    class _BaseSetting(object):
        def __init__(self, default, section, hidden, converter):
            self.default = default
            self.section = section
            self.hidden = hidden
            self.converter = converter

    class _Section(object):
        CAPTURE = "CAPTURE"
        HYPERION = "HYPERION"
        AUDIO = "AUDIO_EFFECT"

    _CONFIG_PATH = "../pilight-cc.config"

    # Settings with default value, section and visibility.
    _CONF = {
        # Persistent settings.
        Setting.CAPTURE_SCALE_WIDTH: _BaseSetting(64, _Section.CAPTURE, False,
                                                  int),
        Setting.CAPTURE_SCALE_HEIGHT: _BaseSetting(64, _Section.CAPTURE, False,
                                                   int),
        Setting.CAPTURE_PRIORITY: _BaseSetting(900, _Section.CAPTURE, False,
                                               int),
        Setting.CAPTURE_FRAME_RATE: _BaseSetting(30, _Section.CAPTURE, False,
                                                 int),

        Setting.HYPERION_IP_ADDRESS: _BaseSetting("127.0.0.1",
                                                  _Section.HYPERION,
                                                  False, str),
        Setting.HYPERION_PORT: _BaseSetting(19945, _Section.HYPERION, False,
                                            int),

        Setting.AUDIO_EFFECT_SPOTIFY_ENABLE: _BaseSetting(False, _Section.AUDIO,
                                                          False, lambda s:
                                                          s == 'True'),
        Setting.AUDIO_EFFECT_PRIORITY: _BaseSetting(800, _Section.AUDIO, False,
                                                    int),
        Setting.AUDIO_EFFECT_FRAME_RATE: _BaseSetting(60, _Section.AUDIO, False,
                                                      int)
    }

    def __init__(self):
        """ Constructor
        """
        self.__settings_lock = RLock()
        self.__listener_lock = Lock()

        self.__read_settings()
        self.__listeners = []

    def __notify_listeners(self):
        """ Notifies the listeners that some setting has changed.
        """
        try:
            self.__listener_lock.acquire()
            for listener in self.__listeners:
                listener(self.get_settings())
        finally:
            self.__listener_lock.release()

    def save_settings(self):
        """
        Save the current config file to storage.
        """
        print "Saving settings"
        try:
            config = RawConfigParser()

            for key, value in self.get_settings().iteritems():
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

    def __read_settings(self):
        """
        Read config file, using default values for missing settings.
        """
        print "Reading settings"
        # Parse config file.
        config = RawConfigParser(allow_no_value=True)
        if exists(SettingsManager._CONFIG_PATH):
            config.read(SettingsManager._CONFIG_PATH)

        # Make sure the required values are set.
        self.__settings = {}
        for key, setting in SettingsManager._CONF.iteritems():
            try:
                val = config.get(setting.section, key)
            except (NoSectionError, NoOptionError):
                val = None
            if not val:
                # Use default value instead.
                val = setting.default

            self.__settings[key] = setting.converter(val)

    def add_on_update_listener(self, callback):
        """ Registers an settings update listener.
        - callback  : the callback function (should take settings as argument)
        """
        try:
            self.__listener_lock.acquire()
            self.__listeners.append(callback)
        finally:
            self.__listener_lock.release()

    def get_settings(self):
        """ Get a copy of all settings.
        """
        try:
            self.__settings_lock.acquire()
            return self.__settings.copy()
        finally:
            self.__settings_lock.release()

    def get_setting(self, key):
        """ Get a setting value.
        - key   : the key of the setting
        """
        try:
            self.__settings_lock.acquire()
            return self.__settings[key]
        finally:
            self.__settings_lock.release()

    def set_setting(self, key, value):
        """ Set a setting value.
        - key   : the key of the setting
        - value : the value of the setting
        """
        try:
            self.__settings_lock.acquire()
            self.__settings[key] = value
            self.__notify_listeners()
        finally:
            self.__settings_lock.release()
