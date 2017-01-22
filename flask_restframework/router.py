from flask.globals import request

from flask_restframework.resource import BaseResource


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

    METHODS = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS"
    ]


    def _get_list_handler(self, request, viewCls):
        "returns handler for list route"

    def _get_route_handler(self, func, viewCls):

        def handler(*a, **k):
            return func(viewCls(request), request, *a, **k)

        return handler

    def _iter_methods(self, viewCls, processed):

        for key, value in viewCls.__dict__.items():
            if key in processed:
                continue

            processed.append(key)

            yield (key, value)

        for parentCls in viewCls.__bases__:
            for item in self._iter_methods(parentCls, processed):
                yield item

    def register(self, url, viewCls, basename):
        if issubclass(viewCls, BaseResource):

            listMethods = []
            detailMethods = []

            for key, value in self._iter_methods(viewCls, []):
                if callable(value):
                    if key.upper() in self.METHODS:
                        # simple list route
                        listMethods.append(key)
                    elif key.replace("_object", "").upper() in self.METHODS:
                        detailMethods.append(key.replace("_object", ""))

                    else:
                        if hasattr(value, "_is_view_function"):
                            self.app.add_url_rule(
                                url+value._route_part,
                                basename+"-{}".format(value._name_part),
                                self._get_route_handler(value, viewCls),
                                methods=value._methods
                            )


            if listMethods:
                self.app.add_url_rule(
                    url, basename, viewCls.as_view(basename),
                    methods=listMethods
                )

            if detailMethods:
                detailBasename = basename + "-detail"
                self.app.add_url_rule(
                    url + "/<pk>", detailBasename, viewCls.as_view(
                        detailBasename, suffix="_object"
                    ), methods=detailMethods
                )

