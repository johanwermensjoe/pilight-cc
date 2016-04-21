""" General error/exception module. """


class BaseError(Exception):
    """ Error raised for hyperion connection errors.
    """

    def __init__(self, msg):
        """
            :param msg: the error message
            :type msg: str
        """
        super(BaseError, self).__init__(self)
        self.msg = msg