import contextlib
import warnings

import functools
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

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning) #turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__), category=DeprecationWarning, stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning) #reset filter
        return func(*args, **kwargs)

    return new_func