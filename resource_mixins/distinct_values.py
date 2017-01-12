from flask.ext.validator.decorators import list_route


class DistinctValuesMixin:

    @list_route
    def distinct(self, request):
      return "OK"
