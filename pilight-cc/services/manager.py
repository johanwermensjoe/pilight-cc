""" Service Manager module. """

from multiprocessing import Value

from services.capture.capture import CaptureService

from services.hyperion.hyperion import HyperionService

from settings.settings import SettingsManager


class ServiceManager(object):
    """ Service Manager class.
        """

    def __init__(self):
        """ Constructor
        """
        # Setup all services.
        self.settings_manager = SettingsManager()
        self.hyperion_service = HyperionService()

        connector = self.settings_manager.create_connector()
        self.capture_service = CaptureService(self.hyperion_service, connector)

        # Setup communication channels.
        # TODO


class State(object):
    def __init__(self):
        self.__value = Value("i")

    def set_value(self, new_value):
        self.__value.value = new_value

    def get_value(self):
        return  self.__value.value
