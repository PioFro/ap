import mongoengine
import datetime

from Status import Status


class Alert(mongoengine.Document):
    subject = mongoengine.StringField(required=True)
    explanation = mongoengine.StringField(required=True)
    severity = mongoengine.IntField(default=0)
    time = mongoengine.DateTimeField(default=datetime.datetime.now)
    details = mongoengine.StringField(default="No details provided")
    status = mongoengine.EmbeddedDocumentField(Status)
    resolved = mongoengine.BooleanField(default=False)
    meta = {
        'db_alias': 'core',
        'collection': 'alerts'
    }
