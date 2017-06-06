import pytest
from flask.app import Flask
from flask_mongoengine import MongoEngine
from mongoengine import fields as db
from pymongo.database import Database

from flask_restframework import fields
from flask_restframework.serializer.model_serializer import ModelSerializer

class Related(db.Document):
    value = db.StringField()

class Embedded(db.EmbeddedDocument):
    value1 = db.StringField()
    value2 = db.StringField()

class Main(db.Document):
    embedded_inner = db.EmbeddedDocumentField(Embedded)
    embedded_list_inner = db.EmbeddedDocumentListField(Embedded)

    related_inner = db.ReferenceField(Related)
    related_list_inner = db.ListField(db.ReferenceField(Related))


@pytest.fixture()
def app():
    app = Flask(__name__)
    return app

@pytest.fixture()
def db(app):
    db = MongoEngine(app, config=dict(
        MONGODB_DB="test"
    ))

    with app.app_context():
        database = db.connection.get_database("test")

        for col in database.collection_names():
            if col != "system.indexes":
                print(col)
                database.drop_collection(col)

    return db

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

    data = Serializer(Main.objects.all()).to_python()

    assert len(data) == 1
    assert data[0] == dict(
        embedded_inner={
            "value1": "1"
        },
        embedded_list_inner=[{
            "value1": "3"
        }]
    )