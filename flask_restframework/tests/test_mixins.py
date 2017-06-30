import pytest

from flask.ext.restframework.model_resource import ModelResource
from flask.ext.restframework.serializer.model_serializer import ModelSerializer
import mongoengine as m

from flask.ext.restframework.tests.compat import mock


class SimpleModel(m.Document):
    value = m.StringField()

@pytest.fixture()
def simple_model(db):
    return SimpleModel.objects.create(
        value="1"
    )

@pytest.mark.test_delete_mixin
def test_delete_mixin(simple_model):

    class S(ModelSerializer):
        class Meta:
            model = SimpleModel

    class R(ModelResource):
        serializer_class = S

        def get_queryset(self):
            return SimpleModel.objects.all()

    request = mock.Mock()

    resp = R(request).delete_object(request, simple_model.id)
    assert resp.status_code == 200
    assert resp.json == {"id": str(simple_model.id)}
