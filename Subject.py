import mongoengine

from Connection import Connection


class Subject(mongoengine.Document):
    subject = mongoengine.StringField(required=True)
    tag = mongoengine.StringField(required=True)
    type = mongoengine.StringField(required=True)
    connections = mongoengine.EmbeddedDocumentListField(Connection)
    meta = {
        'db_alias': 'core',
        'collection': 'topology'
    }
