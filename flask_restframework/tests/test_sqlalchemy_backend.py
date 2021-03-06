import datetime

import pytest
from flask.ext.sqlalchemy import SQLAlchemy
import sqlalchemy as sa

from flask_restframework.model_wrapper import SqlAlchemyModelWrapper
from flask_restframework.serializer.model_serializer import ModelSerializer

db = SQLAlchemy()

class SAModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uniq = db.Column(db.String(length=100), nullable=False, unique=True)
    dt = db.Column(db.DateTime(), default=datetime.datetime.now, nullable=False)
    date = db.Column(db.Date(), default=datetime.date.today, nullable=False)
    boolean = db.Column(db.Boolean(), nullable=False)

    un1 = db.Column(db.String(), nullable=False)
    un2 = db.Column(db.String(), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("un1", "un2"),
    )


@pytest.fixture()
def sdb(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    db.init_app(app)

    SqlAlchemyModelWrapper.init(db)

    db.create_all()
    yield db
    db.drop_all()

@pytest.fixture()
def samodel(sdb):
    ins = SAModel(
        uniq="uniq",
        dt=datetime.datetime(2016, 1, 1),
        date=datetime.date(2016, 1, 1),
        boolean=False,
        un1="un1",
        un2="un2"
    )

    db.session.add(ins)
    db.session.commit()

@pytest.mark.test_unique_validation
def test_unique_validation(samodel):
    assert SAModel.query.count() == 1

    class Serializer(ModelSerializer):
        class Meta:
            model = SAModel

    s = Serializer(dict(
        uniq="uniq",
        dt="2016-01-01 00:00:00",
        date="2016-01-01",
        boolean=False,
        un1="un1",
        un2="un2"
    ))

    assert s.validate() == False
    assert s.errors == {'uniq': ['Trying to save duplicate value uniq']}

def test_serialization(samodel):
    class Serializer(ModelSerializer):
        class Meta:
            model = SAModel

    s = Serializer.from_queryset(SAModel.query)
    item = s.serialize()[0]
    assert item == dict(
        id=1,
        uniq="uniq",
        dt="2016-01-01 00:00:00",
        date="2016-01-01",
        boolean=False,
        un1="un1",
        un2="un2"
    )


@pytest.mark.test_model_serializer_creation
def test_model_serializer_creation(sdb):

    class Serializer(ModelSerializer):
        class Meta:
            model = SAModel

    s = Serializer({})

    assert s.validate() == False
    assert s.errors == {
        'date': ['Field is required'],
        'un1': ['Field is required'],
        'un2': ['Field is required'],
        'boolean': ['Field is required'],
        'dt': ['Field is required'],
        'uniq': ['Field is required']
    }

    assert SAModel.query.count() == 0

    s = Serializer({
        "un1": "1",
        "un2": "2",
        "uniq": "123",
        "boolean": "Olala",
        "date": "asdasd",
        "dt": "asdasd"
    })
    assert s.validate() == False
    assert s.errors == {'boolean': ['Boolean is required'],
                        'date': ['Incorrect DateTime string for %Y-%m-%d format'],
                        'dt': ['Incorrect DateTime string for %Y-%m-%d %H:%M:%S format']}

    s = Serializer({
        "un1": "1",
        "un2": "2",
        "uniq": "123",
        "boolean": True,
        "date": "2016-01-01",
        "dt": "2016-01-01 00:00:00"
    })
    assert s.validate() == True
    instance = s.create(s.cleaned_data).item
    assert isinstance(instance, SAModel)
    assert instance.un1 == "1"
    assert instance.un2 == "2"
    assert instance.uniq == "123"
    assert instance.boolean == True
    assert instance.date == datetime.date(2016, 1, 1)
    assert instance.dt == datetime.datetime(2016, 1, 1)
    assert instance.id == 1

