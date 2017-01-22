from flask import jsonify
from mongoengine.queryset.queryset import QuerySet

from flask_restframework.decorators import list_route


class DistinctValuesMixin:

    distinct_fields = None

    @list_route(methods=["GET"])
    def distinct(self, request):
        assert self.distinct_fields, "You should set list of allowed fields"
        qs = self.get_queryset()

        field = request.args.get("field")

        if field not in self.distinct_fields:
            return jsonify([]), 400

        assert isinstance(qs, QuerySet)

        return jsonify([item for item in qs.distinct(field)])
