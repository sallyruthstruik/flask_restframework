import json

from flask.ext.restframework.queryset_wrapper import QuerysetWrapper
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

@pytest.mark.test_fetch_data_with_cursor
def test_fetch_data_with_cursor(app, complex_doc):
    request = mock.Mock()

    with app.test_request_context():
        resp = Resource(request).get(request)

    # data = json.loads(resp.data.decode("utf-8"))
    assert resp.json[0]["inner_list"] == [{'value': '4'}, {'value': '5'}]
    assert len(resp.json[0]["ref_list"]) == 2
    assert resp.json[0]["inner"] == {"value": "3"}



@pytest.mark.test_join_data
def test_join_data(app, complex_doc):

    class Nested(BaseSerializer):
        value = fields.StringField()

    class S(ModelSerializer):

        ref = fields.ReferenceField(
            Nested, queryset=Ref.objects.all
        )

        nested_list = fields.ListField(fields.ReferenceField(Nested, queryset=Ref.objects.all))

        class Meta:
            model = Doc
            fields = ("id", )

    data = S(QuerysetWrapper.from_queryset(Doc.objects.no_dereference())).serialize()
    assert data[0]["ref"] == {
        "value": "1"
    }

    assert data == S(QuerysetWrapper.from_queryset(Doc._get_collection().find())).serialize()

    #test with custom queryset
    class S(ModelSerializer):
        ref = fields.ReferenceField(
            Nested, queryset=lambda: Ref._get_collection().find()
        )

        nested_list = fields.ListField(fields.ReferenceField(Nested, queryset=Ref.objects.all))

        class Meta:
            model = Doc
            fields = ("id", )

    data = S(QuerysetWrapper.from_queryset(Doc.objects.no_dereference())).serialize()
    assert data[0]["ref"] == {
        "value": "1"
    }




