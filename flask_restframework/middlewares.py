"""

To enable middlewares support you should register, for example::

    AuthenticationMiddleware.register(app)

"""
from flask import request


class BaseMiddleware(object):

    def __init__(self, app):
        self.app = app

    def get_view(self):
        """
        Returns view which will process current request

        :rtype: func
        """
        return self.app.view_functions[request.url_rule.endpoint]

    def before_request(self):
        """
        It will be called before request
        """
        pass

    def after_request(self, response):
        """
        It will be called after request
        """
        return response

    def register_handlers(self):
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)

    @classmethod
    def register(cls, app):
        cls(app).register_handlers()


class AuthenticationMiddleware(BaseMiddleware):

    def get_authentication_backends(self):
        view = self.get_view()

        if hasattr(view, "authentication_backends"):
            return view.authentication_backends

        return self.app.config.get("FLASK_REST", {
        }).get("AUTHENTICATION_BACKENDS", [])

    def before_request(self):
        user = None

        authBackends = self.get_authentication_backends()
        if not authBackends:
            return None

        for backendCls in authBackends:
            user = backendCls(self.app).get_user(request)

            if user:
                request.user = user
                return

        return "Authentication fails", 401

