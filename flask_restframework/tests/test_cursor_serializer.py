from flask.ext.restframework.tests.compat import mock

import mongoengine as m
import pytest

from flask_restframework.model_cursor_resource import GenericCursorResource
from flask_restframework.model_resource import ModelResource
from flask_restframework.serializer.base_serializer import BaseSerializer
from flask_restframework import fields
from flask_restframework.serializer.model_serializer import ModelSerializer


class Inner(m.EmbeddedDocument):
    value = m.StringField()

class Ref(m.Document):
    value = m.StringField()

class Doc(m.Document):
    ref = m.ReferenceField(Ref)
    ref_list = m.ListField(m.ReferenceField(Ref))
    inner = m.EmbeddedDocumentField(Inner)
    inner_list = m.EmbeddedDocumentListField(Inner)

    value = m.StringField()


@pytest.fixture
def complex_doc(db):
    return Doc.objects.create(
        ref=Ref.objects.create(
            value="1"
        ),
        ref_list=[
            Ref.objects.create(
                value="1"
            ),
            Ref.objects.create(
                value="2"
            )
        ],
        inner=Inner(
            value="3"
        ),
        inner_list=[
            Inner(value="4"),
            Inner(value="5")
        ]
    )

class Serializer(ModelSerializer):
    class Meta:
        model = Doc

class Resource(ModelResource):
    serializer_class = Serializer
    def get_queryset(self):
        return Doc._get_collection().find()

def test_fetch_data_with_cursor(complex_doc):
    request = mock.Mock()

    resp = Resource(request).get(request)

    assert resp.json[0]["inner_list"] == [{'value': '4'}, {'value': '5'}]
    assert len(resp.json[0]["ref_list"]) == 2
    assert resp.json[0]["inner"] == {"value": "3"}









