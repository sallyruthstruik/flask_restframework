import copy

import six
from flask import jsonify
from flask.globals import current_app

from flask_restframework.filter_backends import BaseBackend
from flask_restframework.resource import BaseResource, BaseResourceMetaClass


# TODO: Need usage, comment
from flask_restframework.serializer.model_serializer import ModelSerializer



class ModelResource(BaseResource):
    """
    Generic resource for CRUD on mongoengine models.

    Simple usage example::

        >>> class Model(db.Document):
        >>>
        >>>     f1 = db.StringField()
        >>>     f2 = db.BooleanField()
        >>>     f3 = db.StringField()
        >>>
        >>> class S(ModelSerializer):
        >>>     class Meta:
        >>>         model = Model
        >>>
        >>> class ModelRes(ModelResource):
        >>>     serializer_class = S
        >>>     queryset = Model.objects.all()
        >>>
        >>> router = DefaultRouter(app)
        >>> router.register("/test", ModelRes, "modelres")

    In this configuration will be allowed next HTTP methods:

        * GET /test returns::

            [{'f1': '1', 'f2': True, 'f3': '1', 'id': '5864db5d32105b50fa02162b'},
             {'f1': '2', 'f2': True, 'f3': '2', 'id': '5864db5d32105b50fa02162c'}]

        * GET /test/5864db5d32105b50fa02162b returns::

            {'f1': '1', 'f2': True, 'f3': '1', 'id': '5864e2a332105b5a350b99bc'}

    """
    __metaclass__ = BaseResourceMetaClass

    serializer_class = None
    queryset = None
    pagination_class = None
    filter_backends = None  #list of BaseBackend subclasses for filtering GET output


    def __init__(self, request):
        super(ModelResource, self).__init__(request)

        if not self.serializer_class:
            raise ValueError("serializer_class is required")
        if self.get_queryset() is None:
            raise ValueError("queryset is required")

    def get_pagination_class(self):
        """
        Returns pagination class

        You can use pagination_class attribute or set config variable:

            FLASK_REST = {
                "PAGINATION_CLASS": <Your pagination class>
            }
        """

        return self.pagination_class or current_app.config.get("FLASK_REST", {}).get("PAGINATION_CLASS")

    def get_queryset(self):
        return self.queryset

    def get_instance(self, pk):
        "returns one instance from queryset by its PK"
        return self.get_queryset().get(id=pk)

    def get_backend_classes(self):
        "Returns backend classes"

        return self.filter_backends or current_app.config.get("FLASK_REST", {}).get("FILTER_BACKENDS")

    def filter_qs(self, qs):
        "Perform filtration of queryset base on filter_backends"

        backend_classes = self.get_backend_classes()

        if backend_classes:
            for backendCls in backend_classes:
                backend = backendCls(qs, self.request, resource=self)
                assert isinstance(backend, BaseBackend)
                qs = backend.filter()

        return qs

    def get(self, request):
        qs = self.get_queryset()

        qs = self.filter_qs(qs)

        paginationCls = self.get_pagination_class()

        if paginationCls:
            pagination = paginationCls(qs)
            pagination.paginate(request)

            data = self.serializer_class(pagination.qs).to_python()

            data = pagination.update_response(data)
        else:
            data = self.serializer_class(qs).to_python()

        return jsonify(data)

    def post(self, request):
        serializer = self.serializer_class(request.form)
        if not serializer.validate():
            out = jsonify(serializer.errors)
            out.status_code = 400
            return out
        obj = serializer.create(serializer.cleaned_data)
        return jsonify(self.serializer_class(obj).to_python())

    def get_object(self, request, pk):
        obj = self.get_instance(pk)
        return jsonify(self.serializer_class(obj).to_python())

    def put_object(self, request, pk):
        data = self.get_data(request)

        serializer = self.serializer_class(data)

        assert isinstance(serializer, ModelSerializer)
        if not serializer.validate():
            out = jsonify(serializer.errors)
            out.status_code = 400
            return out

        instance = self.get_instance(pk)

        oldInstance = copy.deepcopy(instance)

        validated_data = {
            key: value
            for key, value in six.iteritems(serializer.cleaned_data)
            if key in data
        }

        updatedInstance = serializer.update(instance, validated_data=validated_data)

        self.after_update(oldInstance, updatedInstance, validated_data)

        return jsonify(self.serializer_class(updatedInstance).to_python())

    def after_update(self, oldInstance, updatedInstance, validated_data):
        "Will be called after updating existed instance"
        pass

    def delete_object(self, request, pk):
        instance = self.get_instance(pk)
        id = instance.id
        instance.delete()

        return jsonify({"id": id})

    def get_data(self, request):
        "Returns json body data from request"
        return request.json
