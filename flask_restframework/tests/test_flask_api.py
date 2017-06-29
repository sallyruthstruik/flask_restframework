import datetime
import json

import mongoengine as m
import pytest
from flask.app import Flask

from flask.ext.restframework.model_resource import ModelResource
from flask.ext.restframework.router import DefaultRouter
from flask.ext.restframework.serializer.model_serializer import ModelSerializer

class Model(m.Document):
    created = m.DateTimeField(default=datetime.datetime.now)
    value = m.StringField()

@pytest.mark.test_ignore_created_fields
def test_ignore_excluded_fields():

    class S(ModelSerializer):
        class Meta:
            model = Model
            excluded = ("created", )

    assert sorted(S([]).get_fields().keys()) == ["id", "value"]


def test_ignore_created_fields(app, db):

    class S(ModelSerializer):
        class Meta:
            model = Model
            excluded = ("created", )

    class R(ModelResource):
        serializer_class = S

        def get_queryset(self):
            return Model.objects.all()

    router = DefaultRouter(app)
    router.register("/test", R, "test")
    assert isinstance(app, Flask)

    resp = app.test_client().post("/test", data=json.dumps({
        "value": "1"
    }), headers={"Content-Type": "application/json"})
    assert resp.status_code == 200, resp.data.decode("utf-8")
