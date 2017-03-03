__author__ = 'stas'

class BaseException(Exception):

    status = 500
    name = "Server Error"

class ValidationError(BaseException):

    status = 400
    name = "Validation Error"

    def __init__(self, data):
        """
        :param data: Can be string or dict in format {field: "Message"}
        """
        self.data = data

class AuthorizationError(BaseException):
    status = 401
    name = "Not authorized"


class NotFound(BaseException):
    status = 404
    name = "Not Found"
