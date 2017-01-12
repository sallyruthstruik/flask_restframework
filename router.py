from flask.ext.validator.resource import BaseResource


class BaseRouter(object):

    def __init__(self, app=None):
        """
        :type app: flask.app.Flask | flask.blueprints.Blueprint
        """
        self.init_app(app)

    def init_app(self, app):
        self.app = app


class DefaultRouter(BaseRouter):
    """
    You should use this class for registering Resource/ModelResource classes.
    Example::

        >>> router = DefaultRouter(app)
        >>> router.register("/test", ResourceCls, "test")

    For each register call (url, viewCls, basename)
    It will add 2 routing rules:

        * url with methods from viewCls.get_allowed_methods()
        * url + "/<id>" with methods from viewCls.get_allowed_object_methods()

    """
    def register(self, url, viewCls, basename):
        if issubclass(viewCls, BaseResource):

            methods = viewCls.get_allowed_methods()
            objMethods = viewCls.get_allowed_object_methods()

            if methods:
                self.app.add_url_rule(
                    url, basename, viewCls.as_view(basename),
                    methods=methods
                )
            if objMethods:
                detailBasename = basename + "-detail"
                self.app.add_url_rule(
                    url + "/<pk>", detailBasename, viewCls.as_view(
                        detailBasename, suffix="_object"
                    ), methods=objMethods
                )

