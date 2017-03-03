"""
Authentication backends used for perfoming request authentication.

Each backend has method get_user(request) which can:

    * return user if authentication succeeded
    * return False if authentication fails

Auth will be successful if at most one auth backend will succeeded.

You can set authentication backends per view function or per resource class
or set default in settings::

    >>> @auth_backends(*backend_classes)
    >>> def some_view():
    >>>     ...

    >>> class SomeResource(BaseResource):
    >>>     auth_backends = [*backends]

    >>> app.config["FLASK_REST"]["AUTHENTICATION_BACKENDS"] = [<backends>]

.. warning::

    You should enable AuthenticationMiddleware if you want to use it

"""


class BaseAuthenticationBackend(object):
    """
    Base class for all auth backends
    """

    def __init__(self, app):
        self.app = app

    def get_user(self, request):
        raise NotImplementedError

class NoAuth(BaseAuthenticationBackend):
    """
    If you don't want authorization - use thi backend
    """

    def get_user(self, request):
        return True

class SimpleBasicAuth(BaseAuthenticationBackend):
    """
    Provides simple Basic authorization.

    Login and pass are stored in config parameters: BASIC_AUTH_LOGIN, BASIC_AUTH_PASSWORD

    """

    def __init__(self, app):
        super(SimpleBasicAuth, self).__init__(app)

        self.login = self.app.config["BASIC_AUTH_LOGIN"]
        self.passw = self.app.config["BASIC_AUTH_PASSWORD"]

    def get_user(self, request):
        auth = request.authorization

        if auth:
            return auth.username == self.login and auth.password == self.passw

        return False
