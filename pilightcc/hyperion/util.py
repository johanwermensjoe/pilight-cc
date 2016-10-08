""" Hyperion utilities module. """

import socket

from pilightcc.util.error import BaseError


class HyperionError(BaseError):
    """ Error raised for hyperion connection errors.
    """

    def __init__(self, msg):
        """
            :param msg: the error message
            :type msg: str
        """
        super(HyperionError, self).__init__(msg)


class HyperionConnector(object):
    """ Manages connection to a Hyperion server.
    """

    def __init__(self, ip_address, port, timeout=5):
        """
            :param ip_address: the host address
            :type ip_address: str
            :param port: the host port
            :type port: int
            :param timeout: timeout in seconds before error (default: 5)
            :type timeout: int
        """
        self.__ip_address = ip_address
        self.__port = port
        self.__timeout = timeout
        self._socket = None
        self._connected = False

    def __del__(self):
        """ Disconnect """
        self.disconnect()

    def connect(self):
        """ Attempt connection to hyperion server.
        """
        # Disconnect if previously connected.
        if not self._connected:
            # Create a new socket.
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.__timeout)

            try:
                # Connect socket to the provided server.
                self._socket.connect((self.__ip_address, self.__port))
                self._connected = True
            except socket.error:
                raise HyperionError("Connection failed")

    def disconnect(self):
        """ Disconnect from Hyperion server if connected.
        """
        if self._connected:
            self._socket.close()
            self._connected = False

    def is_connected(self):
        """ The connection status.
            :return: True if is connected to server
            :rtype: bool
        """
        return self._connected
