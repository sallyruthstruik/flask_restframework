import six
from mongoengine.document import Document

from flask.ext.restframework.queryset_wrapper import InstanceWrapper, MongoInstanceWrapper
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
            model = attrs["Meta"].model
        except:
            raise TypeError("You should define Meta class with model attribute")

        fieldsFromModel = {}

        for key, fieldCls in six.iteritems(model_meta.get_fields(model)):
            if fieldCls not in cls.field_mapping:
                raise ValueError("No mapping for field {}".format(fieldCls))

            fieldsFromModel[key] = cls.field_mapping[fieldCls].from_mongoengine_field(
                model_meta.get_field(model, key)
            )

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
        try:
            return self.Meta.model
        except:
            raise ValueError("You should specify Meta class with model attribute")

    def create(self, validated_data):
        "Performs create instance. Returns wrapped model intance"
        return MongoInstanceWrapper(self.get_model().objects.create(**validated_data))

    def update(self, instance, validated_data):
        #type: (InstanceWrapper, dict)->InstanceWrapper
        "Performs update for instance. Returns wrapped instance with updated fields"

        assert isinstance(instance, InstanceWrapper)
        #don't update id of document
        validated_data.pop("id", None)

        instance.update(validated_data)

        return instance







