import mongoengine
import re


class Mail(mongoengine.Document):
    address = mongoengine.StringField(required=True, regex=re.compile('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'))
    level = mongoengine.IntField(default=10, min_value=0, max_value=10)
    meta = {
        'db_alias': 'core',
        'collection': 'mails'
    }
