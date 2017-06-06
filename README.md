# Django Rest Framework analog for Flask+Mongoengine

[![Build Status](https://travis-ci.org/sallyruthstruik/flask_restframework.svg?branch=master)](https://travis-ci.org/sallyruthstruik/flask_restframework)
[![codecov](https://codecov.io/gh/sallyruthstruik/flask_restframework/branch/master/graph/badge.svg)](https://codecov.io/gh/sallyruthstruik/flask_restframework)
[![PyPI version](https://badge.fury.io/py/flask_restframework.svg)](https://badge.fury.io/py/flask_restframework)

Minimalistic and usage-easy RESTful framework for Flask. Like Django Rest Framework for Flask

This project allows you to write serializers/model serializers and REST resources easily.
This project interface was inspired by Django-rest-framework (https://github.com/tomchristie/django-rest-framework)


## Installation

For installation run:
`pip install flask_restframework`

## ToDo app example

Full code you can find in examples/todo.py

Shows functionality of using:

* ModelSerializer
* ModelResource
* Filtering

Firstly, create Flask app and MongoEngine binding:

```python
from flask.app import Flask
from flask.ext.mongoengine import MongoEngine

app = Flask(__name__)

db = MongoEngine(app, config={
    "MONGODB_DB": "todo"
})
```

Next, we create 2 models - ToDo represents one todo item and todoList.
Each todoList can contain several ToDo items:

```python
from mongoengine import fields as dbfields

class ToDo(dbfields.EmbeddedDocument):
    title = dbfields.StringField(required=True)
    body = dbfields.StringField(required=True)
    is_done = dbfields.BooleanField(default=False)


class ToDoList(dbfields.Document):
    title = dbfields.StringField(required=True)

    # Use embedded field for todos. You can also use ReferenceField
    todos = dbfields.EmbeddedDocumentListField(ToDo)
```

### Serializers

For serializing outcoming and parsing incoming data serializers are used.
The simplest way to create serializer for model is to use ModelSerializer:

```python
from flask_restframework import fields, BaseSerializer, ModelSerializer

class ToDoListSerializer(ModelSerializer):
    class Meta:
        model = ToDoList
```

By default it will serialize all fields of model.
You can manage fields you want to serialize in:

* Meta.fields
* Meta.exclude_fields
* Meta.readonly_fields

### Resources

The last step is to create resources and bind them to app:
```python

class ToDoListResource(ModelResource):
    queryset = ToDoList.objects.all()
    serializer_class = ToDoListSerializer

```

Register resource with router and start the app:

```python

router = DefaultRouter(app)
router.register("/todolist", ToDoListResource, "todolist")

if __name__ == "__main__":
    app.run(port=3000)

```


### Server query examples

First, let's create new todolist with bad body:
```
POST /todolist
{}

Response:
{
  "title": [
    "Field is required"
  ]
}
```

Create normal todo:
```
POST /todolist
{
	"title": "Main list", 
	"todos": [{
		"title": "TodoSample", 
		"body": "Do something"
	}]
}

Response:
{
  "id": "59370a0c32105b538798e200", 
  "title": "Main list", 
  "todos": [
    {
      "body": "Do something", 
      "is_done": false, 
      "title": "TodoSample"
    }
  ]
}
```

Update todo, set is_done:
```
PUT /todolist/59370a0c32105b538798e200
{
	"title": "Main list", 
	"todos": [{
		"title": "TodoSample", 
		"body": "Do something", 
		"is_done": true
	}]
}

Response: 
{
  "id": "59370a0c32105b538798e200", 
  "title": "Main list", 
  "todos": [
    {
      "body": "Do something", 
      "is_done": true, 
      "title": "TodoSample"
    }
  ]
}
```

## More functionality


Let's add bit more functionality: