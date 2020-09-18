#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools
import dash
import dash_core_components as dcc
import dash_html_components as html
import networkx as nx
import plotly.graph_objs as go

import pandas as pd
from colour import Color
from datetime import datetime
from textwrap import dedent as d
import json
import scipy
from flask import Flask, request, jsonify
import random

from requests.auth import HTTPBasicAuth

from Alerts import Alert
import mailer

import requests as rq
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

    @staticmethod
    def restoreLog():
        print("restoring the log")
        try:
            DataHolder.safe_log = open("log.safe", "r")
            for line in DataHolder.safe_log:
                DataHolder.current_log.write(line)
                DataHolder.current_log_virtual.append(line.replace("\n",""))
            DataHolder.current_log.close()
            DataHolder.safe_log.close()
            DataHolder.setup = True
        except:
            print("xD")

    @staticmethod
    def backupLog():
        DataHolder.safe_log = open("log.safe","w")
        for i in DataHolder.current_log_virtual:
            DataHolder.safe_log.write(i.replace("\n","")+"\n")
        DataHolder.safe_log.close()

    @staticmethod
    def addEvent(event):
        #if DataHolder.setup:
            #DataHolder.restoreLog()
        DataHolder.current_log = open("log.current", "a+")
        DataHolder.current_log.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+" "+event.replace("\n","").replace("\t","").replace("                "," ")+"\n")
        DataHolder.current_log_virtual.append(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+" "+event+"\n")
        DataHolder.backupLog()

    @staticmethod
    def getEvents():
        DataHolder.current_log = open("log.current","r")
        toret = []
        for line in DataHolder.current_log:
            toret.append(line)
        toret.reverse()
        return toret

    @staticmethod
    def restoreState():
        alertsFile = open("alerts.db","r")
        for line in alertsFile:
            alert = Alert(0,0,0)
            alert.loadJson(json.loads(line))
            DataHolder.alerts.append(alert)
        alertsFile.close()

    @staticmethod
    def backupAlerts():
        f = open("alerts.db","w")
        for i in DataHolder.alerts:
            f.write(str(i.jstring).replace("'",'"'))
        f.close()

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
    def mailerInit():
        f = open("mail-list",'r')
        for line in f:
            DataHolder.mails.append(line.replace("\n",""))
        f.close()
    @staticmethod
    def send(subject, msg):
        for mail in DataHolder.mails:
            mailer.sendMail(mail,subject,msg)

def getSubjectInfo():
    toret = []
    toret.append(dcc.Markdown(d("##### Details on provided subject")))
    if DataHolder.current_selected_node == None:
        toret.append(dcc.Markdown(d("**Id: **No id provided")))
        toret.append(dcc.Markdown(d("**Connected to: **No id provided")))
        toret.append(dcc.Markdown(d("**Provided by: **No id provided")))
        toret.append(dcc.Markdown(d("**Other information: **No id provided")))
    return toret


def getOptions():
    options = []
    for node in DataHolder.activeNodes:
        options.append({'label':node,'value':node})
    return options

def alerts(slider):
    ret = []
    ret.append(html.Div([dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )]))
    index = 0
    for i in range(len(DataHolder.alerts)):
        if i == 10:
            break
        if DataHolder.alerts[i].severity>=slider[0]:
            tmp =html.Div(
                children=[
                    dcc.Markdown(d("""
                                          {}
                                           """.format(str(DataHolder.alerts[i]))),style={"color":"#4e1175"}),
                    html.Button('OK',id='Corect' + str(i), n_clicks=0,style={"border-color":"white","color":"white","background-color": "#4e1175"}),
                    html.Button("Once",id="Once" + str(i), n_clicks=0,style={"border-color":"white","color":"white","background-color": "#4e1175"}),
                    html.Button("Block",id="Incorrect" + str(i), n_clicks=0,style={"border-color":"white","color":"white","background-color": "#4e1175"}),
                    html.Button("Show", id="Show" + str(i), n_clicks=0, style={"border-color":"white","color":"white","display":"inline-block","background-color":"#900C3F"})
                ]
                )
            ret.append(tmp)
            index+=1
    if index>= 10:
        return ret
    for i in range(10 - index):
        tmp = html.Div(
            children=[
                html.Button('OK', id='Corect' + str(i+index), n_clicks=0,disabled=True, style={"visibility":"hidden"}),
                html.Button("Once", id="Once" + str(i+index), n_clicks=0,disabled=True, style={"visibility":"hidden"}),
                html.Button("Block", id="Incorrect" + str(i+index), n_clicks=0,disabled=True, style={"visibility":"hidden"}),
                html.Button("Show", id="Show" + str(i+index), n_clicks=0,disabled=True, style={"visibility":"hidden"})
            ]
        )
        ret.append(tmp)
    return ret

def getAlertsOKbuttonsInput():
    toret = []
    for i in range(10):
        toret.append(dash.dependencies.Input('Corect'+str(i), 'n_clicks'))
    return toret

def getAlertsAllowbuttonsInput():
    toret = []
    for i in range(10):
        toret.append(dash.dependencies.Input('Once'+str(i), 'n_clicks'))
    return toret
def getAlertsBlockbuttonsInput():
    toret = []
    for i in range(10):
        toret.append(dash.dependencies.Input('Incorrect'+str(i), 'n_clicks'))
    return toret
def getShowButtons():
    toret = []
    for i in range(10):
        toret.append(dash.dependencies.Input('Show'+str(i), 'n_clicks'))
    return toret

# import the css template, and pass the css template into dash
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Autopolicy and Policy Based Routing dashboard"
server = app.server
YEAR=[2010, 2019]
ACCOUNT="A0001"

def obtainTopology():
    try:
        jHosts = None
        jDevices = None
        responseHosts = rq.get("{}hosts".format(DataHolder.ip_ctrl), auth=HTTPBasicAuth("karaf", "karaf"))
        responseDevice = rq.get("{}devices".format(DataHolder.ip_ctrl),auth=HTTPBasicAuth("karaf","karaf"))
        responseLinks = rq.get("{}links".format(DataHolder.ip_ctrl),auth=HTTPBasicAuth("karaf","karaf"))
        jHosts = responseHosts.json()
        jDevices = responseDevice.json()
        jLinks = responseLinks.json()
        return jHosts,jDevices,jLinks
    except:
        return None,None,None

##############################################################################################################################################################
def network_graph(yearRange, AccountToSearch):
    jHosts, jDevices, jLinks = obtainTopology()
    if jHosts == None or jDevices == None:
        DataHolder.activeNodes = []
        edge1 = pd.read_csv('edge1.csv')
        node1 = pd.read_csv('node1.csv')
    else:
        hosts = []
        devices = []
        links = []
        for host in jHosts["hosts"]:
            hosts.append((host["mac"], host["ipAddresses"][0],host["locations"][0]["elementId"]))
        for device in jDevices["devices"]:
            devices.append(device["id"])
        for link in jLinks["links"]:
            links.append((link["src"]["device"],link["dst"]["device"]))
        for host in hosts:
            links.append((host[0],host[2]))
        fileEgdes = open("edge2.csv","w")
        fileEgdes.write("Link,Source,Target\n")
        fileNodes = open("node2.csv","w")
        fileNodes.write("ID,Type,Tag\n")
        for link in links:
            fileEgdes.write("1,{},{}\n".format(link[0],link[1]))
        for edge in devices:
            fileNodes.write("{},fwd,{}\n".format(edge,edge))
        for edge in hosts:
            fileNodes.write("{},host,{}\n".format(edge[0], edge[1]))
        fileEgdes.close()
        fileNodes.close()
        edge1 = pd.read_csv('edge2.csv')
        node1 = pd.read_csv('node2.csv')



    # filter the record by datetime, to enable interactive control through the input box
    #edge1['Datetime'] = "" # add empty Datetime column to edge1 dataframe
    accountSet=set() # contain unique account
    for index in range(0,len(edge1)):
        accountSet.add(edge1['Source'][index])
        accountSet.add(edge1['Target'][index])

    # to define the centric point of the networkx layout
    shells=[]
    shell1=[]
    shell1.append(AccountToSearch)
    shells.append(shell1)
    shell2=[]
    for ele in accountSet:
        if ele!=AccountToSearch:
            shell2.append(ele)
    shells.append(shell2)


    G = nx.from_pandas_edgelist(edge1, 'Source', 'Target', ['Source', 'Target', 'Link'], create_using=nx.MultiDiGraph())
    nx.set_node_attributes(G, node1.set_index('ID')['Type'].to_dict(), 'Type')
    nx.set_node_attributes(G, node1.set_index('ID')['Tag'].to_dict(), 'Tag')
    # pos = nx.layout.spring_layout(G)
    # pos = nx.layout.circular_layout(G)
    # nx.layout.shell_layout only works for more than 3 nodes
    if len(shell2)>1:
        pos = DataHolder.drawFunction(G)
    else:
        pos = nx.drawing.layout.spring_layout(G)
    for node in G.nodes:
        G.nodes[node]['pos'] = list(pos[node])


    if len(shell2)==0:
        traceRecode = []  # contains edge_trace, node_trace, middle_node_trace

        node_trace = go.Scatter(x=tuple([1]), y=tuple([1]), text=tuple([str(AccountToSearch)]), textposition="bottom center",
                                mode='markers+text',
                                marker={'size': 50, 'color': 'LightSkyBlue'})
        traceRecode.append(node_trace)

        node_trace1 = go.Scatter(x=tuple([1]), y=tuple([1]),
                                mode='markers',
                                marker={'size': 50, 'color': 'LightSkyBlue'},
                                opacity=0)
        traceRecode.append(node_trace1)

        figure = {
            "data": traceRecode,
            "layout": go.Layout(title='Interactive Transaction Visualization', showlegend=False,
                                margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                                xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                height=600
                                )}
        return figure


    traceRecode = []  # contains edge_trace, node_trace, middle_node_trace
    ############################################################################################################################################################
    colors = list(Color('LightBlue').range_to(Color('DarkBlue'), len(G.edges())))
    colors = ['rgb' + str(x.rgb) for x in colors]

    index = 0
    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        weight = float(G.edges[edge]['Link']) / max(edge1['Link']) * 10
        if G.nodes[edge[0]]["Type"]=="host" or G.nodes[edge[1]]["Type"]=="host":
            c = '#FF5733'
        else:
            c=colors[index]

        trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                           mode='lines',
                           line={'width': 3},
                           marker=dict(color=c),
                           line_shape='spline',
                           opacity=1)
        traceRecode.append(trace)
        index = index + 1
    ###############################################################################################################################################################

    node_trace = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
                            hoverinfo="text", marker={'size': 20, 'color': 'LightSkyBlue'})

    node_trace_host = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
                            hoverinfo="text", marker={'size': 10, 'color':  '#FF5733'})

    node_trace_search = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
                                 hoverinfo="text", marker={'size': 30, 'color': '#900C3F'})

    index = 0
    for node in G.nodes():
        if "of:" in node:
            DataHolder.activeNodes.append(node)
            DataHolder.activeNodes.sort()
        x, y = G.nodes[node]['pos']
        hovertext = "ID: " + str(node) + "<br>" + "Type: " + str(
            G.nodes[node]['Type'])+"<br>"+"Tag: "+str(G.nodes[node]["Tag"])
        text = node
        if node == AccountToSearch:
            node_trace_search['x'] += tuple([x])
            node_trace_search['y'] += tuple([y])
            node_trace_search['hovertext'] += tuple([hovertext])
            node_trace_search['text'] += tuple([text])

        elif G.nodes[node]["Type"] == "host":
            node_trace_host['x'] += tuple([x])
            node_trace_host['y'] += tuple([y])
            node_trace_host['hovertext'] += tuple([hovertext])
            node_trace_host['text'] += tuple([text])
        elif node != AccountToSearch:
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['hovertext'] += tuple([hovertext])
            node_trace['text'] += tuple([text])

        index = index + 1

    traceRecode.append(node_trace)
    traceRecode.append(node_trace_host)
    traceRecode.append(node_trace_search)
    ################################################################################################################################################################
    middle_hover_trace = go.Scatter(x=[], y=[], hovertext=[], mode='markers', hoverinfo="text",
                                    marker={'size': 10, 'color': 'LightSkyBlue'},
                                    opacity=0)

    index = 0
    for edge in G.edges:
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        hovertext = "From: " + str(G.edges[edge]['Source']) + "<br>" + "To: " + str(
            G.edges[edge]['Target']) + "<br>" + "Link: " + str(
            G.edges[edge]['Link'])
        middle_hover_trace['x'] += tuple([(x0 + x1) / 2])
        middle_hover_trace['y'] += tuple([(y0 + y1) / 2])
        middle_hover_trace['hovertext'] += tuple([hovertext])
        index = index + 1

    traceRecode.append(middle_hover_trace)
    #################################################################################################################################################################
    figure = {
        "data": traceRecode,
        "layout": go.Layout(showlegend=False, hovermode='closest',
                            margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                            xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                            height=600,
                            clickmode='event+select'
                            )}
    return figure
######################################################################################################################################################################
# styles: for right side hover/click component
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

app.layout = html.Div([

    #########################Title
    html.Div([html.H1("Autopolicy and PBF Dashboard")],
             className="row",
             style={'textAlign': "center","color":"#4e1175"}),
    #############################################################################################define the row
    dcc.Tabs([
        dcc.Tab(label='Visualisation', style={"color": "#4e1175"}, children=[
    html.Div(
        className="row",
        children=[
            ##############################################left side two input components
            html.Div(
                className="two columns",
                children=[
                       html.Div(children=[dcc.Markdown(d("""
    #### Alerts
     """),style={"color":"#4e1175","font_size":"60px"})
                                                      ]),
                    html.Div(
                        className="twelve columns",
                        id="alerts-list",
                        children=alerts((0,0)),
                        style={"maxHeight":"230px","overflow-y":"scroll","background-color":"#fcfafd"}
                    ),
                    dcc.Markdown(d("""
                            ##### Alert visibility

                            Set the range of visible alerts.
                            
                            *1 - warnings, 10 - critical errors.*
                            """),style={"color":"#4e1175"}),
                    html.Div(
                        className="twelve columns",
                        children=[
                            dcc.RangeSlider(
                                id='my-range-slider',
                                min=1,
                                max=10,
                                step=1,
                                value=[1, 10],
                                marks={
                                    1: {'label': '1'},
                                    2: {'label': '2'},
                                    3: {'label': '3'},
                                    4: {'label': '4'},
                                    5: {'label': '5'},
                                    6: {'label': '6'},
                                    7: {'label': '7'},
                                    8: {'label': '8'},
                                    9: {'label': '9'},
                                    10: {'label': '10'}
                                }
                            ),
                            html.Br(),
                            html.Div(id='output-container-range-slider')
                        ]
                    ),
                    html.Div(
                [
                            dcc.Markdown(d("""##### Select the graph layout"""),style={"color":"#4e1175"}),
                            dcc.Dropdown(
                                id='demo-dropdown',
                                options=[
                                    {'label': 'Random', 'value': 'random'},
                                    {'label': 'Spring', 'value': 'spring'},
                                    {'label': 'Spectral', 'value': 'spectral'},
                                    {'label': 'Shell', 'value': 'shell'},
                                    {'label': 'Kamanda-Kawaii', 'value': 'kawai'},
                                    {'label': 'Fruchterman-Reingold', 'value': 'f'}

                                ],
                                value='kawai',style={"color":"#4e1175"}
                            ),
                            html.Div(id='dd-output-container')

                                ]
                    )
                ]
            ),

            ############################################middle graph component
            html.Div(
                className="eight columns",
                children=[dcc.Graph(id="my-graph",
                                    figure=network_graph(YEAR, ACCOUNT))],
            ),

            #########################################right side two output component
            html.Div(

                className="two columns",
                children=[
                        dcc.Markdown(d("""
                            #### Current selected alert
                            """),style={"color":"#4e1175"}),
                        html.Div(
                        className='twelve columns',
                        id="show",
                        children=[],
                        style={"maxHeight":"300px","overflow-y":"scroll", "background-color":"#fcfafd"}
                        ),
                        dcc.Markdown(d("""
                            #### Policy and Properties
                            """), style={"color":"#4e1175"}),
                    html.Div(
                        className='twelve columns',
                        children=[
                            html.Pre(id='hover-data', style=styles['pre'])
                        ],
                        style={"maxHeight": "200px", "overflow-y":"scroll", "background-color":"#fcfafd"})
                ]
            )
        ]
    ),

    html.Div(id="okbuttonsok"),html.Div(id="allow-once"),html.Div(id="block"),
    dcc.Markdown(d("""
                          #### Logged activity
                          """), style={"color": "#4e1175"}),
    html.Div(
        className='twelve columns',
        children=[
            html.Pre(id='log', style=styles['pre']),
            dcc.Interval(
                id='interval-component-log',
                interval=20 * 1000,  # in milliseconds
                n_intervals=0)
        ],
        style={"maxHeight": "190px", "overflow-y": "scroll","background-color":"#fcfafd" })
    ]),

        dcc.Tab(label='Nodes management', style={"color": "#4e1175"}, children=[
            html.Div(
                className="row",
                children=[
                    html.Div(
                        className="four columns",
                        children=[
                        dcc.Markdown(d("###### Provide the ID of the node: "),style={"color": "#4e1175"}),
                        dcc.Input(id="node_id"
                                  ,type="text",placeholder="of:000000000000001 or 00:00:00:00:00:01", style={"color": "#4e1175","width":"100%"}
                                  ),
                        dcc.Markdown(d("###### Type"),style={"color": "#4e1175"}),
                        dcc.Dropdown(
                            id='type-dropdown',
                            options=[
                                {'label': 'Host', 'value': 'host'},
                                {'label': 'Forwarder', 'value': 'fwd'}
                            ],
                            value='fwd', style={"color": "#4e1175"}),
                        html.Div(children=[
                            html.Button('Add node',id='AddNode', n_clicks=0,
                                        style={"border-color":"white","color":"white","background-color": "#4e1175","width":"33.33%"}),
                            html.Button('Edit node',id='EditNode', n_clicks=0,
                                        style={"border-color":"white","color":"white","background-color": "#4e1175","width":"33.33%"}),
                            html.Button("Delete Node", id="delNode", n_clicks=0,
                                        style={"border-color":"white","color":"white","display":"inline-block","background-color":"#900C3F","width":"33.34%"})]),


                        ]
                    ),
            html.Div(
                style={"background-color":"#fcfafd"},
                className="four columns",
                children=[html.Div(className="twelve columns", children=[
                    dcc.Markdown(d("###### List of posible connections: "),style={"color": "#4e1175"}),

dcc.Checklist(
    options=getOptions(),style={"color": "#4e1175"})

                ])
                          ]
            ),

            html.Div( className="four columns",
                children=getSubjectInfo(),style={"color": "#4e1175"})


                ])
        ])



    ])])

###################################callback for left side components
################################callback for right side components
@app.callback(
    dash.dependencies.Output('hover-data', 'children'),
    [dash.dependencies.Input('my-graph', 'clickData')])
def display_hover_data(hoverData):
    try:
        type = ""
        tmp=json.dumps(hoverData['points'][0]["hovertext"],indent=2)
        idindex = tmp.find("ID: ")
        if idindex != -1:
            idendindex = tmp.find("<")
            tmp = tmp[idindex+4:idendindex]
            toret = tmp
            if toret.count(":")>1:
                type = "host"
            else:type="fwd"
        else:
            type="link"
            idindex = tmp.find("From: ")+len("From: ")
            idendindex = tmp.find("<")
            tmp1 = tmp[idindex:idendindex]
            tmp1+="-"
            idindex = tmp.find("To: ")+len("To: ")
            idendindex = tmp.find("<", idindex)
            tmp1+=tmp[idindex:idendindex]
            toret = tmp1

    except:
        toret=dcc.Markdown(d("Nothing selected"),style={"color":"#4e1175"})
    try:
        response = rq.get("{}rnn/SRE/autopolicy/data/{}/".format(DataHolder.ip_ctrl,toret),auth=HTTPBasicAuth("karaf","karaf"))

        if response.status_code != 200:
            return dcc.Markdown(d("Nothing selected"),style={"color":"#4e1175"})
    except:
        return dcc.Markdown(d("Nothing selected"), style={"color": "#4e1175"})
    #print(response.text)
    #DataHolder.addEvent("Details for the {} subject.".format(toret))

    return DataHolder.getInfoFromString(response.text,type)

@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
    [dash.dependencies.Input('demo-dropdown', 'value'),dash.dependencies.Input('interval-component-log', 'n_intervals')])
def update_output123(value,interval):
    if value=="random":
        DataHolder.drawFunction = nx.drawing.layout.random_layout
    if value=="spectral":
        DataHolder.drawFunction = nx.drawing.layout.spectral_layout
    if value=="spring":
        DataHolder.drawFunction = nx.drawing.layout.spring_layout
    if value=="shell":
        DataHolder.drawFunction = nx.drawing.layout.shell_layout
    if value=="kawai":
        DataHolder.drawFunction = nx.drawing.layout.kamada_kawai_layout
    if value=="f":
        DataHolder.drawFunction = nx.drawing.layout.fruchterman_reingold_layout
    #print("update")
    return network_graph(YEAR,ACCOUNT)

@server.route("/alert/", methods=['POST'])
def postAlert():
    jBody = request.json
    try:
        toSend = "We are sending this email to let you know that the Autopolicy mechanism detected an Alert - some of your devices are not" \
                 "behaving the way they should. Below you will find the details of the alert. If that's a false alert you can" \
                 "access your autopolicy dashboard and let us know by clicking false alert button for that alert. Here are the details" \
                 " for that alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                 "\nAutopolicy Provider".format(jBody["explanation"],jBody["severity"],jBody["subject"],jBody["details"],datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        DataHolder.send("Received an alert from the AP",str(toSend))
        a = Alert(0,0,0)
        a.loadJson(jBody)
        fAlerts = open("alerts.db","a+")
        fAlerts.write(str(jBody).replace("'",'"')+"\n")
        fAlerts.close()

    except:
        return "Provided JSON was not corect"

    DataHolder.alerts.append(a)
    DataHolder.addEvent("Added the alert: "+str(a)+"Waiting for the user confirmation.")
    return 'OK'

@app.callback(dash.dependencies.Output('alerts-list', 'children'), [dash.dependencies.Input('interval-component', 'n_intervals'),dash.dependencies.Input('my-range-slider','value')])
def update(vlaues, slider):
    #print("update...")
    return alerts(slider)

@app.callback(dash.dependencies.Output('log', 'children'), [dash.dependencies.Input('interval-component-log', 'n_intervals')])
def update_log(vlaues):
    return DataHolder.getEvents()

@app.callback(dash.dependencies.Output('okbuttonsok', 'children'),getAlertsOKbuttonsInput())
def okbuttons(*args):
    index = -1
    for i in range(len(args)):
        if args[i]==1:
            index = i
            break
    if index != -1:
        DataHolder.alerts[index].ok()
        DataHolder.addEvent("Accepted the mitigation of the alert: " + str(DataHolder.alerts[index]))

        try:
            toSend = "The alert was stated as a ok alert. The mitigation action taken by that alert will be carried on." \
                     "The OK button was pressed " \
                     "for the alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(DataHolder.alerts[index].explanation, DataHolder.alerts[index].severity, DataHolder.alerts[index].id,
                                                    DataHolder.alerts[index].details, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            DataHolder.send("Received an alert from the AP", str(toSend))
        except:
            return ""
        DataHolder.alerts.remove(DataHolder.alerts[index])
    #print(str(args))
    return ""
@app.callback(dash.dependencies.Output('allow-once', 'children'),getAlertsAllowbuttonsInput())
def allow(*args):
    index = -1
    for i in range(len(args)):
        if args[i]==1:
            index = i
            break
    if index != -1:
        DataHolder.alerts[index].allow()
        DataHolder.addEvent("Allowed once for the alert: "+str(DataHolder.alerts[index]))

        try:
            toSend = "The alert was allowed only once. The mitigation action taken by that alert will be carried on after today." \
                     "The Allow button was pressed " \
                     "for the alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(DataHolder.alerts[index].explanation, DataHolder.alerts[index].severity, DataHolder.alerts[index].id,
                                                    DataHolder.alerts[index].details, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            DataHolder.send("Received an alert from the AP", str(toSend))
        except:
            return ""
        DataHolder.alerts.remove(DataHolder.alerts[index])

    #print(str(args))
    return ""

@app.callback(dash.dependencies.Output('block', 'children'),getAlertsBlockbuttonsInput())
def allow(*args):
    index = -1
    for i in range(len(args)):
        if args[i]==1:
            index = i
            break
    if index != -1:
        DataHolder.alerts[index].block()
        DataHolder.addEvent("Allowed all the time for the alert: " + str(DataHolder.alerts[index]))

        try:
            toSend = "The alert was marked as an invalid alert. The mitigation action taken by that alert will NOT be carried out." \
                     "The Block button was pressed " \
                     "for the alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(DataHolder.alerts[index].explanation, DataHolder.alerts[index].severity, DataHolder.alerts[index].id,
                                                    DataHolder.alerts[index].details, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            DataHolder.send("Received an alert from the AP", str(toSend))
        except:
            return ""

        DataHolder.alerts.remove(DataHolder.alerts[index])
    #print(str(args))
    return ""

@app.callback(dash.dependencies.Output('show', 'children'),getShowButtons())
def show(*args):
    index = -1
    for i in range(len(args)):
        if args[i]==1:
            index = i
            break
    data = DataHolder.currentAlert
    if index != -1:
        data = DataHolder.alerts[index].show()
        DataHolder.addEvent("See the details of the alert: " + str(DataHolder.alerts[index]))
        DataHolder.currentAlert = data
        ##DataHolder.alerts.remove(DataHolder.alerts[index])
    #print(str(args))
    return data

if __name__ == '__main__':
    DataHolder.restoreLog()
    DataHolder.restoreState()
    DataHolder.mailerInit()
    DataHolder.ip_ctrl = sys.argv[1]
    app.run_server(debug=True,host="0.0.0.0",port=1111)
    DataHolder.backupLog()
    DataHolder.backupAlerts()