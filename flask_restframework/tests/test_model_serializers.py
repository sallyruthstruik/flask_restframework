import pytest
from flask.app import Flask
from flask_mongoengine import MongoEngine
from mongoengine import fields as mfields
from pymongo.database import Database

from flask_restframework.queryset_wrapper import QuerysetWrapper
from flask_restframework import fields
from flask_restframework.serializer.model_serializer import ModelSerializer

class Related(mfields.Document):
    value = mfields.StringField()

class Embedded(mfields.EmbeddedDocument):
    value1 = mfields.StringField()
    value2 = mfields.StringField()

class Main(mfields.Document):
    embedded_inner = mfields.EmbeddedDocumentField(Embedded)
    embedded_list_inner = mfields.EmbeddedDocumentListField(Embedded)

    related_inner = mfields.ReferenceField(Related)
    related_list_inner = mfields.ListField(mfields.ReferenceField(Related))

@pytest.fixture()
def main_record(db):
    rel1 = Related.objects.create(
        value="1"
    )
    rel2 = Related.objects.create(
        value="2"
    )
    return Main.objects.create(
        embedded_inner={
            "value1": "1",
            "value2": "2"
        },
        embedded_list_inner=[{
            "value1": "3",
            "value2": "4"
        }],
        related_inner=rel1,
        related_list_inner=[rel1, rel2]
    )

class E1(mfields.EmbeddedDocument):
    value = mfields.StringField()

class E2(mfields.EmbeddedDocument):
    e1 = mfields.EmbeddedDocumentField(E1)

class Doc(mfields.Document):
    e2 = mfields.EmbeddedDocumentField(E2)

@pytest.fixture()
def nested(db):
    return Doc.objects.create(
        e2=E2(
            e1=E1(
                value="test"
            )
        )
    )

@pytest.mark.test_not_full_fk_serialization
def test_not_full_fk_serialization(nested):

    class S(ModelSerializer):
        field = fields.ForeignKeyField("e2__e1")

        class Meta:
            model = Doc
            fields = ("field", )

    out = S(QuerysetWrapper.from_queryset(Doc.objects.all())).serialize()
    assert out == [{
        "field": {
            "value": "test"
        }
    }]

@pytest.mark.test_embedded_inner_serialization
def test_embedded_inner_serialization(main_record):
    class InnerSerializer(ModelSerializer):
        class Meta:
            model = Embedded
            fields = ("value1",)

    class Serializer(ModelSerializer):
        embedded_inner = fields.EmbeddedField(
            InnerSerializer
        )
        embedded_list_inner = fields.ListField(
            fields.EmbeddedField(InnerSerializer)
        )

        class Meta:
            model = Main
            fields = ("embedded_inner", "embedded_list_inner")

    data = Serializer(QuerysetWrapper.from_queryset(Main.objects.all())).serialize()

    assert len(data) == 1
    assert data[0] == dict(
        embedded_inner={
            "value1": "1"
        },
        embedded_list_inner=[{
            "value1": "3"
        }]
    )

@pytest.mark.test_reference_serialization
def test_reference_serialization(main_record):

    class Serializer(ModelSerializer):
        class Meta:
            model = Main

    d = Serializer.from_queryset(Main.objects.all()).serialize()
    assert d[0]["related_inner"] == str(main_record.related_inner.id)
    assert d[0]["related_list_inner"] == list(map(lambda i: str(i.id), main_record.related_list_inner))
