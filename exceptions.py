__author__ = 'stas'


class ValidationError(Exception):

    def __init__(self, data):
        """
        :param data: Can be string or dict in format {field: "Message"}
        """
        self.data = data

