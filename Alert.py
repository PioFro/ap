import mongoengine
import datetime
import dash_core_components as dcc

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
    def __str__(s):
        return """
        **Subject:** {}
        
        **Explanation:** {}
        
        **Time:** {}
        """.format(s.subject, s.explanation,s.time)

    def show(self):
        return [dcc.Markdown("""

                ** Subject: ** {}

                ** Provided by: **{}

                ** Date: **{} 

                ** Severity: **{}

                ** Explanation: **{}

                ** Detailed explanation: **{}
                
                ** Statuses: **{}

                """.format(self.subject, "SerIoT", self.time, self.severity, self.explanation, self.details,str(self.status)),
                             style={"color": "#4e1175"})]
    def block(self):
        print("block")
    def ok(self):
        print("ok")
    def allow(self):
        print("allow")