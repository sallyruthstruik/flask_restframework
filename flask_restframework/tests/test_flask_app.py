import base64
import datetime
import json
import unittest
from pprint import pprint

try:
    from unittest.mock import Mock, call
except ImportError:
    from mock import Mock, call

import six
from flask import jsonify
from flask.app import Flask
from flask.blueprints import Blueprint
from flask_mongoengine import MongoEngine
from flask.globals import request
from flask.helpers import url_for
from flask.views import View
from mongoengine import fields as db

from flask_restframework.authentication_backend import BaseAuthenticationBackend, SimpleBasicAuth
from flask_restframework.decorators import auth_backends
from flask_restframework.exceptions import AuthorizationError
from flask_restframework.middlewares import BaseMiddleware, AuthenticationMiddleware
from flask_restframework.validators import UniqueValidator
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
        print(data)
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

class TestMiddlewares(SimpleFlaskAppTest):

    def setUp(self):
        super(TestMiddlewares, self).setUp()
        @self.app.route("/test_middleware", methods=["GET"])
        def test_middleware():
            return "test-middleware"


    def test_authorization(self):

        class CustomAuthBackends(BaseAuthenticationBackend):
            def get_user(self, request):
                if request.args:
                    return True
                return False

        @self.app.route("/test_auth_route", methods=["GET"])
        @auth_backends(CustomAuthBackends)
        def test_auth():
            return "ok"

        self.app.config["BASIC_AUTH_LOGIN"] = "admin"
        self.app.config["BASIC_AUTH_PASSWORD"] = "1"

        @self.app.route("/test_basic", methods=["GET"])
        @auth_backends(SimpleBasicAuth)
        def test_basic():
            return "basic"


        class TestRes(BaseResource):
            authentication_backends = [CustomAuthBackends]
            def get(self, request):
                return "auth res"

        router = DefaultRouter(self.app)
        router.register("/test_auth_resource", TestRes, "test_auth_res")

        AuthenticationMiddleware.register(self.app)

        resp = self.client.get("/test_auth_route")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.data, b'Authentication fails')

        resp = self.client.get("/test_auth_route?key=value")
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get("/test_auth_resource")
        self.assertEqual(resp.status_code, 401)

        resp = self.client.get("/test_auth_resource?key=value")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, b"auth res")

        resp = self.client.get("/test_basic?k=v")
        self.assertEqual(resp.status_code, 401)

        resp = self.client.get(
            "/test_basic?k=v", headers={
                'Authorization': b'Basic '+base64.b64encode(b"admin:1")
            }
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, b"basic")

    def test_middleware_can_interrupt_execution(self):
        m = Mock()

        class Middleware1(BaseMiddleware):

            def before_request(self):
                m("before-1")
                return "INTERRUPTED", 400

            def after_request(self, response):
                m("after-1")
                return response

        class Middleware2(BaseMiddleware):
            def before_request(self):
                m("before-2")

            def after_request(self, response):
                m("after-2")
                return response

        Middleware1.register(self.app)
        Middleware2.register(self.app)

        resp = self.client.get("/test_middleware")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data, b"INTERRUPTED")
        self.assertEqual(m.call_args_list, [
            call("before-1"),
            call("after-2"),
            call("after-1")
        ])


    def test_middlewares_order(self):
        m = Mock()

        class Middleware1(BaseMiddleware):

            def before_request(self):
                m("before-1")

            def after_request(self, response):
                m("after-1")
                return response

        class Middleware2(BaseMiddleware):
            def before_request(self):
                m("before-2")

            def after_request(self, response):
                m("after-2")
                return response

        Middleware1.register(self.app)
        Middleware2.register(self.app)

        self.client.get("/test_middleware")
        self.assertEqual(m.call_args_list, [
            call("before-1"),
            call("before-2"),
            call("after-2"),
            call("after-1")
        ])


class TestModelResources(SimpleFlaskAppTest):

    def setUp(self):
        super(TestModelResources, self).setUp()

        class EmbeddedDoc(db.EmbeddedDocument):
            value = db.StringField()

        class BaseDoc(db.Document):
            inner = db.EmbeddedDocumentField(EmbeddedDoc)
            inner_list = db.EmbeddedDocumentListField(EmbeddedDoc)

            req_field = db.StringField(required=True)
            string = db.StringField()
            bool = db.BooleanField()
            integer_field = db.IntField()
            dict_f = db.DictField()

        class Serializer(ModelSerializer):
            class Meta:
                model = BaseDoc

        class R(ModelResource):
            serializer_class = Serializer

            def get_queryset(self):
                return BaseDoc.objects.all()

        BaseDoc.drop_collection()

        router = DefaultRouter(self.app)
        router.register("/test_resource", R, "test_resource")

        self.router = router
        self.BaseDoc = BaseDoc
        self.EmbeddedDoc = EmbeddedDoc
        self.Serializer = Serializer

    def test_reference_field_serialization(self):

        class Ref(db.Document):
            value = db.StringField()

        class Doc(db.Document):
            ref = db.ReferenceField(Ref)
            ref_list = db.ListField(db.ReferenceField(Ref))

        Ref.objects.delete()
        Doc.objects.delete()

        r1 = Ref.objects.create(**dict(
            value="1"
        ))
        r2 = Ref.objects.create(**dict(
            value="2"
        ))

        d = Doc.objects.create(**dict(
            ref=r1,
            ref_list=[r1, r2]
        ))

        class S(ModelSerializer):
            class Meta:
                model = Doc

        data = S(Doc.objects.all()).serialize()[0]

        self.assertEqual(data["ref"], str(r1.id))
        self.assertEqual(data["ref_list"], list(map(str, [r1.id, r2.id])))


    def test_update_embedded_doc(self):

        doc = self.BaseDoc.objects.create(
            inner={"value": "1"},
            req_field="1"
        )

        serializer = self.Serializer(dict(
            inner={"value": "2"},
            req_field="1"
        ))

        self.assertEqual(serializer.validate(), True)

        #serializer should automatically instantiate embedded doc
        self.assertTrue(isinstance(serializer.cleaned_data["inner"], self.EmbeddedDoc))

        #serializer should correctly update instance
        serializer.update(doc, serializer.cleaned_data)
        self.assertEqual(self.BaseDoc.objects.get(id=doc.id).inner.value, "2")

        #serializer should correctly validate instance
        serializer = self.Serializer(dict(
            inner={"value": 123},
            req_field="1"
        ))
        self.assertEqual(serializer.validate(), False)
        self.assertEqual(serializer.errors, {'value': ['StringField only accepts string values']})



    def test_patch_several_fields(self):

        id = self.test_creation()

        resp = self.client.patch("/test_resource/{}".format(id), data=json.dumps({
            "string": "other string",
            "bool": True
        }), content_type="application/json")

        self.assertEqual(resp.status_code, 200, resp.data)
        data = self._parse(resp.data)
        self.assertEqual(data["string"], "other string")
        self.assertEqual(data["bool"], True)
        self.assertEqual(data["inner"], {
                "value": "1"
        })
        self.assertEqual(data["req_field"], "required")

        resp = self.client.patch("/test_resource/{}".format(id), data=json.dumps({
            "string": "other string",
            "bool": "Very Bad!",
            "integer_field": "Not an int!"
        }), content_type="application/json")

        self.assertEqual(resp.status_code, 400)
        data = self._parse(resp.data)
        self.assertEqual(
            data["bool"], ["Boolean is required"]
        )
        self.assertEqual(data["integer_field"], ["Integer is required"])

    def test_creation(self):

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
            "bool": False,
            "req_field": "required",
            "dict_f": {
                "key": "value"
            }
        }

        resp = self.client.post("/test_resource", data=json.dumps(data), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        ins = self.BaseDoc.objects.first()

        self.assertEqual(ins.bool, False)
        self.assertEqual(ins.string, "string")
        self.assertEqual(ins.inner.value, "1")
        self.assertEqual(ins.inner_list[0].value, "2")
        self.assertEqual(ins.inner_list[1].value, "3")
        self.assertEqual(ins.dict_f, {"key": "value"})

        return ins.id

    def test_unique_embedded(self):

        class Emb(db.EmbeddedDocument):
            ru = db.StringField()
            en = db.StringField()

        class Col(db.Document):

            value = db.EmbeddedDocumentField(Emb, unique=True)

        Col.objects.delete()
        Col.objects.create(
            value={
                "ru": "ru",
                "en": "en"
            }
        )

        class S(ModelSerializer):
            class Meta:
                model = Col

        s = S(data=dict(value=dict(
            ru="ru",
            en="en"
        )))
        self.assertEqual(s.validate(), False)
        self.assertTrue("value" in s.errors)

        s = S(data=dict(value=dict(
            ru="ru1",
            en="en"
        )))
        self.assertEqual(s.validate(), True)

    def test_unique_validation(self):

        class UniqueCol(db.Document):

            value = db.StringField(unique=True)
            dt_value = db.DateTimeField(unique=True)
            int_value = db.IntField(unique=True)

        UniqueCol.objects.delete()

        class Serialzier(ModelSerializer):

            class Meta:
                model = UniqueCol

        class SimpleSerializer(BaseSerializer):

            value = fields.StringField(validators=[
                UniqueValidator(qs=UniqueCol.objects.all())
            ])

        instance = UniqueCol.objects.create(
            value="1",
            dt_value=datetime.datetime(2000, 1, 1),
            int_value=1
        )

        s = SimpleSerializer(data=dict(value="1"))
        self.assertEqual(s.validate(), False)
        self.assertEqual(s.errors, {'value': ['Trying to save duplicate value 1']})

        s = Serialzier(data=dict(
            value="1",
            dt_value="2000-01-01 00:00:00",
            int_value=1
        ))

        self.assertEqual(s.validate(), False)
        self.assertEqual(s.errors, {
            'dt_value': ['Trying to save duplicate value 2000-01-01 00:00:00'],
            'int_value': ['Trying to save duplicate value 1'],
            'value': ['Trying to save duplicate value 1']})

        #test update unique instance

        class R(ModelResource):
            serializer_class = Serialzier

            def get_queryset(self):
                return UniqueCol.objects.all()

        self.router.register("/test_unique_validation", R, "test_unique_validation")

        resp = self.client.put("/test_unique_validation/{}".format(instance.id), data=json.dumps({
            "value": "1",
            "dt_value": "2000-01-01 00:00:00",
            "int_value": 2
        }), content_type="application/json")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(self._parse(resp.data)["int_value"], 2)










