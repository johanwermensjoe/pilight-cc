""" Settings module. """


class SettingsMonitor(object):
    """ Class to capture changes in settings.
    """

    def __init__(self, settings):
        self.__settings = settings

    def onAbortRequested(self):
        self.__settings.abort = False

    def onSettingsChanged(self):
        self.__settings.readSettings()

    def onScreensaverDeactivated(self):
        self.__settings.screensaver = False

    def onScreensaverActivated(self):
        self.__settings.screensaver = True


class Settings:
    """ Class which contains all settings.
    """

    def __init__(self):
        """ Constructor
        """
        self.rev = 0
        self.__monitor = MyMonitor(self)
        self.__player = xbmc.Player()
        self.readSettings()

    def __del__(self):
        """ Destructor
        """
        del self.__monitor
        del self.__player

    def readSettings(self):
        """ (Re-)read all settings
        """
        self.enable = bool(addon.getSetting("hyperion_enable"))
        self.enableScreensaver = bool(addon.getSetting("screensaver_enable"))
        self.address = addon.getSetting("hyperion_ip")
        self.port = int(addon.getSetting("hyperion_port"))
        self.priority = int(addon.getSetting("hyperion_priority"))
        self.timeout = int(addon.getSetting("reconnect_timeout"))
        self.capture_width = int(addon.getSetting("capture_width"))
        self.capture_height = int(addon.getSetting("capture_height"))
        self.framerate = int(addon.getSetting("framerate"))

        self.showErrorMessage = True
        self.rev += 1
