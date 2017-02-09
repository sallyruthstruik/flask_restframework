from flask import jsonify
from mongoengine.queryset.queryset import QuerySet

from flask_restframework.decorators import list_route


class DistinctValuesMixin:
    """
    Allows to get distinct values for fields in resource.
    Example usage::

        >>> class SomeResource(DistinctValuesMixin,
        >>>                    ModelResource):
        >>>     serializer_class = SomeSerializer
        >>>     ordering = ["-created"]
        >>>     distinct_fields = ["name"]
        >>>
        >>>     def get_queryset(self):
        >>>         return SomeModel.objects.all()

    You should specify required resource attribute **distinct_fields** to list of allowed fields.
    Then you can make requests::

        GET <resource base url>/distinct?field=<fieldname>

    Response will be list of distinct values of field <fieldname> in database.
    You can filter response with usual backend filters.
    """
    distinct_fields = None

    @list_route(methods=["GET"])
    def distinct(self, request):
        assert self.distinct_fields, "You should set list of allowed fields"
        qs = self.get_queryset()

        qs = self.filter_qs(qs)

        field = request.args.get("field")

        if field not in self.distinct_fields:
            return jsonify([]), 400

        assert isinstance(qs, QuerySet)

        return jsonify([item for item in qs.distinct(field)])
