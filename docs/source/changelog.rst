
Changelog
==============


New in 0.0.27
------------------------

* Добавлен промежуточный слой между сериалайзерами и Queryset: :class:`flask_restframework.queryset_wrapper.QuerysetWrapper`
  :class:`flask_restframework.queryset_wrapper.InstanceWrapper`. Это позволяет использовать различные источники данных для сериализации,
  например
  .. code-block:: python

        class S(ModelSerializer):

            ref = fields.ReferenceField(
                Nested, queryset=Ref.objects.all
            )

            nested_list = fields.ListField(fields.ReferenceField(Nested, queryset=Ref.objects.all))

            class Meta:
                model = Doc
                fields = ("id", )

        data = S(QuerysetWrapper.from_queryset(Doc.objects.no_dereference())).serialize()
        data = S(QuerysetWrapper.from_queryset(Doc._get_collection().find())).serialize()

  На больших коллекциях второй вариант будет на несколько порядков быстрее, тк пропускается шаг сериализации в MongoEngine Document

* Больше нельзя напрямую инстанцировать Serializer из Queryset. Нужно использовать методы :func:`flask_restframework.serializer.base_serializer.BaseSerializer.from_queryset`
  и :func:`flask_restframework.serializer.base_serializer.BaseSerializer.from_instance`
  .. code-block:: python

        Serializer.from_queryset(Doc.objects.all())
        Serializer.from_instance(Doc.objects.first())

* Добавлен класс :class:`flask_restframework.fields.ReferenceField`, позволяющий сериализовать JOIN-отношения и mongoengine.ReferenceField
  .. code-block:: python

        class Nested(BaseSerializer):
            value = fields.StringField()

        class S(ModelSerializer):
            ref = fields.ReferenceField(
                Nested, queryset=Ref.objects.all
            )

            nested_list = fields.ListField(fields.ReferenceField(Nested, queryset=Ref.objects.all))

            class Meta:
                model = Doc
                fields = ("id", )

        data = S(QuerysetWrapper.from_queryset(Doc.objects.no_dereference())).serialize()

* Методы всех mixin классов (:class:`flask_restframework.model_resource.CreateMixin`, :class:`flask_restframework.model_resource.UpdateMixin`,...)
  в качестве instance принимают InstanceWrapper
