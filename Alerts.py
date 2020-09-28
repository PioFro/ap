from datetime import datetime
import json
import dash_core_components as dcc

class Alert:
    LastUsedID = 0

    def __init__(s, subject, explanation, severity):
        s.subject = subject
        s.explanation = explanation
        s.severity = severity
        s.time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        s.id = Alert.LastUsedID
        s.details = "No details provided"
        Alert.LastUsedID+=1
        s.jstring = ""


    def loadJson(s, jstring):
        s.subject = jstring["subject"]
        s.explanation = jstring["explanation"]
        s.severity = jstring["severity"]
        try:
            s.details = jstring["details"]
        except:
            s.details = "No details provided"
        s.id = Alert.LastUsedID
        Alert.LastUsedID += 1
        s.time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        s.jstring=jstring
    def __str__(s):
        return """
        **Subject:** {}
        
        **Explanation:** {}
        
        **Time:** {}
        """.format(s.subject, s.explanation,s.time)

    def ok(self):
        print("OKEYED the "+str(self))

    def allow(self):
        print("allowe once"+str(self))
    def block(self):
        print("Allowed all times")