""" Hyperion JSON communication module. """
import socket
import json

from pilightcc.hyperion.util import HyperionError, HyperionConnector


class HyperionJson(HyperionConnector):
    """ Provide JSON based interface to Hyperion server.
    """

    class _Command(object):
        CLEAR = 'clear'
        COLOR = 'color'
        CLEAR_ALL = 'clearall'
        EFFECT = 'send_effect'
        SERVER_INFO = 'serverinfo'

    class _Field(object):
        COMMAND = 'command'
        PRIORITY = 'priority'
        COLOR = 'color'
        DURATION = 'duration'
        EFFECT = 'send_effect'
        EFFECT_NAME = 'name'
        EFFECT_ARGS = 'args'

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
        super(HyperionJson, self).__init__(ip_address, port, timeout)

    def __send_json(self, fields):
        """
        Send a JSON message to the Hyperion server.
            :param fields:
            :type fields: dict
            :return:
            :raises HyperionError
        """
        try:
            self._socket.sendall(json.dumps(fields) + "\n")
        except socket.error:
            self._connected = False
            raise HyperionError("Connection failed")

    def clear_all(self):
        """
        Clear all previous commands.
            :return:
            :raises: HyperionError
        """
        self.__send_json({HyperionJson._Field.COMMAND:
                          HyperionJson._Command.CLEAR_ALL})

    def clear(self, priority):
        """
        Clear all previous commands with lower priority.
            :param priority: the priority
            :type priority: int
            :return:
            :raises: HyperionError
        """
        self.__send_json({HyperionJson._Field.COMMAND:
                          HyperionJson._Command.CLEAR,
                          HyperionJson._Field.PRIORITY: priority})

    def send_effect(self, name, priority, args=None):
        """
        Show an send_effect stored on the server.
            :param name: the name of the send_effect
            :type name: str
            :param priority: the priority
            :type priority: int
            :param args: commandline send_effect arguments
            :type args: dict
            :return:
            :raises: HyperionError
        """
        if args is None:
            args = {}
        self.__send_json({HyperionJson._Field.COMMAND:
                          HyperionJson._Command.EFFECT,
                          HyperionJson._Field.PRIORITY: priority,
                          HyperionJson._Field.EFFECT: {
                              HyperionJson._Field.EFFECT_NAME: name,
                              HyperionJson._Field.EFFECT_ARGS: args
                          }})

    def send_colors(self, colors, priority, duration=-1):
        """
        Set individual send_colors for the LEDs or a single color.
            :param colors: list of the flattened led data (r,g,b) * led count
            :type colors: list
            :param priority: the priority
            :type priority: int
            :param duration: the display duration in milliseconds (default: -1)
            :type duration: int
            :return:
            :raises: HyperionError

        .. Note:: If only one set of (r,g,b) values are given
                  the color will apply to all LEDs.
        """
        self.__send_json({HyperionJson._Field.COMMAND:
                          HyperionJson._Command.COLOR,
                          HyperionJson._Field.PRIORITY: priority,
                          HyperionJson._Field.COLOR: colors,
                          HyperionJson._Field.DURATION: duration})
