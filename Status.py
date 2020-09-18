import mongoengine
import datetime


class Status(mongoengine.EmbeddedDocument):
    current = mongoengine.StringField(required=True, default="Not resolved")
    time = mongoengine.DateTimeField(default=datetime.datetime.now)
    previous = mongoengine.ListField()

    def __str__(self):
        return "Previous statuses: " + str(self.previous) + ". Curent status: {} -> {}".format(self.current, self.time)
