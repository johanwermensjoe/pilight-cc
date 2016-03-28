""" Hyperion Service module. """

# Networking
import socket
import struct

# Multiprocessing
from multiprocessing import Queue

from services.service import BaseService

from settings.settings import Setting
from settings.settings import Flag

# Protocol buffer message
from message_pb2 import HyperionRequest
from message_pb2 import HyperionReply
from message_pb2 import ColorRequest
from message_pb2 import ImageRequest
from message_pb2 import ClearRequest


class HyperionService(BaseService):
    """ Hyperion Service class.
    """

    class StateValue(object):
        """ State Value class.
        """
        CONNECTED = 1
        DISCONNECTED = 2
        ERROR = 3

    def __init__(self, settings_connector):
        """ Constructor
        - settings_connector    : connector for settings updates
        """
        super(HyperionService, self).__init__(settings_connector,
                                              Flag.HYPERION_ENABLE)
        self.state.set_value(HyperionService.StateValue.DISCONNECTED)
        self.__queue = Queue()

    def __del__(self):
        # Close the socket.
        self.__socket.close()

    def __load_settings(self):
        # Load the updated settings.
        self.__ip_address = self.__settings_connector.get_setting(
            Setting.HYPERION_IP_ADDRESS)
        self.__port = self.__settings_connector.get_setting(
            Setting.HYPERION_PORT)

    def __connect(self):
        """ Attempt connection to hyperion server.
        """
        # Create a new socket.
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.settimeout(2)

        # Connect socket to the provided server.
        self.__socket.connect((self.__ip_address, self.__port))

    def __send_message(self, message):
        """ Send the given proto message to Hyperion.

        A RuntimeError will be raised if the reply contains an error
        - message : proto request to send
        """
        # Send the message.
        binary_request = message.SerializeToString()
        binary_size = struct.pack(">I", len(binary_request))
        self.__socket.sendall(binary_size)
        self.__socket.sendall(binary_request);

        # Receive a reply from Hyperion.
        size = struct.unpack(">I", self.__socket.recv(4))[0]
        reply = HyperionReply()
        reply.ParseFromString(self.__socket.recv(size))

        # Check the reply
        if not reply.success:
            raise RuntimeError("Hyperion server error: " + reply.error)

    def __run_service(self):

        try:
            # Try to connect to server if not connected.
            if self.state.get_value() != \
                    HyperionService.StateValue.CONNECTED:
                self.__connect()

            # Fetch and send messages.
            self.__send_message(self.__queue.get())
        except socket.timeout:
            self.state.set_value(HyperionService.StateValue.ERROR)
        except socket.error:
            self.state.set_value(HyperionService.StateValue.ERROR)
        except RuntimeError:
            self.state.set_value(HyperionService.StateValue.ERROR)

    def send_color(self, color, priority, duration=-1):
        """ Send a static color to Hyperion.
        - color    : integer value with the color as 0x00RRGGBB
        - priority : the priority channel to use
        - duration : duration the LEDs should be set
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.COLOR
        color_request = request.Extensions[ColorRequest.colorRequest]
        color_request.RgbColor = color
        color_request.priority = priority
        color_request.duration = duration

        # Add to queue.
        self.__queue.put(request)

    def send_image(self, width, height, data, priority, duration=-1):
        """ Send an image to Hyperion.
        - width    : width of the image
        - height   : height of the image
        - data     : image data (byte string containing 0xRRGGBB pixel values)
        - priority : the priority channel to use
        - duration : duration the LEDs should be set
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.IMAGE
        image_request = request.Extensions[ImageRequest.imageRequest]
        image_request.imagewidth = width
        image_request.imageheight = height
        image_request.imagedata = str(data)
        image_request.priority = priority
        image_request.duration = duration

        # Add to queue.
        self.__queue.put(request)

    def clear(self, priority):
        """ Clear the given priority channel.
        - priority : the priority channel to clear
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.CLEAR
        clear_request = request.Extensions[ClearRequest.clearRequest]
        clear_request.priority = priority

        # Add to queue.
        self.__queue.put(request)

    def clear_all(self):
        """ Clear all active priority channels.
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.CLEARALL

        # Add to queue.
        self.__queue.put(request)
