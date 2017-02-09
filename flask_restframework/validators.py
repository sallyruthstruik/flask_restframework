import re

from flask_restframework.exceptions import ValidationError

class BaseValidator(object):

    message = None

    def __init__(self, message=None):

        if message:
            self.message = message

    def raise_error(self, **context):
        raise ValidationError(self.message.format(**context))

    def __call__(self, serializer, value):
        ":type serializer: flask_restframework.serializer.base_serializer.BaseSerializer"
        raise NotImplementedError

    def for_mongoengine(self):
        "Allows you to use these validators at mongoengine level"
        def inner(value):
            try:
                self(None, value)
            except ValidationError:
                return False

            return True

        inner.original_validator = self

        return inner


class RegexpValidator(BaseValidator):

    message = "Value {value} doesn't match pattern {pattern}"

    def __init__(self, pattern, **k):
        super(RegexpValidator, self).__init__(**k)
        self.pattern = pattern

    def __call__(self, serializer, value):
        if not re.match(self.pattern, value):
            self.raise_error(value=value, pattern=self.pattern)
        return value


