import datetime

import pytest
from flask.ext.sqlalchemy import SQLAlchemy
import sqlalchemy as sa

from flask.ext.restframework.serializer.model_serializer import ModelSerializer

db = SQLAlchemy()

class SAModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uniq = db.Column(db.String(length=100), nullable=False, unique=True)
    dt = db.Column(db.DateTime(), default=datetime.datetime.now)
    date = db.Column(db.Date(), default=datetime.date.today)
    boolean = db.Column(db.Boolean())

    un1 = db.Column(db.String(), nullable=False)
    un2 = db.Column(db.String(), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("un1", "un2"), 
    )


@pytest.fixture()
def sdb(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db.init_app(app)
    db.create_all()
    yield db
    db.drop_all()

@pytest.mark.test_model_serializer_creation
def test_model_serializer_creation():

    class Serializer(ModelSerializer):
        class Meta:
            model = SAModel()

    s = Serializer({})
    assert s.validate() == False
    assert s.errors == {}