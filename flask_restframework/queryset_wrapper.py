#coding: utf8
from flask.ext.sqlalchemy import Model, BaseQuery, _BoundDeclarativeMeta
from flask.globals import current_app
from mongoengine.base.document import BaseDocument
from mongoengine.document import Document
from mongoengine.queryset.queryset import QuerySet
from pymongo.cursor import Cursor
from sqlalchemy.sql.expression import desc


class InstanceWrapper(object):
    """
    Обертка для записи из базы.

    Поддерживается Mongoengine Document и dict из курсора.

    """
    def __init__(self, item):
        self.item = item

    def get_id(self):
        """
        Возвращает id записи
        """
        raise NotImplementedError

    def get_field(self, key):
        """
        Возвращает значение поля key для обернутой записи.
        Должен поддерживать __ Django нотацию
        """
        raise NotImplementedError

    def update(self, validated_data):
        raise NotImplementedError

    def to_dict(self):
        """
        Should return dict representation of instance
        """
        raise NotImplementedError

    def delete(self):
        """
        Should delete this instance
        """
        raise NotImplementedError

    @classmethod
    def from_instance(cls, item):
        """
        Returns wrapped instance
        """
        if isinstance(item, Document):
            return MongoInstanceWrapper(item)
        elif isinstance(item, dict):
            return CursorInstanceWrapper
        elif isinstance(item, Model):
            return SqlAlchemyInstanceWrapper(item)

        raise TypeError("Incorrect type {}".format(type(item)))

class MongoInstanceWrapper(InstanceWrapper):
    """
    Обертка для Mongoengine Document записи
    """
    item = None #type: Document

    def delete(self):
        self.item.delete()

    def to_dict(self):
        return self.item.to_mongo()

    def get_id(self):
        return self.item.pk

    def update(self, validated_data):
        for key, value in validated_data.items():
            setattr(self.item, key, value)

        self.item.save()

    def get_field(self, key):
        out = self.item

        for part in key.split("__"):
            try:
                out = getattr(out, part)
            except:
                return None

        if isinstance(out, (BaseDocument, dict)):
            return MongoInstanceWrapper(out)
        elif isinstance(out, list):
            r = []
            for item in out:
                if isinstance(item, (BaseDocument, dict)):
                    r.append(MongoInstanceWrapper(item))
                else:
                    r.append(item)

            return r

        return out


class SqlAlchemyInstanceWrapper(InstanceWrapper):

    __db = None
    @property
    def db(self):
        from flask_restframework.model_wrapper import SqlAlchemyModelWrapper

        if self.__db is None:
            self.__db = SqlAlchemyModelWrapper.db

        return self.__db

    def update(self, validated_data):
        for key, value in validated_data.items():
            setattr(self.item, key, value)

        self.db.add(self.item)
        self.db.commit()

    def get_id(self):
        return self.item.id

    def delete(self):
        self.db.delete(self.item)
        self.db.commit()

    def to_dict(self):
        return {
            key: value
            for key, value in self.item.__dict__.items()
            if not key.startswith("_")
        }

    def get_field(self, key):
        out = self.item

        for part in key.split("__"):
            try:
                out = getattr(out, part)
            except:
                return None

        return out


class CursorInstanceWrapper(InstanceWrapper):
    """
    Обертка для записи из pymongo.Cursor (по сути обычный dict)
    """
    def to_dict(self):
        return dict(self.item)

    def get_id(self):
        return self.item["_id"]

    def get_field(self, key):
        if key == "id":
            key = "_id"

        out = self.item

        for part in key.split("__"):
            try:
                out = out.get(part)
            except:
                return None

        if isinstance(out, dict):
            return CursorInstanceWrapper(out)
        if isinstance(out, list):
            r = []

            for item in out:
                if isinstance(item, dict):
                    r.append(CursorInstanceWrapper(item))
                else:
                    r.append(item)

            return r

        return out

class QuerysetWrapper(object):
    """
    Обертка для Queryset.
    """
    def __init__(self, data, wrapperType):
        self.wrapperType = wrapperType
        self.data = data

    @classmethod
    def from_model(cls, modelCls):
        from flask_restframework.model_wrapper import SqlAlchemyModelWrapper
        if issubclass(modelCls, Document):
            return cls.from_queryset(modelCls.objects.all())
        elif issubclass(modelCls, Model):
            return cls.from_queryset(modelCls.query)
        else:
            raise TypeError(type(modelCls))

    @classmethod
    def from_queryset(cls, qs):
        """
        Returns wrapped queryset from passed qs
        """
        if isinstance(qs, QuerySet):
            return MongoDbQuerySet(qs, MongoInstanceWrapper)
        elif isinstance(qs, Cursor):
            return CursorQuerySet(qs, CursorInstanceWrapper)
        elif callable(qs):
            return cls.from_queryset(qs())
        elif isinstance(qs, QuerysetWrapper):
            return qs
        elif isinstance(qs, BaseQuery):
            return SqlAlchemyQuerySet(qs, SqlAlchemyInstanceWrapper)

        raise TypeError("Unknown type {}".format(type(qs)))

    def get(self, id):
        #type: (Any)->InstanceWrapper
        """Should return one instance by it id"""

        raise NotImplementedError

    def get_data(self):
        #type: ()->List[InstanceWrapper]
        """
        Returns iterable of InstanceWrapper
        """

        for item in self.data:
            yield self.wrapperType(item)

    def count(self):
        """
        Should return total count of items in QuerySet
        """
        raise NotImplementedError

    def slice(self, frm, to):
        """
        Should slice queryset
        """
        raise NotImplementedError

    def filter_by(self, **filters):
        #type: ()->QuerysetWrapper
        """
        Should filter queryset by filters (Django style filtering)
        Returns new queryset
        """
        raise NotImplementedError

    def order_by(self, *ordering):
        #type: (list[str])->QuerysetWrapper
        """
        Should return ordered queryset.

        :param ordering: list of fields: "field" for ASC, "-field" for DESC
        """
        raise NotImplementedError

    def first(self):
        """
        Should return first element of queryset or None
        """
        raise NotImplementedError


class MongoDbQuerySet(QuerysetWrapper):
    """
    Обертка для MongoEngine Queryset
    """

    def first(self):
        return self.data.first()

    def order_by(self, *ordering):
        return MongoDbQuerySet(self.data.order_by(*ordering), self.wrapperType)

    def filter_by(self, **filters):
        return MongoDbQuerySet(self.data.filter(**filters), self.wrapperType)

    def slice(self, frm, to):
        return MongoDbQuerySet(self.data[frm:to], self.wrapperType)

    def get(self, id):
        return self.wrapperType(self.data.get(id=id))

    def count(self):
        return self.data.count()

class CursorQuerySet(QuerysetWrapper):
    """
    Обертка для pymongo.Cursor
    """
    def __init__(self, *a, **k):
        super(CursorQuerySet, self).__init__(*a, **k)
        self.data = list(self.data)

    def count(self):
        return len(self.data)

    def filter_by(self, id=None):
        return CursorQuerySet(filter(
            lambda item: item["_id"]==id,
            self.data
        ), wrapperType=self.wrapperType)

    def slice(self, frm, to):
        return self.data[frm: to]

class SqlAlchemyQuerySet(QuerysetWrapper):
    def first(self):
        item = self.data.first()
        if item:
            return SqlAlchemyInstanceWrapper(item)

    def slice(self, frm, to):
        return SqlAlchemyQuerySet(self.data.limit(to-frm).offset(frm), SqlAlchemyInstanceWrapper)

    def get(self, id):
        return self.data.get(id=id)

    def count(self):
        return self.data.count()

    def filter_by(self, **filters):
        f = []

        model = self._get_model()

        for key, value in filters.items():
            clause = "eq"
            if "__" in key:
                key, clause = key.split("__")

            if clause == "eq":
                f.append(getattr(model, key) == value)
            elif clause == "ne":
                f.append(getattr(model, key) == value)
            else:
                raise TypeError("Unknown clause {} for key {}".format(clause, key))

        return SqlAlchemyQuerySet(self.data.filter(*f), SqlAlchemyInstanceWrapper)

    def _get_model(self):
        return self.data._primary_entity.entity_zero._identity_class

    def order_by(self, *ordering):
        l = []
        model = self._get_model()
        for col in ordering:
            if col[0] == "-":
                l.append(desc(getattr(model, col.lstrip("-"))))
            else:
                l.append(getattr(model, col))

        return SqlAlchemyQuerySet(self.data.order_by(*l), SqlAlchemyInstanceWrapper)

