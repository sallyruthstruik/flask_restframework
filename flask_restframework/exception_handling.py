"""
This module provides JSON exception handling.
"""
import logging

from flask import jsonify
from flask.app import Flask
from werkzeug.exceptions import default_exceptions

LOGGER = logging.getLogger("restframework.exceptions")

class ExceptionHandler:
    """

    Usage
    .. code-block:: python

        ExceptionHandler(app)\
            .handle_common_exceptions()\
            .handle_http_exceptions()

    On exception you'll get::

        {
          "code": 500,
          "description": "exceptions must derive from BaseException",
          "error": "TypeError"
        }

    for common exceptions and::

        {
          "code": 404,
          "description": "The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again.",
          "error": "Not Found"
        }

    for http ones

    """
    def __init__(self, app=None):
        ":type app: Flask"
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

    def handle_common_exceptions(self):

        def common_exception_handler(e):
            LOGGER.exception(
                "Getted common exception: %s", e,
                extra={"meta": e}
            )

            resp = jsonify({
                "error": e.__class__.__name__,
                "code": 500,
                "description": str(e)
            })

            resp.status_code = 500

            return resp

        self.app.errorhandler(Exception)(common_exception_handler)

        return self

    def handle_http_exceptions(self):

        def handler(e):
            LOGGER.error(
                "Getted http exception: %s", e, exc_info=True,
                extra={"meta": e}
            )
            resp = jsonify({
                "error": e.name,
                "code": e.code,
                "description": e.description
            })

            resp.status_code = e.code

            return resp

        for code, ex in default_exceptions.items():
            self.app.errorhandler(code)(handler)

        return self
