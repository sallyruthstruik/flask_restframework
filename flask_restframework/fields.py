import datetime
import decimal

from bson.dbref import DBRef
from flask import json

from flask_restframework.utils.util import wrap_mongoengine_errors
from flask_restframework.validators import UniqueValidator
from flask_restframework.validators import BaseValidator
from flask_restframework.exceptions import ValidationError
from mongoengine import fields as db

__author__ = 'stas'


class BaseField(object):
    """
    Base Field
    """

    serializer = None   #ref on serializer instance
    fieldname = None    #string name of the field

    @classmethod
    def _update_init_args(cls, args, kwargs, mongoEngineField):
        """
        Allows to simple override instantiation process from mongoEngineField.
        See example in EmbeddedField
        """
        return args, kwargs

    @classmethod
    def from_mongoengine_field(cls, mongoEngineField):
        validators = []
        if mongoEngineField.validation:

            if hasattr(mongoEngineField.validation, "original_validator"):
                validator_adapter = mongoEngineField.validation.original_validator
            else:
                validator_adapter = lambda serializer, value: mongoEngineField.validation(value)

            validators = [validator_adapter]

        if mongoEngineField.unique:
            model = mongoEngineField.owner_document
            validators.append(UniqueValidator(qs=model.objects.all()))

        args, kwargs = tuple(), dict(
            required=mongoEngineField.required,
            default=mongoEngineField.default,
            validators=validators
        )

        args, kwargs = cls._update_init_args(args, kwargs, mongoEngineField)

        return cls(*args, **kwargs)

    def __init__(
            self,
            required=False,
            blank=True,
            default=None,
            validators=None,
            read_only=False
    ):
        """
        :param required: if True then field should strictly present in data (but may be null)
        :param blank: if False then field should not be null or empty ("" for strings and so on)
        :param default: Default value for this field.
        """

        self._required = required
        self._blank = blank
        self._validators = validators or []
        self._default = default
        self._read_only = read_only

    def run_validate(self, serializer, value):
        """
        :type serializer: flask_restframework.serializer.BaseSerializer

        Should return value which will be passed in BaseValidator.cleaned_data
        """

        if self._read_only:
            raise ValueError("You can't run validation on read only field!")

        if value is None and self._default is not None:
            value = self._default

            # Allow to pass lambdas as default (as is in mongoengine)
            if callable(value):
                value = value()

        if value is None:
            if self._required:
                raise ValidationError("Field is required")
            else:
                return value

        for customVal in self._validators:
            customVal(self, value)

        if value is not None:
            value = self.validate(value)

        return value

    def to_python(self, value):
        """For passed from Model instance value this method should return plain python object
        which will be used
        later in serialization

        :param value: value from db object
        """
        raise NotImplementedError()

    def to_json(self, value):
        """
        Takes Python representation of value and should return JSON-compatible object

        Usually returns .to_python
        """
        return value

    # TODO: validate MUST be implemented!
    def validate(self, value):
        pass

    def get_value_from_model_object(self, doc, field):
        "returns value for fieldName field and document doc"
        return getattr(doc, field)



class StringField(BaseField):

    def to_python(self, value):
        if value:
            return str(value)

    def __init__(self, choices=None, **k):
        self.choices = choices
        super(StringField, self).__init__(**k)

    def validate(self, value):
        if self.choices and value not in self.choices:
            raise ValidationError("Value should be one of {}, got {}".format(
                self.choices, value)
            )

        return value


class BooleanField(BaseField):

    def to_python(self, value):
        return value

    def validate(self, value):
        if value not in [True, False]:
            raise ValidationError("Boolean is required")

        return value

class IntegerField(BaseField):

    def to_python(self, value):
        return value

    def validate(self, value):
        try:
            return int(value)
        except:
            raise ValidationError("Integer is required")


class DecimalField(BaseField):

    def to_python(self, value):
        return value

    def to_json(self, value):
        if value:
            return str(value)

    def validate(self, value):
        if value:
            try:
                return decimal.Decimal(value)
            except:
                raise ValidationError('Decimal is required')


# TODO: validate URL
class URLField(BaseField):

    def to_python(self, value):
        return value

    def validate(self, value):
        return value

class DateTimeField(BaseField):

    def to_python(self, value):
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime(self._format)

        return value

    def __init__(self, format="%Y-%m-%d %H:%M:%S", **k):
        self._format = format
        super(DateTimeField, self).__init__(**k)

    def validate(self, value):
        try:
            return datetime.datetime.strptime(value, self._format)
        except:
            raise ValidationError("Incorrect DateTime string for {} format".format(self._format))


class MongoEngineIdField(BaseField):

    def to_python(self, value):
        return str(value.id)

    def __init__(self, documentCls, **k):
        self._documentCls = documentCls
        super(MongoEngineIdField, self).__init__(**k)

    def validate(self, value):
        ids = {
            str(item.id): item
            for item in self._documentCls.objects.all()
        }

        if value not in ids:
            raise ValidationError("Incorrect id: {}".format(value))

        return ids[value]


class MethodField(BaseField):

    def __init__(self, methodName):
        super(MethodField, self).__init__(read_only=True)
        self.methodName = methodName

    def get_value_from_model_object(self, doc, field):
        return getattr(self.serializer, self.methodName)(doc)

    def to_python(self, value):
        return value


class BaseRelatedField(BaseField):

    def __init__(self, document_fieldname=None, **k):
        super(BaseRelatedField, self).__init__(**k)
        self.document_fieldname = document_fieldname


    def get_value_from_model_object(self, doc, field):
        """
        Gets value from doc according to field name. FIeld name can contain __ notation.
        If defined self.document_fieldname, it will be used instead of field.
        Because we can use aliases like::

            alias = field.ForeignKeyField("some__real__path")

        :param doc: Document
        :param field: string fieldname
        """
        out = doc

        try:
            for part in (self.document_fieldname or field).split("__"):
                out = getattr(out, part)
        except AttributeError:
            return None

        return out

class ForeignKeyField(BaseRelatedField):
    """
    Fields represent ForeignKeyRelation which can be getted with __ notation.
    It is only READ field, but it subclasses may be also changeable.

    Goal of this field - to allow get inner/related data with __ notation.
    """
    def __init__(self, document_fieldname, **k):
        k["read_only"] = True
        k["document_fieldname"] = document_fieldname
        super(ForeignKeyField, self).__init__(**k)

    def to_python(self, value):
        if isinstance(value, db.Document):
            return str(value.id)
        return value

    def to_json(self, value):
        if isinstance(value, db.EmbeddedDocument):
            return dict(value.to_mongo())
        return value

class PrimaryKeyRelatedField(BaseRelatedField):

    @classmethod
    def from_mongoengine_field(cls, mongoEngineField):
        return cls(
            related_model=mongoEngineField.document_type,
            required=mongoEngineField.required,
            default=mongoEngineField.default
        )

    def __init__(self, related_model, **k):
        super(PrimaryKeyRelatedField, self).__init__(**k)
        self.related_model = related_model

    def to_python(self, value):
        if isinstance(value, (db.Document, DBRef)):
            return str(value.id)
        return value

    def to_json(self, value):
        return value

    def validate(self, value):
        instance = self.related_model.objects.filter(id=value).first()

        if not instance:
            raise ValidationError("Object with id {} not found".format(value))

        return instance


class ListField(BaseField):

    nestedField = None  #type: BaseField

    @classmethod
    def _update_init_args(cls, args, kwargs, mongoEngineField):
        from flask_restframework.utils.mongoengine_model_meta import FIELD_MAPPING

        # Create serializer field for inner mongoengine field
        innerField = FIELD_MAPPING[mongoEngineField.field.__class__].from_mongoengine_field(
            mongoEngineField.field
        )

        return (innerField,), kwargs

    def __init__(self, innerField, **k):
        super(ListField, self).__init__(**k)
        self.inner_serializer = innerField  # type: BaseField

    def to_python(self, value):
        if value:
            return list(map(self.inner_serializer.to_python, value))

    def validate(self, value):
        if not isinstance(value, list):
            raise ValidationError("Array is required")

        return list(map(self.inner_serializer.validate, value))


class EmbeddedField(BaseRelatedField):

    @classmethod
    def _update_init_args(cls, args, kwargs, mongoEngineField):
        from flask_restframework.serializer.model_serializer import ModelSerializer

        class InnerSerializer(ModelSerializer):
            class Meta:
                model = mongoEngineField.document_type

        return (InnerSerializer, ), kwargs

    def __init__(self, inner_serializer=None, read_only=False, **k):
        super(EmbeddedField, self).__init__(**k)

        self.inner_serializer = inner_serializer    #type: ModelSerializer
        self._read_only = read_only

    def to_python(self, value):
        if value:
            return self.inner_serializer(value).to_python()

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Object is required")

        if not self.inner_serializer(value).validate():
            raise ValidationError("Incorrect value passed to inner field: {}".format(value))

        return self.inner_serializer.Meta.model(**value)


class DictField(BaseField):

    def to_python(self, value):
        if value:
            try:
                return dict(value)
            except:
                return value

        return value

    def validate(self, value):

        if not isinstance(value, dict):
            raise ValidationError("Dict is required!")

        return value


class SequenceField(BaseField):

    def to_python(self, value):
        print(value, type(value))
        return value


