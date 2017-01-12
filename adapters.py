"""
Because of different DB libs Flask can work with,
In this module I will describe common interface for working with Queryset/Model instances
"""
from mongoengine.queryset.queryset import QuerySet


class BaseModelAdapter:

    def __init__(self, document):
        self._document = document


class BaseQuerysetAdapter:

    MODEL_ADAPTER = None

    def __init__(self, queryset):
        self._queryset = queryset

    def __iter__(self):
        for item in self._queryset:
            yield self.MODEL_ADAPTER(item)


class MongoEngineModelAdapter(BaseModelAdapter):
    pass

class MongoEngineQuerysetAdapter(BaseQuerysetAdapter):

    MODEL_ADAPTER = MongoEngineModelAdapter

    def __init__(self, queryset):
        assert isinstance(queryset, QuerySet)
        super(MongoEngineQuerysetAdapter, self).__init__(queryset)
