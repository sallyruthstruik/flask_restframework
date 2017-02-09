import datetime
import json
import unittest
from pprint import pprint

import six
from flask import jsonify
from flask.app import Flask
from flask.blueprints import Blueprint
from flask_mongoengine import MongoEngine
from flask.globals import request
from flask.helpers import url_for
from flask.views import View
from mongoengine import fields as db

from flask_restframework.validators import RegexpValidator
from flask_restframework.decorators import list_route, detail_route
from flask_restframework import fields
from flask_restframework.adapters import MongoEngineQuerysetAdapter
from flask_restframework.decorators import validate
from flask_restframework.model_resource import ModelResource
from flask_restframework.pagination import DefaultPagination
from flask_restframework.resource import BaseResource, BaseResourceMetaClass
from flask_restframework.router import DefaultRouter
from flask_restframework.serializer import BaseSerializer
from flask_restframework.serializer.model_serializer import ModelSerializer


class SimpleFlaskAppTest(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)

        self.client = self.app.test_client()

        self.db = MongoEngine(self.app)

        class TestCol(db.Document):
            value = db.StringField()

            def __unicode__(self):
                return "TestCol(value={})".format(self.value)

        TestCol.objects.delete()

        TestCol.objects.create(value="1")
        TestCol.objects.create(value="2")

        self.TestCol = TestCol

    def _parse(self, resp):
        resp = resp.decode("utf-8")
        return json.loads(resp)

    def test_validation_mongoengine_will_work_with_model_serializer(self):

        class Doc(db.Document):
            value = db.StringField(validation=RegexpValidator(r"\d+", message="Bad value").for_mongoengine())

        Doc.drop_collection()

        class Serializer(ModelSerializer):
            class Meta:
                model = Doc

        Doc.objects.create(value="123")

        s = Serializer(data={"value": "asd"})
        self.assertEqual(s.validate(), False)
        self.assertEqual(s.errors, {"value": ["Bad value"]})

    def test_resource_decorator(self):

        class S(BaseSerializer):

            field = fields.StringField(required=True)

        @self.app.route("/test", methods=["POST"])
        @validate(S)
        def resource(cleaned_data):
            return "OK"

        resp = self.client.post("/test", data=json.dumps({}), headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            json.loads(resp.data.decode("utf-8")), {'field': ['Field is required']}
        )

    def testSimpleResourceAndRouter(self):

        router = DefaultRouter(self.app)

        class Resource(BaseResource):

            def get(self, request):
                return "GET"

            def post(self, request):
                return "POST"

            def put(self, request):
                return "PUT"

            def patch(self, request):
                return "PATCH"

            def delete(self, request):
                return "DELETE"

            @list_route(methods=["GET", "POST"])
            def listroute(self, request):
                return "LIST"

            @detail_route(methods=["GET", "POST"])
            def detailroute(self, request, pk):
                return "detail"

        self.assertSetEqual(
            set(Resource.get_allowed_methods()), {"get", "post", "put", "patch", "delete"}
        )

        router.register("/test", Resource, "test")

        for method in ["get", "post", "put", "patch", "delete"]:
            resp = getattr(self.client, method)("/test")
            self.assertEqual(resp.data.decode("utf-8"), method.upper())

        for method in ["GET", "POST"]:
            resp = getattr(self.client, method.lower())("/test/listroute")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data.decode("utf-8"), "LIST")

        for method in ["GET", "POST"]:
            resp = getattr(self.client, method.lower())("/test/detailroute/1")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.data.decode("utf-8"), "detail")

            resp = self.client.get("/test/detailroute")
            self.assertEqual(resp.status_code, 404)



    def testRoutingWithBluePrint(self):

        bp = Blueprint("test", __name__)
        router = DefaultRouter(bp)

        class Res(BaseResource):
            def get(self, request):
                return "GET"

        router.register("/blabla", Res, "blabla")

        self.app.register_blueprint(bp, url_prefix="/test")

        with self.app.test_request_context():
            self.assertEqual(url_for("test.blabla"), "/test/blabla")

    def testModelResource(self):

        router = DefaultRouter(self.app)

        class Base(db.Document):

            title = db.StringField()

        class ED(db.EmbeddedDocument):

            value = db.StringField()

        class Model(db.Document):

            base = db.ReferenceField(Base)
            f1 = db.StringField()
            f2 = db.BooleanField()
            f3 = db.StringField()

            embedded = db.EmbeddedDocumentField(ED)
            listf = db.EmbeddedDocumentListField(ED)

            dictf = db.DictField()

        Model.objects.delete()

        ins = Model.objects.create(
            base=Base.objects.create(title="1"),
            f1="1",
            f2=True,
            f3="1",
            embedded={"value": "123"},
            listf=[{"value": "234"}],
            dictf={"key": "value"}
        )

        Model.objects.create(
            base=Base.objects.create(title="2"),
            f1="2",
            f2=True,
            f3="2",
            embedded={"value": "123"},
            listf=[{"value": "234"}]
        )

        class S(ModelSerializer):
            title = fields.ForeignKeyField("base__title")
            class Meta:
                model = Model
                fk_fields = ("base__title", )

        class ModelRes(ModelResource):

            serializer_class = S
            queryset = Model.objects.all()
            pagination_class = DefaultPagination

        router.register("/test", ModelRes, "modelres")
        resp = self.client.get("/test")
        self.assertEqual(resp.status_code, 200)
        data = self._parse(resp.data)
        self.assertEqual(len(data["results"]), 2)
        item = data["results"][0]
        self.assertEqual(item["dictf"], {"key": "value"})
        self.assertEqual(item["title"], "1")
        self.assertEqual(item["base__title"], "1")

        # get one object
        resp = self.client.get("/test/{}".format(ins.id))
        self.assertEqual(resp.status_code, 200)
        pprint(self._parse(resp.data))

        #test pagination
        for i in range(10):
            Model.objects.create(
                base=Base.objects.create(title="1"),
                f1="1",
                f2=True,
                f3="2"
            )

        self.assertEqual(Model.objects.count(), 12)

        resp = self.client.get("/test?page=1")
        self.assertEqual(resp.status_code, 200)
        data = self._parse(resp.data)
        results = data["results"]

        self.assertEqual(results[0]["embedded"], {"value": "123"})
        self.assertEqual(results[0]["listf"], [{"value": "234"}])

        self.assertEqual(len(data["results"]), 10)

        resp = self.client.get("/test?page=2")
        self.assertEqual(resp.status_code, 200)
        data = self._parse(resp.data)
        self.assertEqual(len(data["results"]), 2)

        resp = self.client.get("/test?page=2&page_size=5")
        self.assertEqual(resp.status_code, 200)
        data = self._parse(resp.data)
        self.assertEqual(len(data["results"]), 5)

        resp = self.client.get("/test?page=3&page_size=5")
        self.assertEqual(resp.status_code, 200)
        data = self._parse(resp.data)
        self.assertEqual(len(data["results"]), 2)


        #test put
        resp = self.client.put("/test/{}".format(ins.id), data=json.dumps({
            "f3": "OLALA"
        }), headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 200, resp.data)
        data = self._parse(resp.data)
        self.assertEqual(data["f1"], "1")
        self.assertEqual(data["f2"], True)
        self.assertEqual(data["f3"], "OLALA")


    def testMongoEngineForeignKeyField(self):

        self.assertEqual(self.TestCol.objects.count(), 2)

        class Serializer(BaseSerializer):
            fk = fields.MongoEngineIdField(self.TestCol, required=True)

        v = Serializer({"fk": "123"})
        self.assertEqual(v.validate(), False)
        self.assertEqual(v.errors, {'fk': ['Incorrect id: 123']})

        v = Serializer({"fk": str(self.TestCol.objects.first().id)})
        v.validate()
        self.assertEqual(v.errors, {})
        self.assertEqual(v.cleaned_data["fk"], self.TestCol.objects.first())

        class R(BaseResource):

            def post(self, request):
                errors, data = self.validate_request(Serializer)
                if errors:
                    return errors

                return "OK"

        self.app.add_url_rule("/api", view_func=R.as_view("test2"),
                              methods=["GET", "POST"])

        resp = self.client.post("/api", data=json.dumps({}),
                                headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data.decode("utf-8"))
        self.assertEqual(data["fk"], ['Field is required'])

    def testSerialization(self):

        class Col(db.Document):

            value = db.StringField()
            created = db.DateTimeField(default=datetime.datetime.now)

        Col.objects.delete()
        Col.objects.create(value="1")
        Col.objects.create(value="2")

        class S(BaseSerializer):

            value = fields.StringField()
            created = fields.DateTimeField(read_only=True)

        data = S(Col.objects.all()).to_python()
        self.assertEqual(len(data), 2)
        self.assertEqual(
            list(map(lambda i: i["value"], data)),
            ["1", "2"]
        )

        #test can't set read only field
        ser = S({"value": "1", "created": "2016-01-01 00:00:00"})
        ser.validate()

        self.assertTrue("created" not in ser.cleaned_data)

    def testModelSerialization(self):

        class DeepInner(db.EmbeddedDocument):
            value = db.StringField()

        class Inner(db.EmbeddedDocument):
            value = db.StringField()
            deep = db.EmbeddedDocumentField(DeepInner)

        class Col(db.Document):

            value = db.StringField()
            excluded_field = db.StringField(default="excluded")
            created = db.DateTimeField(default=datetime.datetime.now)
            inner = db.EmbeddedDocumentField(Inner)


        Col.objects.delete()
        Col.objects.create(value="1", inner={"value": "inner1", "deep": {"value": "123"}})
        Col.objects.create(value="2", inner={"value": "inner2"})

        class Serializer(ModelSerializer):

            method_field = fields.MethodField("test")

            renamed = fields.ForeignKeyField(document_fieldname="inner__deep__value")

            def test(self, doc):
                return doc.value

            class Meta:
                model = Col
                fields = ("value", "created", "method_field")
                fk_fields = ("inner__value", "inner__deep__value")

        data = Serializer(Col.objects.all()).to_python()

        for item in data:
            self.assertTrue("value" in item)
            self.assertEqual(item["value"], item["method_field"])
            self.assertTrue(type(item["created"]), datetime.datetime)
            self.assertEqual(item["renamed"], item["inner__deep__value"])

    def test_creation(self):

        class Inner(db.EmbeddedDocument):
            value = db.StringField()

        class Doc(db.Document):
            inner = db.EmbeddedDocumentField(Inner)
            inner_list = db.EmbeddedDocumentListField(Inner)

            string = db.StringField()
            bool = db.BooleanField()

        class S(ModelSerializer):
            class Meta:
                model = Doc

        class R(ModelResource):
            serializer_class = S

            def get_queryset(self):
                return Doc.objects.all()

        Doc.drop_collection()

        router = DefaultRouter(self.app)
        router.register("/test", R, "test")

        data = {
            "inner": {
                "value": "1"
            },
            "inner_list": [{
                "value": "2"
            }, {
                "value": "3"
            }],
            "string": "string",
            "bool": False
        }

        resp = self.client.post("/test", data=json.dumps(data), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        ins = Doc.objects.first()

        self.assertEqual(ins.bool, False)
        self.assertEqual(ins.string, "string")
        self.assertEqual(ins.inner.value, "1")
        self.assertEqual(ins.inner_list[0].value, "2")
        self.assertEqual(ins.inner_list[1].value, "3")







