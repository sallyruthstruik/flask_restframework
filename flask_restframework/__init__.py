"""

Serializer API
===================

.. automodule:: flask_restframework.serializer.base_serializer
    :members:

.. automodule:: flask_restframework.queryset_wrapper
    :members:

.. automodule:: flask_restframework.model_wrapper
    :members:

"""
from flask.app import Flask
from flask.json import jsonify
from flask.wrappers import Response

from flask_restframework.exceptions import BaseRestException

__author__ = 'stas'
__version__ = "0.0.34"

from flask_restframework.serializer import BaseSerializer
from flask_restframework.serializer.model_serializer import ModelSerializer
from flask_restframework.queryset_wrapper import QuerysetWrapper

class RestFramework(object):
    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        #type: (Flask)->None
        self.app = app

        def exception_handler(e):
            assert isinstance(e, BaseRestException)

            resp = jsonify(e.data)
            resp.status_code = e.status

            return resp

        self.app.errorhandler(BaseRestException)(exception_handler)


