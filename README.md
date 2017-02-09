# Django Rest Framework analog for Flask+Mongoengine

[![Build Status](https://travis-ci.org/sallyruthstruik/flask_restframework.svg?branch=master)](https://travis-ci.org/sallyruthstruik/flask_restframework)
[![codecov](https://codecov.io/gh/sallyruthstruik/flask_restframework/branch/master/graph/badge.svg)](https://codecov.io/gh/sallyruthstruik/flask_restframework)
[![PyPI version](https://badge.fury.io/py/flask_restframework.svg)](https://badge.fury.io/py/flask_restframework)

Minimalistic and usage-easy RESTful framework for Flask. Like Django Rest Framework for Flask

This project allows you to write serializers/model serializers and REST resources easily.
This project interface was inspired by Django-rest-framework (https://github.com/tomchristie/django-rest-framework)


## Installation

For installation run:
`pip install flask_restframework`

Example of usage you can see here: https://github.com/sallyruthstruik/angular2_logviewer/tree/master/server

Simple example:
```python

api = Blueprint("api", __name__)
router = DefaultRouter(api)

class LogsSerializer(ModelSerializer):
    class Meta:
        model = Logs



class LogsResource(DistinctValuesMixin,
                   ModelResource):

    serializer_class = LogsSerializer
    queryset = Logs.objects.all()
    distinct_fields = ["request_id", "level", "host", "logger_name"]
    update_json_filter = update_json_filter #allows to filter with ?json_filters={...}
    ordering = ("-@timestamp", )  #default ordering

```


