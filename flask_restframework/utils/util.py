import contextlib

from mongoengine.errors import FieldDoesNotExist, ValidationError

from flask_restframework import exceptions


@contextlib.contextmanager
def wrap_mongoengine_errors(updater=None):
    try:
        yield
    except (FieldDoesNotExist, ValidationError) as e:
        data = e.to_dict()
        if updater:
            data = updater(data)
        raise exceptions.ValidationError(data)
