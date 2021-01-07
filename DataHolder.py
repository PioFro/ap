from textwrap import dedent as d
import dash_core_components as dcc
import networkx as nx
import DBDashWrapper as wrap
import DataProviderService as dps
import mailer
import json
import sys

class DataHolder:
    drawFunction = nx.drawing.layout.random_layout
    alerts = []
    currentAlert = dcc.Markdown(d("Nothing selected"),style={"color":"#4e1175"})
    safe_log = open("log.safe","r")
    current_log=open("log.current","w")
    current_log_virtual = []
    setup = False
    mails = []
    ip_ctrl="http://localhost:8181/onos/v1/"
    activeNodes=[]
    current_selected_node = None
    path = None
    refreshTopology = True
    out_ip=sys.argv[3]
    tmp_fig=None
    pathsTuples = [("of:0000000000000009","of:0000000000000002"),("of:0000000000000005","of:0000000000000003"),("of:0000000000000007","of:0000000000000005"),("of:0000000000000001","of:0000000000000004"),("of:0000000000000001","of:0000000000000009")]
    paths = []

    @staticmethod
    def randomizeTuples(numberOfTuples):
        print("randomize tuples")



    @staticmethod
    def getEvents():
        return wrap.getLogDCCWrapped()

    @staticmethod
    def restoreState():
        DataHolder.alerts = []
        for alert in dps.getAlerts():
            if alert not in DataHolder.alerts:
                DataHolder.alerts.append(alert.id)

        topology = dps.getSubjects()
        edgesFile = open("edge1.csv", "w")
        edgesFile.write("Link,Source,Target\n")
        nodesFile = open("node1.csv", "w")
        nodesFile.write("ID,Type,Tag\n")
        edgesFile2 = open("edge2.csv", "w")
        edgesFile2.write("Link,Source,Target\n")
        nodesFile2 = open("node2.csv", "w")
        nodesFile2.write("ID,Type,Tag\n")

        for device in topology:
            nodesFile.write("{},{},{}\n".format(device.subject, device.type, device.tag))
            nodesFile2.write("{},{},{}\n".format(device.subject, device.type, device.tag))
            for connection in device.connections:
                edgesFile.write("{},{},{}\n".format(connection.capacity, connection.src, connection.dst))
                edgesFile2.write("{},{},{}\n".format(connection.capacity, connection.src, connection.dst))
        edgesFile.close()
        nodesFile.close()
        edgesFile2.close()
        nodesFile2.close()



    @staticmethod
    def getInfoFromString(jstring,type):
        toret = []

        if type == "fwd":
            toret.append(dcc.Markdown(d('''##### Properites\n\n'''),style={"color":"#4e1175"}))
            tmp = json.loads(jstring)
            for i in tmp["properties"]:
                toret.append(dcc.Markdown(d("**"+str(i["name"])+"** : "+str(i["value"])+"\n"),style={"color":"#4e1175"}))
        if type == "host":
            tmp = json.loads(jstring)
            toret.append(dcc.Markdown(d("###### Policy\n\n"),style={"color":"#4e1175"}))
            try:
                for i in tmp["criteria manager"]:
                    toret.append(dcc.Markdown(d("The **{}s** must fulfil \n**{} = {}**".format(str(i["subject"]),str(i["name"]),str(i["value"]))+'\n'),style={"color":"#4e1175"}))
            except:
                toret.append(dcc.Markdown(d("This user has no Policy declared"),style={"color":"#4e1175"}))
            if len(tmp["criteria manager"]) == 0:
                toret.append(dcc.Markdown(d("This user has no Policy declared"), style={"color": "#4e1175"}))
            toret.append(dcc.Markdown(d("\n\n###### Autopolicy Profile\n\n"),style={"color":"#4e1175"}))
            try:
                for i in tmp["autopolicy profile"]["from device"]["allow"]:
                    ap = str(i).replace("dst ", "").split(" ")
                    toret.append(dcc.Markdown(d("**Allowed IP:** "+ap[0]+" \n"),style={"color":"#4e1175"}))
                    toret.append(dcc.Markdown(d("**Allowed protocol: **" + ap[1] + " \n"),style={"color":"#4e1175"}))
                    toret.append(dcc.Markdown(d("**Allowed ports: **" + ap[2] + " \n"),style={"color":"#4e1175"}))
                    toret.append(dcc.Markdown(d("**Max Bitrate: **" + ap[3] + " [Mb/s] \n"),style={"color":"#4e1175"}))
                    toret.append("---------------------------------------------------- \n")
            except:
                toret.append(dcc.Markdown(d("**No profile declared**"),style={"color":"#4e1175"}))
            toret.append(dcc.Markdown(d("\n\n##### Autopolicy\n\n##### Identity\n\n"),style={"color":"#4e1175"}))
            toret.append(dcc.Markdown(d("**Manufacturer: **{}\n**Device: **{}\n**Revision: **{}\n".format(tmp["autopolicy identity"]["manufacturer"], tmp["autopolicy identity"]["device"], tmp["autopolicy identity"]["revision"])),style={"color":"#4e1175"}))
        if type == "link":
            toret.append(dcc.Markdown(d('''##### Properites\n\n'''), style={"color": "#4e1175"}))
            tmp = json.loads(jstring)
            for i in tmp["properties"]:
                toret.append(dcc.Markdown(d("**"+str(i["name"])+"** : "+ str(i["value"]) + "\n"), style={"color": "#4e1175"}))

        return toret

    @staticmethod
    def send(subject, msg):
        for mail in dps.getMails():
            mailer.sendMail(mail.address,subject,msg)

    @staticmethod
    def checkPath(edge1, egde2):
        isOK = False
        for i in range(len(DataHolder.path)-1):
            if (edge1 == DataHolder.path[i] and egde2 == DataHolder.path[i+1]):
                isOK = True
        return isOK