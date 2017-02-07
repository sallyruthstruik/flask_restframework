import json


class BaseBackend:

    def __init__(self, qs, request, resource):
        self.qs = qs
        self.request = request
        self.resource = resource

    def filter(self):
        raise NotImplementedError


class OrderingBackend(BaseBackend):
    """
    Allows ordering with GET parameter.
    For example,

        GET ?ordering=name,-value

    Will sort .order_by(["name", "-value"])

    You can set resource attribute **ordering** if you want default ordering
    """

    def _default_ordering(self):
        if hasattr(self.resource, "ordering"):
            return self.resource.ordering
        return []

    def filter(self):

        try:
            ordering_fields = self.request.args.get("ordering")

            if ordering_fields:
                ordering_fields = ordering_fields.split(",")
            else:
                ordering_fields = []
        except:
            ordering_fields = []

        ordering_fields = ordering_fields or self._default_ordering()

        if ordering_fields:
            self.qs = self.qs.order_by(*ordering_fields)

        return self.qs


class JsonFilterBackend(BaseBackend):
    """
    Allows custom filtration with json_filter GET parameter.
    For example:

        GET ?json_filters={"name": "blablabla"}

    will filter queryset in this way:

        .filter(__raw__={"name": "blablabla"})

    You can manage filter logig with Resource attribute update_json_filter which accepts
    (json_filter)->new_json_filter

    """

    def filter(self):
        try:
            json_filter = self.request.args.get("json_filters")
            json_filter = json.loads(json_filter)
        except:
            return self.qs

        if hasattr(self.resource, "update_json_filter"):
            json_filter = self.resource.__class__.update_json_filter(json_filter)

        self.qs = self.qs.filter(__raw__=json_filter)

        return self.qs


class SearchFilterBackend(BaseBackend):
    """
    Allows custom filtration with search GET parameter.
    For example:

        GET ?search="search text"

    will filter queryset in this way:

        .filter(__raw__={"$text": {"$search": search_text}})

    """

    def filter(self):

        try:
            search_text = self.request.args.get("search")
        except:
            search_text = ""

        if search_text:
            self.qs = self.qs.filter(__raw__={"$text": {"$search": search_text}})

        return self.qs
