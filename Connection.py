import mongoengine


class Connection(mongoengine.EmbeddedDocument):
    src = mongoengine.StringField(required=True)
    dst = mongoengine.StringField(required=True)
    capacity = mongoengine.IntField(default=1)
    def __str__(self):
        return "src: {}, dst:{}, capacity: {}".format(self.src, self.dst, str(self.capacity))
