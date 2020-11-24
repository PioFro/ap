import requests as rq
from requests.auth import HTTPBasicAuth
import json
from DataHolder import DataHolder
import DataProviderService as dps

class Connector:
    ControllerURL="0.0.0.0"
    prevX=[1]
    prevY=[1]
    prevKey = ""
    window=10
    jcnm = ""
    isSameRq = False
    isFirstConnection = True
    updateTime = 5
    initNumberOfPackets = 0
    initNumberOfBytes = 0

    @staticmethod
    def GetLatestInfo(type, id, param):
        if len(Connector.prevY) > Connector.window:
            Connector.prevY.remove(Connector.prevY[0])
        if "{}{}{}".format(type,id,param) != Connector.prevKey:
            Connector.prevKey="{}{}{}".format(type,id,param)
            Connector.prevX=[1]
            Connector.prevY=[1]
            Connector.isFirstConnection = True
        if type=="link":
            type = "path"
            id = id.replace("-"," to ")

        if type=="path":
            path = Connector.getBestPath(id)
            if param == "delay":
                try:
                    y = 0
                    for fwdIter in range(len(path)-1):
                        y+=Connector.getDelayInfoOnLink(path[fwdIter],path[fwdIter+1])
                    Connector.prevY.append(y)
                    Connector.prevX.append(Connector.prevX[-1]+Connector.updateTime)
                except:
                    print("Connection to the url : {} lost".format(DataHolder.ip_ctrl))
            if param=="packets" or param=="bytes":
                hostsSrc = dps.getHostsConnectedToForwarder(path[0])
                hostsDst = dps.getHostsConnectedToForwarder(path[-1])
                flows = Connector.getFlowsOnDevice(path[0])
                p = 0
                b = 0
                for src in hostsSrc:
                    for dst in hostsDst:
                        for flow in flows:
                            dstOK = False
                            srcOK = False
                            for crit in flow[2]["criteria"]:
                                if crit["type"]=="IPV4_DST" and crit["ip"]==dst[1]+"/32":
                                    dstOK = True
                                if crit["type"]=="IPV4_SRC" and crit["ip"]==src[1]+"/32":
                                    srcOK = True
                            if dstOK and srcOK:
                                p+=flow[0]
                                b+=flow[1]
                if Connector.isFirstConnection:
                    Connector.initNumberOfPackets = p
                    Connector.initNumberOfBytes=b
                    Connector.isFirstConnection = False
                if param == "packets":
                    Connector.prevY.append(float(p-Connector.initNumberOfPackets)/Connector.updateTime)
                    Connector.initNumberOfPackets = p
                else:
                    Connector.prevY.append(float(b-Connector.initNumberOfBytes) / Connector.updateTime)
                    Connector.initNumberOfBytes = b
                Connector.prevX.append(Connector.prevX[-1] + Connector.updateTime)
                return Connector.prevX,Connector.prevY
        if type == "fwd":
            if param=="packets" or param=="bytes" or param=="flows":
                flows = Connector.getFlowsOnDevice(id)
                p=0
                b=0
                if param=="flows":
                    Connector.prevY.append(len(flows))
                if param=="packets" or param=="bytes":
                   for flow in flows:
                       p+=flow[0]
                       b+=flow[0]
                   if Connector.isFirstConnection:
                        Connector.initNumberOfPackets = p
                        Connector.initNumberOfBytes=b
                        Connector.isFirstConnection=False
                   if param == "packets":
                       Connector.prevY.append(float(p - Connector.initNumberOfPackets) / Connector.updateTime)
                       Connector.initNumberOfPackets = p
                   else:
                       Connector.prevY.append(float(b - Connector.initNumberOfBytes) / Connector.updateTime)
                       Connector.initNumberOfBytes = b
                Connector.prevX.append(Connector.prevX[-1] + Connector.updateTime)
                return Connector.prevX, Connector.prevY
            if param =="delay":
                sub = dps.getSubjectById(id)
                i = 0
                sum = 0.0
                for con in sub.connections:
                    tmp = Connector.getDelayInfoOnLink(sub.subject,con.dst)
                    sum +=tmp
                    i += 1
                Connector.prevY.append(sum/i)
                Connector.prevX.append(Connector.prevX[-1] + Connector.updateTime)

        if type=="host":
            hst = dps.getSubjectById(id)
            fwd = hst.connections[0].dst
            pout =0
            pin = 0
            bout = 0
            byin = 0
            flows = Connector.getFlowsOnDevice(fwd)
            for flow in flows:
                for crit in flow[2]["criteria"]:
                    if crit["type"] == "IPV4_DST" and crit["ip"] == hst.tag + "/32":
                        pin+=flow[0]
                        byin+=flow[1]
                    if crit["type"] == "IPV4_SRC" and crit["ip"] == hst.tag + "/32":
                        pout+=flow[0]
                        bout+=flow[1]
            if Connector.isFirstConnection:
                if (param=="outbytes" or param=="outpakcket"):
                    Connector.initNumberOfPackets = pout
                    Connector.initNumberOfBytes = bout
                else:
                    Connector.initNumberOfPackets=pin
                    Connector.initNumberOfBytes=byin

                Connector.isFirstConnection = False
            if param == "outpackets":
                Connector.prevY.append(float(pout - Connector.initNumberOfPackets) / Connector.updateTime)
                Connector.initNumberOfPackets = pout
            elif param == "outbytes":
                Connector.prevY.append(float(bout - Connector.initNumberOfBytes) / Connector.updateTime)
                Connector.initNumberOfBytes = bout
            elif param == "inpackets":
                Connector.prevY.append(float(pin - Connector.initNumberOfPackets) / Connector.updateTime)
                Connector.initNumberOfPackets = pin
            elif param == "inbytes":
                Connector.prevY.append(float(byin - Connector.initNumberOfBytes) / Connector.updateTime)
                Connector.initNumberOfBytes = byin

            Connector.prevX.append(Connector.prevX[-1] + Connector.updateTime)
        Connector.isSameRq=False
        return Connector.prevX,Connector.prevY
    @staticmethod
    def getBestPath(id):
        path = []
        res = rq.get(
            "{}SRE/path/getbest/{}/{}/".format(DataHolder.ip_ctrl.replace("/v1/", "/rnn/"), id.split(" to ")[0],id.split(" to ")[1]),
            auth=HTTPBasicAuth("karaf", "karaf"))
        for node in json.loads(res.text)["path"]:
            strNode = "of:" + ((16 - (int(node / 10) + 1)) * "0") + str(node)
            path.append(strNode)
        return path

    @staticmethod
    def getDelayInfoOnLink(src, dst):
        delay = 0
        if not Connector.isSameRq:
            Connector.isSameRq = True
            res = rq.get("{}SRE/cnm".format(DataHolder.ip_ctrl.replace("/v1/", "/rnn/")), auth=HTTPBasicAuth("karaf", "karaf"))
            Connector.jcnm = json.loads(res.text)
        for fwd in Connector.jcnm["cnm"]["topology"]["devices"]:
            if fwd["id"] == src:
                for link in fwd["links"]:
                    if link["device id"] == dst:
                        return float(link["qos parameter"])

    @staticmethod
    def getFlowsOnDevice(fwd):
        res = rq.get("{}flows/{}".format(DataHolder.ip_ctrl,fwd),
                     auth=HTTPBasicAuth("karaf", "karaf"))
        flowsEntries = json.loads(res.text)
        flows = []
        for flow in flowsEntries["flows"]:
            flows.append((int(flow["packets"]),int(flow["bytes"]),flow["selector"]))
        return flows