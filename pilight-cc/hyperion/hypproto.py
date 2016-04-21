""" Hyperion Protocol Buffer communication module. """

# Networking
from socket import error
from struct import pack, unpack

# Protocol buffer message
from hyperion.hyputil import HyperionError, HyperionConnector
from hyperion.message_pb2 import HyperionRequest, HyperionReply, \
    ColorRequest, ImageRequest, ClearRequest


class HyperionProto(HyperionConnector):
    """ Provide Protocol Buffer based interface to Hyperion server.
    """

    def __init__(self, ip_address, port, timeout=5):
        """
        Connect to hyperion server.
            :param ip_address: the host address
            :type ip_address: str
            :param port: the host port
            :type port: int
            :param timeout: timeout in seconds before error (default: 5)
            :type timeout: int
        """
        super(HyperionProto, self).__init__(ip_address, port, timeout)

    def __send_proto(self, message):
        """ Send the given proto message to Hyperion.

        A RuntimeError will be raised if the reply contains an error
        - message : proto request to send
        """
        try:
            # Send the message.
            binary_request = message.SerializeToString()
            binary_size = pack(">I", len(binary_request))
            self._socket.sendall(binary_size)
            self._socket.sendall(binary_request)

            # Receive a reply from Hyperion.
            size = unpack(">I", self._socket.recv(4))[0]
            reply = HyperionReply()
            reply.ParseFromString(self._socket.recv(size))

            # Check the reply
            if not reply.success:
                self._connected = False
                raise HyperionError("Hyperion server error: " + reply.error)
        except error:
            self._connected = False
            raise HyperionError("Hyperion server connection error")

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

        self.__send_proto(request)

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

        self.__send_proto(request)

    def clear(self, priority):
        """ Clear the given priority channel.
        - priority : the priority channel to clear
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.CLEAR
        clear_request = request.Extensions[ClearRequest.clearRequest]
        clear_request.priority = priority

        self.__send_proto(request)

    def clear_all(self):
        """ Clear all active priority channels.
        """
        # Create the request.
        request = HyperionRequest()
        request.command = HyperionRequest.CLEARALL

        self.__send_proto(request)
