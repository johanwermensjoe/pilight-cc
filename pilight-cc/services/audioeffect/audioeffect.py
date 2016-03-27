""" Audio Effect service module. """

# Multiprocessing
from multiprocessing import Process
from threading import Timer

from services.manager import State

from settings.settings import Flag
from settings.settings import Setting


class AudioEffectService(Process):
    """ Capture Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        OK = 1
        ERROR = 2

    _IMAGE_DURATION = 500

    def __init__(self, hyperion_service, settings_connector):
        """ Constructor
        - hyperion_service      : hyperion service to send messages
        - settings_connector    : connector for settings updates
        """
        self.__state = State()
        self.__state.set_value(AudioEffectService.StateValue.OK)
        self.__settings_connector = settings_connector
        self.__hyperion_service = hyperion_service
        self.__load_settings()

    def __update_pixel_buffer(self):
        self.__data = self.scale_pixel_buffer(
            self.get_pixel_buffer(),
            self.__scale_width,
            self.__scale_height)

    def __load_settings(self):
        # Clear alert before to avoid missing updates.
        self.__settings_connector.signal.clear()

        # Load the updated settings.
        self.__priority = self.__settings_connector.get_setting(
            Setting.AUDIO_EFFECT_PRIORITY)
        self.__frame_rate = self.__settings_connector.get_setting(
            Setting.AUDIO_EFFECT_FRAME_RATE)

    def run(self):
        # Check if the capture service is enabled or block until it is.
        self.__settings_connector.get_flag(Flag.AUDIO_EFFECT_ENABLE).wait()

        # Schedule the next run.
        Timer(1 / self.__frame_rate, self.__run).start()

        # Reload settings if needed.
        if self.__settings_connector.signal.is_set():
            self.__load_settings()

        # Capture audio.
        # TODO
        self.read_audio()

        # Calculate effect frame.
        # TODO
        self.calculate_effect()

        # Send message.
        # TODO
        self.__hyperion_service.send_image(self.__scale_width,
                                           self.__scale_height,
                                           self.__data.get_pixels(),
                                           self.__priority,
                                           AudioEffectService._IMAGE_DURATION)

    @staticmethod
    def read_audio():
        pass

    @staticmethod
    def calculate_effect():
        pass