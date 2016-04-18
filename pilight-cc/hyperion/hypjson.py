""" Hyperion JSON communication module. """

import socket

from hyperion.hyputil import HyperionError


class HyperionJsonConnector(object):

    def __init__(self, ip_address, port, timeout=10):
        """
        Connect to hyperion server.
            :param ip_address: the host address
            :type ip_address: str
            :param port: the host port
            :type port: int
            :param timeout: timeout in seconds before error (default: 5)
            :type timeout: int
        """
        try:
            self.__connect(ip_address, port, timeout)
        except Exception:
            raise HyperionError("Connection failed")

    def __del__(self):
        self.__socket.close()

    def __connect(self, ip_address, port, timeout):
        """ Attempt connection to hyperion server.
        """
        # Create a new socket.
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.settimeout(timeout)

        # Connect socket to the provided server.
        self.__socket.connect((ip_address, port))

    def disconnect(self):
        self.socket.send('{"command":"clearall"}\n')

    def send_led_data(self, led_data):
        """
        Send the led data in a message format the hyperion json server understands
        :param led_data: bytearray of the led data (r,g,b) * hyperion.ledcount
        """

        if not self.connected:
            return
        # create a message to send
        message = '{"color":['
        # add all the color values to the message
        for i in range(len(led_data)):
            message += repr(led_data[i])
            # separate the color values with ",", but do not add a "," at the end
            if not i == len(led_data) - 1:
                message += ','
        # complete message
        message += '],"command":"color","priority":100}\n'
        self.socket.send(message)