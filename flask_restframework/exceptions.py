__author__ = 'stas'

class BaseRestException(Exception):

    status = 500
    name = "Server Error"

    def __init__(self, data):
        """
        :param data: Can be string or dict in format {field: "Message"}
        """
        self.data = data

class ValidationError(BaseRestException):

    status = 400
    name = "Validation Error"

class AuthorizationError(BaseRestException):
    status = 401
    name = "Not authorized"


class NotFound(BaseRestException):
    status = 404
    name = "Not Found"

class ReturnResponseException(BaseRestException):
    def __init__(self, data, status=200):
        super(ReturnResponseException, self).__init__(data)
        self.status = status