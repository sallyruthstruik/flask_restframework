import typing

from flask_restframework.queryset_wrapper import QuerysetWrapper
from flask_restframework.model_resource import ModelResource
from flask_restframework.serializer.model_serializer import ModelSerializer


class Base(object):

    queryset = None

    def method(self)->QuerysetWrapper:
        return self.queryset

    def _method(self)->QuerysetWrapper:
        return self.method()

    def run(self):
        x = self._method()   #type: QuerysetWrapper

class Temp(Base):

    def method(self)->QuerysetWrapper:
        return 1

