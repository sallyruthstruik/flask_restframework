from flask.app import Flask
from flask.ext.mongoengine import MongoEngine

from flask.ext.restframework.model_resource import ModelResource
from flask.ext.restframework.router import DefaultRouter
from flask_restframework import fields, BaseSerializer, ModelSerializer

app = Flask(__name__)

db = MongoEngine(app, config={
    "MONGODB_DB": "todo"
})

from mongoengine import fields as dbfields

class ToDo(dbfields.EmbeddedDocument):
    title = dbfields.StringField(required=True)
    body = dbfields.StringField(required=True)
    is_done = dbfields.BooleanField(default=False)


class ToDoList(dbfields.Document):
    title = dbfields.StringField(required=True)

    # Use embedded field for todos. You can also use ReferenceField
    todos = dbfields.EmbeddedDocumentListField(ToDo)

class ToDoListSerializer(ModelSerializer):
    class Meta:
        model = ToDoList


class ToDoListResource(ModelResource):
    queryset = ToDoList.objects.all()
    serializer_class = ToDoListSerializer


router = DefaultRouter(app)
router.register("/todolist", ToDoListResource, "todolist")

if __name__ == "__main__":
    app.run(port=3000)