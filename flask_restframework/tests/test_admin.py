from flask_restframework.admin.manager import Admin
from flask_restframework.resource import BaseResource
import mongoengine as me

class R1(BaseResource):
    pass

class R2(BaseResource):
    pass


class Doc(me.Document):
    field = me.StringField()


def test_admin_register_resources(app, db):
    Doc.objects.delete()
    doc = Doc.objects.create(
        field="field"
    )

    admin = Admin()

    admin.register_resource(R1)
    admin.register_resource(R2)
    admin.register_model(Doc)

    admin.init_blueprint(app, "admin", __name__, "/admin")

    assert admin.view_resources().json == [
        {"name": "r1", "url": '/admin/resource/r1'},
        {"name": "r2", "url": '/admin/resource/r2'},
        {"name": "doc", "url": '/admin/resource/doc'}
    ]

    assert admin._registered_resources[-1].view_list_resource().json["results"] == [
        {"field": "field", "id": str(doc.id)}
    ]