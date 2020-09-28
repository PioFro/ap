import mongoengine
import datetime
from Alert import Alert
from Connection import Connection
from Mails import Mail
from Status import Status
from Subject import Subject
from Event import Event

class Data:
    INIT = False

def global_init():
    if not Data.INIT:
        mongoengine.register_connection(alias='core', name='autopolicy')
        Data.INIT = True
        addEvent("Connected to the database.","admin")

def getSubjectById(sub: str)->Subject:
    if Data.INIT:
        subject = Subject.objects().filter(subject=sub).first()
        return subject
    else:
        global_init()
        return getSubjectById(sub)

def getSubjects()->[Subject]:
    if Data.INIT:
        return Subject.objects()
    else:
        global_init()
        return Subject.objects()

def delSubjects():
    if Data.INIT:
        for sub in Subject.objects():
            addEvent("Device {} was deleted.".format(sub.subject),"admin")
            sub.delete()
    else:
        global_init()
        delSubjects()


# add details by using keyword details="details"
def addAlert(exp, sub, sev, **kwargs):
    if Data.INIT:
        details = kwargs.get("details", None)
        if getSubjectById(sub) is None:
            addEvent("Failed to create alert - no such subject in the network as stated in the alert.", sub)
            return False,"No such subject : {}".format(sub), "NO ID"
        newAlert = Alert()
        if details is not None:
            newAlert.details = details
        newAlert.subject = sub
        newAlert.explanation = exp
        newAlert.severity = sev
        newAlert.status = Status()
        newAlert.save()
        addEvent("Created an alert on {}. Cause: {}".format(sub,exp), str(newAlert.id))
        return True, "OK", newAlert.id
    else:
        global_init()
        return addAlert(exp,sub,sev)


def addSubject(sub, tag, type, conections: []):
    if Data.INIT:
        if getSubjectById(sub) is not None:
            addEvent("Unable to create a subject in the network. Subject already exists.", sub)
            print("Subject {} already exists.".format(sub))
            return
        subject = Subject()
        subject.subject = sub
        subject.type = type
        subject.tag = tag
        subject.connections = conections
        subject.save()
        addEvent("Added subject: {} to the database.".format(sub), str(subject.id))
        links = []
        for connnection in subject.connections:
            links.append(connnection.dst)
        addConnectionsTo(sub,links)

    else:
        global_init()
        addSubject(sub,tag,type,conections)

def delSubject(sub):
    if Data.INIT:
        toDel = getSubjectById(sub)
        addEvent("Device {} was deleted.".format(toDel.subject), "admin")
        links = []
        for connnection in toDel.connections:
            links.append(connnection.dst)
        delConnectionsTo(sub,links)
        toDel.delete()
    else:
        global_init()
        delSubject(sub)

def delConnectionsTo(sub, links):
    for subject in getSubjects():
        if subject.subject!=sub and subject.subject in links:
            for connection in subject.connections.copy():
                if connection.dst == sub:
                    addEvent("Connection between {} and {} was deleted.".format(sub,connection.src), "admin")
                    subject.connections.remove(connection)
                    break
            subject.save()

def addConnectionsTo(sub,links):
    for subject in getSubjects():
        if subject.subject!=sub and subject.subject in links:
            con = Connection()
            con.src=subject.subject
            con.dst=sub
            con.capacity = 1
            subject.connections.append(con)
            addEvent("Connection between {} and {} added automatically due to the lack of such in {}".format(sub,subject.subject,subject.subject),str(subject.id))
            subject.save()

def getAlerts():
    if Data.INIT:
        return Alert.objects().filter(resolved=False)
    else:
        global_init()
        return getAlerts()


def getAlert(alertId):
    if Data.INIT:
        return Alert.objects().filter(id=alertId).first()
    else:
        global_init()
        return getAlert(alertId)

def changeState(alertId, nextStatus, **kwargs):
    if Data.INIT:
        res = kwargs.get("resolved", None)
        alert = getAlert(alertId)
        if alert.status is None:
            alert.status = Status()
            alert.save()
            return

        previousStatus = alert.status.current
        if previousStatus == nextStatus:
            addEvent("Unable to create next status in alert - the status was already created.",str(alert.id))
            return
        for stat in alert.status.previous:
            if nextStatus in stat:
                addEvent("Unable to create next status in alert - the status was already created.", str(alert.id))
                return
        previousStatusTime = alert.status.time
        alert.status.previous.append("{} -> {}".format(previousStatus, previousStatusTime))
        alert.status.current = nextStatus
        alert.status.time = datetime.datetime.now()
        addEvent("Alert changed status from {} to {}".format(previousStatus, nextStatus), str(alert.id))
        if res is not None:
            addEvent("Alert was resolved.",str(alert.id))
            alert.resolved = True
        alert.save()
    else:
        global_init()
        changeState(alertId, nextStatus)


def delAlert(alertId):
    if Data.INIT:
        Alert.objects().filter(id=alertId).delete()
        addEvent("Alert was deleted from the database", str(alertId))
    else:
        global_init()
        delAlert(alertId)


def addMail(addr, **kwargs):
    if Data.INIT:
        if Mail.objects().filter(address=addr).first() is not None:
            return
        mail = Mail()
        level = kwargs.get("lvl", None)
        mail.address = addr
        if level is not None:
            mail.level = level
        mail.save()
        addEvent("Mail {} was added to the database".format(addr), str(mail.id))
    else:
        global_init()
        addMail(addr)
def delMail(addr):
    if Data.INIT:
        Mail.objects().filter(address=addr).delete()
        addEvent("Mail {} was deleted from the database".format(addr), str(addr))
    else:
        global_init()
        delMail(addr)
def getMails():
    if Data.INIT:
        return Mail.objects()
    else:
        global_init()
        return Mail.objects()

def addEvent(description, subId):
    event = Event()
    event.description = description
    event.subjectId = subId
    event.save()

def getEvents():
    return Event.objects()