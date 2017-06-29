import pytest
from flask.app import Flask
from flask.ext.mongoengine import MongoEngine


@pytest.fixture()
def app():
    app = Flask(__name__)

    with app.app_context():
        yield app

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