""" Service Manager module. """

from multiprocessing import Value

from services.capture.capture import CaptureService

from services.hyperion.hyperion import HyperionService


class ServiceManager(object):
    """ Service Manager class.
        """

    def __init__(self):
        """ Constructor
        """
        # Setup all services.
        # TODO
        self.capture_service = CaptureService()
        self.hyperion_service = HyperionService()

        # Setup communication channels.
        # TODO


class State(object):
    def __init__(self):
        self.__value = Value("i")

    def value(self):
        return self.__value.value
