""" Hyperion Service module. """

# Networking
import socket
import struct

# Protocol buffer message
from message_pb2 import HyperionRequest
from message_pb2 import HyperionReply
from message_pb2 import ColorRequest
from message_pb2 import ImageRequest
from message_pb2 import ClearRequest


class HyperionError(Exception):
    """ Error raised for hyperion connection errors.

    Attributes:
        msg     -- explanation of the error
    """

    def __init__(self, msg):
        self.msg = msg


class HyperionConnector(object):
    """ Hyperion Service class.
    """

    def __init__(self, ip_address, port):
        """ Constructor
        """
        try:
            self.__connect(ip_address, port)
        except Exception:
            raise HyperionError("Connection failed")

    def __del__(self):
        # Close the socket.
        if self.__socket:
            self.__socket.close()

    def __connect(self, ip_address, port):
        """ Attempt connection to hyperion server.
        """
        # Create a new socket.
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.settimeout(2)

        # Connect socket to the provided server.
        self.__socket.connect((ip_address, port))

    def __send_message(self, message):
        """ Send the given proto message to Hyperion.

        A RuntimeError will be raised if the reply contains an error
        - message : proto request to send
        """
        # Send the message.
        binary_request = message.SerializeToString()
        binary_size = struct.pack(">I", len(binary_request))
        self.__socket.sendall(binary_size)
        self.__socket.sendall(binary_request)

        # Receive a reply from Hyperion.
        size = struct.unpack(">I", self.__socket.recv(4))[0]
        reply = HyperionReply()
        reply.ParseFromString(self.__socket.recv(size))

        # Check the reply
        if not reply.success:
            raise HyperionError("Hyperion server error: " + reply.error)

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

        self.__send_message(request)

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

        self.__send_message(request)

    def clear(self, priority):
        """ Clear the given priority channel.
        - priority : the priority channel to clear
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.CLEAR
        clear_request = request.Extensions[ClearRequest.clearRequest]
        clear_request.priority = priority

        self.__send_message(request)

    def clear_all(self):
        """ Clear all active priority channels.
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.CLEARALL

        self.__send_message(request)
