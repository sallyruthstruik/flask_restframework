from collections import OrderedDict
import six as six
from mongoengine.queryset.queryset import QuerySet
from werkzeug.exceptions import BadRequest

from flask_restframework.fields import BaseRelatedField
from flask_restframework.fields import ForeignKeyField

from flask_restframework.fields import BaseField
from ..exceptions import ValidationError

__author__ = 'stas'

class _BaseSerializerMetaClass(type):
    """
    This metaclass sets a dictionary named `_declared_fields` on the class.
    Any instances of `Field` included as attributes on either the class
    or on any of its superclasses will be include in the
    `_declared_fields` dictionary.
    """

    @classmethod
    def _get_declared_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in list(attrs.items())
                  if isinstance(obj, BaseField)]

        # If this class is subclassing another Serializer, add that Serializer's
        # fields.  Note that we loop over the bases in *reverse*. This is necessary
        # in order to maintain the correct order of fields.
        for base in reversed(bases):
            if hasattr(base, '_declared_fields'):
                fields = list(base._declared_fields.items()) + fields

        return OrderedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = cls._get_declared_fields(bases, attrs)
        return super(_BaseSerializerMetaClass, cls).__new__(cls, name, bases, attrs)

@six.add_metaclass(_BaseSerializerMetaClass)
class BaseSerializer:
    """
    Base class for all validators.
    Each validator represents rules for validating request
    Each view can have multiple validators, base on Content-Type header
    Validator can validate next fields:

        * request.form - Ordinal POST queries
        * request.json - POST JSON body
        * request.args - GET params
        * request.files - passed files

    After validation, validator has next properties:

        * self.errors - error dict in next format::

            {
                <field>: [list of errors]
                __non_field_errors__: [list of common (not field) errors]
            }

        * self.data - validated data constructed from request.form/request.json
        * self.query_data - validated data constructed from request.args
        * self.files - validated files

    Usage example::

        class TestValidation(BaseValidator):

            choices = fields.StringField(choices=["1", "2", "3"], required=True)
            not_req = fields.StringField()
            boolean = fields.BooleanField(required=True)
            boolean_not_req = fields.BooleanField()

    Meta subclass atributes::

        class Meta:

            allow_additional_fields = False     #if True - all not registered fields also will be passed in cleaned_data
            excluded = ("field1", )             # array of fields need to be excluded from serialization
            fields = ("field1", )               # array of fields need to be serialized. You can't use fields and excluded in
                                                  same serializer
            fk_fields = ("related__field", )    # array of related (or embeddedDocument) fields need to be serialized
            read_only = (<read only field name>, )  #array of read only fields of serializer


    """

    _declared_fields = None     #type: OrderedDict

    def __init__(self, data, context=None):

        self._data = data    #original data
        self._cleaned_data = {}     #validated data
        self.context = context or {}

        self._bind_self_to_fields()

    def get_fields(self):
        "returns mapping: <fieldName>: <Field>"

        return self._declared_fields

    def to_python(self):
        """
        Returns python representation of queryset data.
        This data will be used in serializer.cleaned_data
        """
        if isinstance(self._data, QuerySet):

            output = []
            for item in self._data:
                output.append(self._item_to_python(item))
        else:
            output = self._item_to_python(self._data)

        return output

    def serialize(self):
        """
        This method takes python representation .to_python of data
        and perform serialization to json-compatible array
        """

        data = self.to_python()


        if isinstance(data, list):
            out = []
            for item in data:
                out.append(self._serialize_item(item))
            return out
        else:
            return self._serialize_item(data)



    @property
    def cleaned_data(self):
        return self._cleaned_data

    def create(self, validated_data):
        """
        Perform create operation
        :param validated_data: data after validation
        :return: created instance
        """

    def update(self, instance, validated_data):
        """
        Perform update opertaion
        :param instance: instance for update
        :param validated_data: data after validation
        :return: updated instance
        """

    def validate(self, part=False):
        """
        Runs validation on passed data

        Usage example::

            >>> s = serializerCls(request.json)
            >>> if not s.validate():
            >>>     out = jsonify(s.errors)
            >>>     out.status_code = 400
            >>>     return out

        You can preform part validation, i.e. to validate only presented in data fields.
        It can be useful for validating PATCH request, when we need to validate only subset of fields.

        :return: True if validation succeeded, False else
        """
        from flask_restframework import fields

        errors = {}

        if self._data is None:
            raise BadRequest("No data passed")

        if self._allow_additional_fields():
            self._cleaned_data = self._data.copy()

        for key, field in self._get_writable_fields().items():

            #skip not presented fields for part validation
            if part and key not in self._data.keys():
                continue

            assert isinstance(field, fields.BaseField)

            value = self._data.get(key)

            try:
                validated_value = field.run_validate(serializer=self, value=value)

                self._cleaned_data[key] = validated_value

            except ValidationError as e:
                if isinstance(e.data, dict):
                    for key, message in six.iteritems(e.data):
                        errors.setdefault(key, []).append(message)
                elif isinstance(e.data, six.string_types):
                    errors.setdefault(key, []).append(e.data)

        self.errors = errors

        if errors:
            return False

        return True

    def get_serialisable_fields(self):
        "returns set of fields need to be serialized"
        output = set(self.get_fields().keys())
        if hasattr(self, "Meta"):

            meta = self.Meta
            if hasattr(meta, "fields"):
                output = set(meta.fields)

                if hasattr(meta, "excluded"):
                    raise ValueError("You can't use fields and excluded attribute together!")

            elif hasattr(meta, "excluded"):
                output = set(self.get_fields().keys()).difference(meta.excluded)

        return output

    def get_declared_only_fields(self):
        "Returns only declared fields"
        return self._declared_fields

    def get_fk_fields(self):
        """
        Returns dictionary with ForeignKey fields
        This is fields which ONLY readable. You can use it only for representing nested/related data.
        For use it in validation, use PrimaryKeyField
        <key in serializer>: <field instance>
        """
        out = {}
        if hasattr(self, "Meta") and hasattr(self.Meta, "fk_fields"):
            for key in self.Meta.fk_fields:
                if "__" not in key:
                    raise ValueError("You should use Django __ notation for FK fields!")

                mainFkField = key.split("__")[0]
                fields = self.get_fields()
                if mainFkField not in self.get_fields():
                    raise ValueError("Incorrect field: {}".format(mainFkField))

                out[key] = fields[mainFkField]

        for key, value in six.iteritems(self.get_declared_only_fields()):
            if isinstance(value, ForeignKeyField):
                out[key] = value

        return out

    def _allow_additional_fields(self):
        meta = getattr(self, "Meta", None)
        return getattr(meta, "allow_additional_fields", False)

    def _item_to_python(self, item):
        "Return python representation for one item, base on fields"

        out = {}

        serializable_fields = self.get_serialisable_fields()

        for key, field in self.get_fields().items():
            if key not in serializable_fields:
                continue

            assert isinstance(field, BaseField), field

            value = field.get_value_from_model_object(item, key)

            out[key] = field.to_python(value)

        for key, field in six.iteritems(self.get_fk_fields()):
            assert isinstance(field, BaseRelatedField)

            value = field.get_value_from_model_object(item, key)

            out[key] = field.to_python(value)

        return out

    def _serialize_item(self, item):
        """
        Performs serialization for python representation of item.
        Uses Field.
        """
        out = {}

        for key, value in self.get_fields().items():
            assert isinstance(value, BaseField)
            if key in item:
                out[key] = value.to_json(item[key])

        for key, value in self.get_fk_fields().items():
            if key in item:
                out[key] = value.to_json(item[key])

        return out

    def _get_writable_fields(self):
        """
        Returns subdict from self.get_fields() with writable fields only

        :rtype dict:
        """
        out = {}

        read_only_from_meta = []
        if hasattr(self, "Meta"):
            read_only_from_meta = getattr(self.Meta, "read_only", [])

        for key, field in self.get_fields().items():
            assert isinstance(field, BaseField)
            if not field._read_only and key not in read_only_from_meta:
                out[key] = field

        return out


    def _bind_self_to_fields(self):
        "For each field sets <field>.serializer to self"
        for fieldname, field in six.iteritems(self.get_fields()):
            field.serializer = self
            field.fieldname = fieldname




