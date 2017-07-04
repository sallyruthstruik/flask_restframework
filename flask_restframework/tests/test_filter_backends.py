import json

import pytest
from mongoengine.queryset.queryset import QuerySet

from flask.ext.restframework.filter_backends import JsonFilterBackend, OrderingBackend
from flask.ext.restframework.queryset_wrapper import MongoDbQuerySet
import mongoengine as m

from flask.ext.restframework.tests.compat import mock


class Doc(m.Document):
    pass


@mock.patch.object(QuerySet, "filter")
def test_json_filter_backend(m, db):
    qs = Doc.objects.all()
    m.return_value = qs

    jf = JsonFilterBackend(
        MongoDbQuerySet.from_queryset(qs),
        mock.Mock(
            args=dict(json_filters=json.dumps(dict(key="value")))
        ), mock.Mock(
            spec=[]
        )
    )

    jf.filter()

    assert isinstance(m, mock.Mock)
    m.assert_has_calls([
        mock.call(__raw__=dict(key="value"))
    ])

@pytest.mark.test_json_filter_backend
@mock.patch.object(QuerySet, "order_by")
def test_ordering_backend(m, db):
    qs = Doc.objects.all()
    m.return_value = qs

    ob = OrderingBackend(
        MongoDbQuerySet.from_queryset(qs),
        mock.Mock(
            args=dict(ordering="field,-other")
        ),
        mock.Mock(spec=[])
    )
    ob.filter()
    m.assert_has_calls([
        mock.call("field", "-other")
    ])

    #check default ordering
    ob = OrderingBackend(
        MongoDbQuerySet.from_queryset(qs),
        mock.Mock(
            args=dict()
        ),
        mock.Mock(spec=["ordering"], ordering=("-field", ))
    )
    ob.filter()
    m.assert_has_calls([
        mock.call("-field")
    ])


