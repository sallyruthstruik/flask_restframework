import mongoengine


class BaseModelWrapper(object):
    """
    Wraps model class and provide interface for:

    * Getting fields
    * Getting constraings

    and so on
    """

    def __init__(self, modelClass):
        self.modelClass = modelClass

    @classmethod
    def fromModel(cls, modelClass):
        if issubclass(modelClass, mongoengine.Document):
            return

class MongoEngineModelWrapper(BaseModelWrapper):
    pass

class SqlAlchemyModelWrapper(BaseModelWrapper)