import datetime
import unittest

from flask_restframework.validators import RegexpValidator
from flask_restframework.serializer.model_serializer import ModelSerializer
from flask_restframework import fields
from flask_restframework.serializer import BaseSerializer
from mongoengine import fields as db

class TestFieldsValidation(unittest.TestCase):

    def setUp(self):
        pass


    def test_model_serializer_required(self):

        class Base(db.Document):
            value = db.StringField()

        class Doc(db.Document):
            value = db.StringField(required=True)
            read_only = db.StringField()
            base = db.ReferenceField(Base, required=True)

        class S(ModelSerializer):

            ro = db.StringField()

            class Meta:
                model = Doc
                read_only = ("read_only", )

        serializer = S({})
        self.assertEqual(serializer.validate(), False)
        self.assertTrue("read_only" not in serializer._get_writable_fields())
        self.assertEqual(serializer.errors, {
            "value": ['Field is required'],
            "base": ['Field is required']
        })


    def testSerializerWithAdditionalData(self):
        class TestSerializer(BaseSerializer):

            field = fields.StringField(required=True)

            class Meta:
                allow_additional_fields = True

        v = TestSerializer({"field": "value", "additional": "value2"})
        self.assertEqual(v.validate(), True)
        self.assertEqual(v.cleaned_data["additional"], "value2")

    def test_fields_validation(self):

        class TestValidation(BaseSerializer):

            choices = fields.StringField(choices=["1", "2", "3"], required=True)
            not_req = fields.StringField()
            boolean = fields.BooleanField(required=True)
            boolean_not_req = fields.BooleanField()
            string_def = fields.StringField(default="", required=True)
            dt = fields.DateTimeField()

        v = TestValidation({})
        self.assertEqual(v.validate(), False)
        self.assertEqual(v.errors, {
            "choices": ["Field is required"],
            "boolean": ["Field is required"]
        })

        v = TestValidation({"choices": "bad", "boolean": "bad", "boolean_not_req": "bad"})
        self.assertEqual(v.validate(), False)
        self.assertEqual(v.errors, {
            "boolean": ["Boolean is required"],
            "boolean_not_req": ["Boolean is required"],
            'choices': ["Value should be one of ['1', '2', '3'], got bad"]
        })

        v = TestValidation({"choices": "1", "boolean": False})
        v.validate()
        self.assertEqual(v.cleaned_data["string_def"], "")

        v = TestValidation({"choices": "1", "boolean": False, "dt": "2016-01-01 00:00:00"})
        self.assertEqual(v.validate(), True)
        self.assertEqual(v.cleaned_data["dt"], datetime.datetime(2016, 1, 1))

