import six


from flask_restframework.serializer.base_serializer import BaseSerializer, _BaseSerializerMetaClass


from ..utils import mongoengine_model_meta as model_meta


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
        >>> data = S(Col.objects.all()).to_python()

    """
    field_mapping = model_meta.FIELD_MAPPING

    def get_model(self):
        try:
            return self.Meta.model
        except:
            raise ValueError("You should specify Meta class with model attribute")

    def get_fields(self):
        model = self.get_model()

        fieldsFromModel = {}

        for key, fieldCls in six.iteritems(model_meta.get_fields(model)):
            if fieldCls not in self.field_mapping:
                raise ValueError("No mapping for field {}".format(fieldCls))

            fieldsFromModel[key] = self.field_mapping[fieldCls].from_mongoengine_field(
                model_meta.get_field(model, key)
            )

        fieldsFromModel.update(super(ModelSerializer, self).get_fields())

        return fieldsFromModel

    def create(self, validated_data):
        "Performs create instance. Returns model intance"
        return self.get_model().objects.create(**validated_data)

    def update(self, instance, validated_data):
        "Performs update for instance. Returns instance with updated fields"

        for key, value in six.iteritems(validated_data):
            try:
                setattr(instance, key, value)
            except Exception as e:
                print(key, value)

        instance.save()

        return instance







