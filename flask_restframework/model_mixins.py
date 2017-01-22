
class DeleteManyMixin:

    _allowed_methods = ["delete"]

    def delete(self, request):
        ids = None

        if request.json:
            ids = request.json.get("ids")

        qs = self.get_queryset()

        if ids:
            qs = qs.filter(id__in=ids)

        qs.delete()

        return "{}"