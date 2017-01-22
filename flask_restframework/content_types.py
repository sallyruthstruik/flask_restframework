from flask_restframework.exceptions import ValidationError

__author__ = 'stas'

class BaseContentType:
    """
    For given request returns dictionary with data, base on request Content-Type header
    Or raises ValidationError if no data present
    """

    HEADER = None

    def __init__(self, request, data_required=False):
        self.request = request
        self.data_required = data_required

    def run_get_data(self):
        if self.request.headers["Content-Type"] == self.HEADER:
            return self.get_data()
        else:
            if self.data_required:
                raise ValidationError("No data with content-type {} found".format(self.HEADER))


    def get_data(self):
        raise NotImplementedError()

class JsonContentType(BaseContentType):

    HEADER = "application/json"

    def get_data(self):
        return self.request.json

