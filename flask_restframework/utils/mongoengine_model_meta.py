import six
from mongoengine import fields as db
from flask_restframework import fields

FIELD_MAPPING = {
    db.ObjectIdField: fields.StringField,
    db.StringField: fields.StringField,
    db.BooleanField: fields.BooleanField,
    db.DateTimeField: fields.DateTimeField,
    db.EmbeddedDocumentField: fields.EmbeddedField,
    db.ReferenceField: fields.PrimaryKeyRelatedField,
    db.IntField: fields.IntegerField,
    db.URLField: fields.URLField,
    db.EmbeddedDocumentListField: fields.ListField,
    db.ListField: fields.ListField,
    db.DictField: fields.DictField
}

def get_fields(model):
    "Returns dict <fieldName>: <fieldClass>"
    out = {}
    for key, value in six.iteritems(model._fields):
        out[key] = value.__class__

    return out


def initialize_field(field):
    return None


def get_field(model, key):
    "for model returns its field instance with name key"
    return model._fields[key]
