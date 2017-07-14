"""
This module represents abstraction layer between ORM models and serializers.
This wrappers are used by ModelSerializer class.
"""
import mongoengine
import six
from flask.ext.sqlalchemy import Model, SQLAlchemy
from flask.globals import current_app

from flask_restframework.fields import EmbeddedField
from flask_restframework.queryset_wrapper import InstanceWrapper
from flask_restframework.validators import UniqueValidator
from flask_restframework.fields import BaseField
from flask_restframework.utils import mongoengine_model_meta
import sqlalchemy as sa
from flask_restframework import fields

class BaseModelWrapper(object):
    """
    Wraps model class and provide interface for:

    * Getting fields
    * Getting constraings
    * Creating instances

    and so on
    """

    def __init__(self, modelClass):
        self.modelClass = modelClass

    @classmethod
    def fromModel(cls, modelClass):
        if issubclass(modelClass, (mongoengine.Document, mongoengine.EmbeddedDocument)):
            return MongoEngineModelWrapper(modelClass)
        elif issubclass(modelClass, Model):
            return SqlAlchemyModelWrapper(modelClass)
        raise TypeError("Bad model class {}".format(modelClass))

    def get_fields(self):
        # type: ()->dict[str, BaseFieldWrapper]
        """
        Should return dict[str, FieldWrapper] of current model
        """
        raise NotImplementedError

    def create(self, **attrs):
        #type: ()->InstanceWrapper
        """
        Should create new instance from attrs and return InstanceWrapper
        :param attrs:
        :return:
        """
        raise NotImplementedError



class BaseFieldWrapper(object):
    """
    Wrapper for model Field. It can be mongoengine field, or sa column or so on.
    """
    field_mapping = mongoengine_model_meta.FIELD_MAPPING

    def __init__(self, field, modelClass):
        self.field = field
        self.model = modelClass

    def get_serializer_field(self, key):
        """
        Should initialize and return serializer field for self.field.
        """
        raise NotImplementedError



class MongoEngineFieldWrapper(BaseFieldWrapper):
    """Wrapper for mongoengine field"""
    def get_serializer_field(self, key):
        try:
            serializerFieldCls = self.field_mapping[self.field.__class__]
        except KeyError:
            raise TypeError("Serializer field for type {} not found! Declare in in FIELD_MAPPING".format(self.field.__class__))

        validators = []
        if hasattr(self.field, "validation") and self.field.validation:

            if hasattr(self.field.validation, "original_validator"):
                validator_adapter = self.field.validation.original_validator
            else:
                validator_adapter = lambda serializer, value: self.field.validation(value)

            validators = [validator_adapter]

        if hasattr(self.field, "unique") and self.field.unique:
            model = self.field.owner_document
            validators.append(UniqueValidator(qs=lambda: model.objects.all()))

        kwargs = dict(
            required=getattr(self.field, "required", False),
            default=getattr(self.field, "default", None),
            validators=validators
        )

        if issubclass(serializerFieldCls, fields.ListField):
            kwargs["innerField"] = MongoEngineFieldWrapper(self.field.field, self.model).get_serializer_field(None)

        if issubclass(serializerFieldCls, fields.PrimaryKeyRelatedField):
            related_model = self.field.document_type
            kwargs["related_model"] = related_model

        if issubclass(serializerFieldCls, EmbeddedField):
            from flask_restframework.serializer.model_serializer import ModelSerializer
            class InnerSerializer(ModelSerializer):
                class Meta:
                    model = self.field.document_type

            kwargs["inner_serializer"] = InnerSerializer


        return serializerFieldCls(
            **kwargs
        )


class SqlAlchemyFieldWrapper(BaseFieldWrapper):
    """Wrapper for sqlalchemy field"""
    MAPPING = {
        sa.String: fields.StringField,
        sa.Integer: fields.IntegerField,
        sa.DateTime: fields.DateTimeField,
        sa.Date: fields.DateField,
        sa.Boolean: fields.BooleanField
    }

    def get_serializer_field(self, key):
        try:
            serializerFieldCls = self.MAPPING[self.field.type.__class__]
        except KeyError:
            raise TypeError(
                "Serializer field for type {} not found! Declare in in FIELD_MAPPING".format(self.field.type.__class__)
            )

        assert issubclass(serializerFieldCls, BaseField)

        validators = []
        if self.field.unique:
            validators.append(UniqueValidator(self.model.query))

        return serializerFieldCls(
            blank=self.field.nullable,
            required=not self.field.nullable,
            read_only=self.field.primary_key,
            validators=validators
        )


class MongoEngineModelWrapper(BaseModelWrapper):
    """Wrapper for mongoengine model"""
    def create(self, **attrs):
        return self.modelClass.objects.create(**attrs)

    def get_fields(self):
        out = {}
        for key, value in six.iteritems(self.modelClass._fields):
            out[key] = MongoEngineFieldWrapper(value, self.modelClass)

        return out


class SqlAlchemyModelWrapper(BaseModelWrapper):
    """Wrapper for sqlalchemt model"""
    db = None   #type: SQLAlchemy

    @classmethod
    def init(cls, db):
        cls.db = db

    def create(self, **attrs):
        instance = self.modelClass(**attrs)

        self.db.session.add(instance)
        self.db.session.commit()

        return instance

    def get_fields(self):
        # type: ()->dict[str, BaseFieldWrapper]
        return {
            key: SqlAlchemyFieldWrapper(value, self.modelClass)
            for key, value in self.modelClass.__table__.columns.items()
        }

