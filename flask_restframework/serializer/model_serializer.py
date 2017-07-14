#coding: utf8
import six
from mongoengine.document import Document

from flask_restframework.model_wrapper import BaseModelWrapper, BaseFieldWrapper
from flask_restframework.queryset_wrapper import InstanceWrapper, MongoInstanceWrapper
from flask_restframework.serializer.base_serializer import BaseSerializer, _BaseSerializerMetaClass


from ..utils import mongoengine_model_meta as model_meta

class _ModelSerializerMetaclass(_BaseSerializerMetaClass):
    field_mapping = model_meta.FIELD_MAPPING

    @classmethod
    def _get_declared_fields(cls, name, bases, attrs):
        declared = _BaseSerializerMetaClass._get_declared_fields(name, bases, attrs)

        if name == "ModelSerializer":
            return declared

        # if declared Meta.fields, update it from declared only fields
        if "Meta" in attrs:
            if hasattr(attrs["Meta"], "fields"):
                attrs["Meta"].fields = tuple(set(attrs["Meta"].fields).union(declared.keys()))

        try:
            model = BaseModelWrapper.fromModel(attrs["Meta"].model)
        except AttributeError:
            raise TypeError("You should define Meta class with model attribute")

        fieldsFromModel = {}
        assert isinstance(model, BaseModelWrapper)

        for key, wrappedField in model.get_fields().items():
            assert isinstance(wrappedField, BaseFieldWrapper)

            #TODO: сделать проверку
            # if fieldCls not in cls.field_mapping:
            #     raise ValueError("No mapping for field {}".format(fieldCls))

            fieldsFromModel[key] = wrappedField.get_serializer_field(key)

        fieldsFromModel.update(declared)

        return fieldsFromModel


@six.add_metaclass(_ModelSerializerMetaclass)
class ModelSerializer(BaseSerializer):
    """
    Generic serializer for mongoengine models.
    You can use it in this way:

        >>> class Col(db.Document):
        >>>     value = db.StringField()
        >>>     created = db.DateTimeField(default=datetime.datetime.now)
        >>>
        >>> class S(BaseSerializer):
        >>>     class Meta:
        >>>         model = Col
        >>>
        >>> data = S(Col.objects.all()).serialize()

    """

    def get_model(self):
        #type: ()->BaseModelWrapper
        """
        Returns BaseModelWrapper for serializer-defined model.
        """

        try:
            return BaseModelWrapper.fromModel(self.Meta.model)
        except:
            raise ValueError("You should specify Meta class with model attribute")

    def create(self, validated_data):
        "Performs create instance. Returns wrapped model intance"
        return InstanceWrapper.from_instance(self.get_model().create(**validated_data))

    def update(self, instance, validated_data):
        #type: (InstanceWrapper, dict)->InstanceWrapper
        "Performs update for instance. Returns wrapped instance with updated fields"

        assert isinstance(instance, InstanceWrapper)
        #don't update id of document
        validated_data.pop("id", None)

        instance.update(validated_data)

        return instance







