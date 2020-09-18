import mongoengine


class Connection(mongoengine.EmbeddedDocument):
    src = mongoengine.StringField(required=True)
    dst = mongoengine.StringField(required=True)
    capacity = mongoengine.IntField(default=1)
