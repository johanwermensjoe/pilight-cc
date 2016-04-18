""" Hyperion utilities module. """


class HyperionError(Exception):
    """ Error raised for hyperion connection errors.

    Attributes:
        msg     -- explanation of the error
    """

    def __init__(self, msg):
        """
            :param msg: the error message
            :type msg: str
        """
        self.msg = msg
