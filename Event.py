import mongoengine
import datetime
class Event(mongoengine.Document):
    time = mongoengine.DateTimeField(default=datetime.datetime.now)
    description = mongoengine.StringField(required=True)
    subjectId = mongoengine.StringField(required=True)
    meta = {
        'db_alias': 'core',
        'collection': 'log'
    }