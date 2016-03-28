""" Audio Effect service module. """

from services.baseservice import BaseService

from settings.settings import Flag
from settings.settings import Setting


class AudioEffectService(BaseService):
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
        super(AudioEffectService, self).__init__(settings_connector,
                                                 Flag.AUDIO_EFFECT_ENABLE)
        self.state.set_value(AudioEffectService.StateValue.OK)
        self.__hyperion_service = hyperion_service

    def __update_pixel_buffer(self):
        self.__data = self.scale_pixel_buffer(
            self.get_pixel_buffer(),
            self.__scale_width,
            self.__scale_height)

    def __load_settings(self):
        # Load the settings.
        self.__priority = self.__settings_connector.get_setting(
            Setting.AUDIO_EFFECT_PRIORITY)
        self.__frame_rate = self.__settings_connector.get_setting(
            Setting.AUDIO_EFFECT_FRAME_RATE)

    def __run_service(self):
        # TODO timer

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
