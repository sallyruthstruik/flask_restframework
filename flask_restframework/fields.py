import datetime

from flask import json

from flask_restframework.exceptions import ValidationError
from mongoengine import fields as db

__author__ = 'stas'

class BaseField(object):
    """
    Base Field
    """

    serializer = None   #ref on serializer instance

    @classmethod
    def from_mongoengine_field(cls, mongoEngineField):
        try:
            return cls(
                required=mongoEngineField.required,
                default=mongoEngineField.default
            )
        except:
            print("ERROR")

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

    def run_validate(self, validator, value):
        """
        :type validator: flask_restframework.serializer.BaseSerializer

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
            customVal(validator, value)

        if value:
            value = self.validate(validator, value)

        return value

    def to_python(self, value):
        """For passed from Model instance value this method should return plain python object
        which will be used
        later in serialization

        :param value: value from db object
        """
        raise NotImplementedError()

    # TODO: validate MUST be implemented!
    def validate(self, validator, value):
        pass

    def get_value_from_model_object(self, doc, field):
        "returns value for fieldName field and document doc"
        try:
            return getattr(doc, field)
        except:
            print("ERR")


class StringField(BaseField):

    def to_python(self, value):
        if value:
            return str(value)

    def __init__(self, choices=None, **k):
        self.choices = choices
        super(StringField, self).__init__(**k)

    def validate(self, validator, value):
        if self.choices and value not in self.choices:
            raise ValidationError("Value should be one of {}, got {}".format(
                self.choices, value)
            )

        return value


class BooleanField(BaseField):

    def to_python(self, value):
        return value

    def validate(self, validator, value):
        if value not in [True, False]:
            raise ValidationError("Boolean is required")

        return value

class IntegerField(BaseField):

    def to_python(self, value):
        return value

# TODO: validate URL
class URLField(BaseField):

    def to_python(self, value):
        return value

    def validate(self, validator, value):
        return value

class DateTimeField(BaseField):

    def to_python(self, value):
        if value:
            return value.strftime(self._format)

    def __init__(self, format="%Y-%m-%d %H:%M:%S", **k):
        self._format = format
        super(DateTimeField, self).__init__(**k)

    def validate(self, validator, value):
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

    def validate(self, validator, value):
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
        field = self.document_fieldname or field
        parts = field.split("__")
        out = doc
        for item in parts:
            outCls = out.__class__

            if out:
                out = getattr(out, item)

                try:
                    outField = getattr(outCls, item)
                except AttributeError:
                    outField = None

        if out and outField:
            from flask_restframework.utils import mongoengine_model_meta
            return mongoengine_model_meta.FIELD_MAPPING[outField.__class__].from_mongoengine_field(
                outField).to_python(out)

        return out


class ForeignKeyField(BaseRelatedField):
    """
    Fields represent ForeignKeyRelation which can be getted with __ notation.
    It is only READ field, but it subclasses may be also changeable.

    Goal of this field - to allow get inner/related data with __ notation.
    """
    def __init__(self, **k):
        k["read_only"] = True
        super(ForeignKeyField, self).__init__(**k)

    def to_python(self, value):
        if isinstance(value, db.Document):
            return str(value.id)
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
        if isinstance(value, db.Document):
            return str(value.id)
        return value

    def validate(self, validator, value):
        instance = self.related_model.objects.filter(id=value).first()

        if not instance:
            raise ValidationError("Object with id {} not found".format(value))

        return instance


class ListField(BaseField):

    def to_python(self, value):
        embedded = EmbeddedField()
        return list(map(embedded.to_python, value))

    def validate(self, validator, value):
        if not isinstance(value, list):
            raise ValidationError("Array is required")

        return value


class EmbeddedField(BaseRelatedField):

    def __init__(self, read_only=False, **k):
        super(EmbeddedField, self).__init__(**k)

        self._read_only = read_only

    def to_python(self, value):
        # TODO: Use nested serializer

        if value and isinstance(value, db.EmbeddedDocument):
            return json.loads(value.to_json())

        return value

    def validate(self, validator, value):
        if not isinstance(value, dict):
            raise ValidationError("Object is required")

        return value


class DictField(BaseField):

    def to_python(self, value):
        if value:
            try:
                return dict(value)
            except:
                return value

        return value
