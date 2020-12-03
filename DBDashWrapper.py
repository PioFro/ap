import dash_core_components as dcc
import dash_html_components as html
import DataProviderService as dps
from textwrap import dedent as d
from Subject import Subject

def getMailsDCCWrapped():
    mails = dps.getMails()
    dccWraped = []
    for mail in mails:
        dccWraped.append(dcc.Markdown(d(mail.address)))
    return dccWraped

def getLogDCCWrapped():
    events = dps.getEvents()
    dccWrapped = []
    for event in events:
        dccWrapped.append(dcc.Markdown(d("""**Time: ** {}, **Description: **{}, **ID: **{}""".format(event.time, event.description,event.subjectId)),style={"color":"#4e1175"}))
    dccWrapped.reverse()
    return dccWrapped

def getConnectionsDCCWrapped(subject: Subject):
    dccWrapped = []
    for con in subject.connections:
        dccWrapped.append(dcc.Markdown(d(
            """
            ** src:** {}, **dst:** {}, **capacity:** {} **Mb/s** 
            """.format(con.src, con.dst, con.capacity)
        )))
    return dccWrapped
