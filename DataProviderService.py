import mongoengine
import datetime
from Alert import Alert
from Connection import Connection
from Mails import Mail
from Status import Status
from Subject import Subject


def global_init():
    mongoengine.register_connection(alias='core', name='autopolicy')


def getSubjectById(sub: str):
    subject = Subject.objects().filter(subject=sub).first()
    return subject


# add details by using keyword details="details"
def addAlert(exp, sub, sev, **kwargs):
    details = kwargs.get("details", None)
    if getSubjectById(sub) is None:
        print("No such subject : {}".format(sub))
        return
    newAlert = Alert()
    if details is not None:
        newAlert.details = details
    newAlert.subject = sub
    newAlert.explanation = exp
    newAlert.severity = sev
    newAlert.save()


def addSubject(sub, tag, type, conections: []):
    if getSubjectById(sub) is not None:
        print("Subject {} already exists.".format(sub))
        return
    subject = Subject()
    subject.subject = sub
    subject.type = type
    subject.tag = tag
    subject.connections = conections
    subject.save()


def getAlerts():
    return Alert.objects()


def getAlert(alertId):
    return Alert.objects().filter(id=alertId).first()


def changeState(alertId, nextStatus):
    alert = getAlert(alertId)
    if alert.status is None:
        alert.status = Status()
        alert.save()
        return
    previousStatus = alert.status.current
    previousStatusTime = alert.status.time
    alert.status.previous.append("{} -> {}".format(previousStatus, previousStatusTime))
    alert.status.current = nextStatus
    alert.status.time = datetime.datetime.now()
    alert.save()


def delAlert(alertId):
    Alert.objects().filter(id=alertId).delete()


def addMail(addr, **kwargs):
    mail = Mail()
    level = kwargs.get("lvl", None)
    mail.address = addr
    if level is not None:
        mail.level = level
    mail.save()
