#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import setuptools
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
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
import DataProviderService as dps
import DBDashWrapper as wrap
import Connection
from Subject import Subject
import re
from DataHolder import DataHolder
from Connector import Connector


def getFigureWithOptions(type = None, id=None, param = None):
    tr = []
    x=[]
    y=[]
    if type is None or id is None or param is None:
        a = random.random()
        title = "Placeholder"
        for i in range(-1000,1000):
            x.append(i)
            y.append(a*i*i + 2*i +1)
        tr.append(go.Scatter(x=x, y=y))
    else:
        title = "{} for {} with id {}".format(param,type,id)
        x,y = Connector.GetLatestInfo(type,id,param)
        tr.append(go.Scatter(x=x, y=y))

    lay = go.Layout(title=title, showlegend=False,
                            margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                            xaxis={'showgrid': True, 'zeroline': True, 'showticklabels': True},
                            yaxis={'showgrid': True, 'zeroline': True, 'showticklabels': True},
                            height=400
                            )
    figure2 = {
        "data": tr,
        "layout": lay}
    DataHolder.tmp_fig = figure2
    return figure2


def topologyChanged(links, hosts, forwarders):
    try:
        #dps.delSubjects()
        subjects = list(dps.getSubjects())
        for subject in subjects:
            hostDel = False
            fwdDel = False
            for link in links.copy():
                if link[0] == subject.subject:
                    for con in subject.connections:
                        if con.src == link[0] and con.dst == link[1]:
                            links.remove(link)
            for host in hosts.copy():
                if host[0]==subject.subject:
                    hosts.remove(host)
                    hostDel = True
            if not hostDel:
                for forwarder in forwarders.copy():
                    if forwarder==subject.subject:
                        forwarders.remove(forwarder)
                        fwdDel = True

        if len(hosts)==0 and len(forwarders) == 0 and len(links)==0:
                return False

        if len(hosts)!=0:
            for host in hosts:
                cons = []
                for link in links.copy():
                    if link[0]==host[0]:
                        con = Connection.Connection()
                        con.capacity = 1
                        con.src = link[0]
                        con.dst = link[1]
                        cons.append(con)
                        links.remove(link)
                dps.addSubject(host[0], host[1], "host", cons)
        if len(forwarders) != 0:
            for fwd in forwarders:
                cons = []
                for link in links.copy():
                    if link[0]==fwd:
                        con = Connection.Connection()
                        con.capacity = 1
                        con.src = link[0]
                        con.dst = link[1]
                        cons.append(con)
                        links.remove(link)
                dps.addSubject(fwd, fwd, "fwd", cons)
        if len(links) != 0:
            for link in links:
                sub = dps.getSubjectById(link[0])
                con = Connection.Connection()
                con.capacity = 1
                con.src = sub.subject
                con.dst = link[1]
                sub.connections.append(con)
                sub.save()
        return True
    except:
        return False

def getPathBetween(src, dst):
    response = rq.get("{}SRE/path/getbest/{}/{}/".format(DataHolder.ip_ctrl.replace("/v1/", "/rnn/"), src, dst),
                      auth=HTTPBasicAuth("karaf", "karaf"))
    if response.status_code is not 200:
        DataHolder.path = None
        return None
    DataHolder.path = []
    for node in json.loads(response.text)["path"]:
        strNode = "of:"+((16-(int(node/10)+1))*"0")+str(node)
        DataHolder.path.append(strNode)

    return DataHolder.path

def getSubjectInfo(subject: Subject):
    toret = []
    toret.append(dcc.Markdown(d("##### Details on provided subject")))
    if subject is None:
        toret.append(dcc.Markdown(d("###### **No id provided**")))
        return toret
    if subject.subject is not None:
        toret.append(dcc.Markdown(d("###### **Identifier: ** \n"+subject.subject)))
        toret.append(dcc.Markdown(d("###### **Connected to: **")))
        toret.extend(wrap.getConnectionsDCCWrapped(subject))
        toret.append(dcc.Markdown(d("###### **Provided by: ** \nSerIoT")))
        toret.append(dcc.Markdown(d("###### **Other information: **\n"+ subject.tag)))
    else:
        toret.append(dcc.Markdown(d("###### **No id provided**")))
    return toret


def getOptions(more = False):
    options = []
    keys = ""
    for node in dps.getSubjects():
        options.append({'label':node.subject,'value':node.subject})
        if more:
            for permu in dps.getSubjects():
                if permu.subject != node.subject and str(permu.subject).count(":")<3 and str(node.subject).count(":")<3:
                    options.append({"label":"{} to {}".format(permu.subject, node.subject), "value":"{} to {}".format(permu.subject, node.subject)})
            for con in node.connections:
                if  "{}-{}".format(con.src,con.dst) not in keys:
                    keys+="{}-{}".format(con.src,con.dst)+" "
                    opt={"label":"{}-{}".format(con.src,con.dst),"value":"{}-{}".format(con.src,con.dst)}
                    options.append(opt)
    return options

def alerts(slider):
    DataHolder.restoreState()
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
        if dps.getAlert(DataHolder.alerts[i]).severity>=slider[0]:
            tmp =html.Div(
                children=[
                    dcc.Markdown(d("""
                                          {}
                                           """.format(str(dps.getAlert(DataHolder.alerts[i])))),style={"color":"#4e1175"}),
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
        print("{}hosts".format(DataHolder.ip_ctrl))
        responseHosts = rq.get("{}hosts".format(DataHolder.ip_ctrl), auth=HTTPBasicAuth("karaf", "karaf"))
        print("Response Hosts: "+ responseHosts.text)
        responseDevice = rq.get("{}devices".format(DataHolder.ip_ctrl),auth=HTTPBasicAuth("karaf","karaf"))
        print("Response Devices"+ responseDevice.text)
        responseLinks = rq.get("{}links".format(DataHolder.ip_ctrl),auth=HTTPBasicAuth("karaf","karaf"))
        print("Response Links :" +responseLinks.text)
        jHosts = responseHosts.json()
        jDevices = responseDevice.json()
        jLinks = responseLinks.json()
        return jHosts,jDevices,jLinks
    except:
        return None,None,None

##############################################################################################################################################################
def network_graph(yearRange, AccountToSearch, sdn):
    if not sdn:
        if DataHolder.refreshTopology:
            DataHolder.refreshTopology = False
            topology = dps.getSubjects()
            edgesFile = open("edge1.csv","w")
            edgesFile.write("Link,Source,Target\n")
            nodesFile = open("node1.csv","w")
            nodesFile.write("ID,Type,Tag\n")

            for device in topology:
                nodesFile.write("{},{},{}\n".format(device.subject,device.type,device.tag))
                for connection in device.connections:
                    edgesFile.write("{},{},{}\n".format(connection.capacity,connection.src, connection.dst))

            edgesFile.close()
            nodesFile.close()
        edge1 = pd.read_csv('edge1.csv')
        node1 = pd.read_csv('node1.csv')
    else:
        jHosts, jDevices, jLinks = obtainTopology()
        if jHosts == None or jDevices == None or jLinks == None:
            print("There is no response from the SDN topology provider")
        else:
            hosts = []
            devices = []
            links = []
            for host in jHosts["hosts"]:
                try:
                    hosts.append((host["mac"], host["ipAddresses"][0],host["locations"][0]["elementId"]))
                except:
                    print("there are some hosts without an IP address. Skipping...")
            for device in jDevices["devices"]:
                devices.append(device["id"])
            for link in jLinks["links"]:
                links.append((link["src"]["device"],link["dst"]["device"]))
            for host in hosts:
                links.append((host[0],host[2]))

            if topologyChanged(links, hosts, devices):
                topology = dps.getSubjects()
                fileEgdes = open("edge2.csv","w")
                fileEgdes.write("Link,Source,Target\n")
                fileNodes = open("node2.csv","w")
                fileNodes.write("ID,Type,Tag\n")
                for device in topology:
                    fileNodes.write("{},{},{}\n".format(device.subject, device.type, device.tag))
                    for connection in device.connections:
                        fileEgdes.write("{},{},{}\n".format(connection.capacity, connection.src, connection.dst))
                fileEgdes.close()
                fileNodes.close()

        edge1 = pd.read_csv('edge2.csv')
        node1 = pd.read_csv('node2.csv')



    # filter the record by datetime, to enable interactive control through the input box
    #edge1['Datetime'] = "" # add empty Datetime column to edge1 dataframe
    DataHolder.activeNodes = []
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
            c = "#1a936b"
        else:
            c=colors[index]
        if DataHolder.path is not None:
            if DataHolder.checkPath(edge[0], edge[1]):
                c = "#e8fc03"

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
                            hoverinfo="text", marker={'size': 20, 'color':  "#1a936b"})

    node_trace_search = go.Scatter(x=[], y=[], hovertext=[], text=[], mode='markers+text', textposition="bottom center",
                                 hoverinfo="text", marker={'size': 30, 'color': "#e8fc03"})

    index = 0
    for node in G.nodes():
        if "of:" in node:
            DataHolder.activeNodes.append(node)
            DataHolder.activeNodes.sort()
        x, y = G.nodes[node]['pos']
        hovertext = "ID: " + str(node) + "<br>" + "Type: " + str(
            G.nodes[node]['Type'])+"<br>"+"Tag: "+str(G.nodes[node]["Tag"])
        text = node
        if DataHolder.path is not None:
            if node in DataHolder.path:
                node_trace_search['x'] += tuple([x])
                node_trace_search['y'] += tuple([y])
                node_trace_search['hovertext'] += tuple([hovertext])
                node_trace_search['text'] += tuple([text])
                AccountToSearch = node

        if G.nodes[node]["Type"] == "host":
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
             style={'textAlign': "center","color":"#4e1175","background-color":"#fcfafd"}),
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
                                    figure=network_graph(YEAR, ACCOUNT,False))],
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

    html.Div(id="pathselectorsrc", children=
             [
                 dcc.Markdown(d("#### Select source")),
                 dcc.Dropdown(options=getOptions(),id="srcpath")
             ],style={"color":"#4e1175"}),
    html.Div(id="pathselectordst", children=
             [
                 dcc.Markdown(d("####  Select destination")),
                 dcc.Dropdown(options=getOptions(),id="dstpath")
             ],style={"color":"#4e1175"}),
    html.Div(
        className='twelve columns',
        children=[
        dcc.Markdown(d("""
                          #### Logged activity
                          """), style={"color": "#4e1175"}),
            html.Pre(id='log', style=styles['pre']),
            dcc.Interval(
                id='interval-component-log',
                interval=1 * 1000,  # in milliseconds
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
                        dcc.Markdown(d("###### Provide the tag of the node \n\n For hosts this is an IP address."),style={"color": "#4e1175"}),
                        dcc.Input(id="node_tag"
                                  ,type="text",placeholder="OF forwarder 1 or 10.0.1.1/24", style={"color": "#4e1175","width":"100%"}
                                  ),
                        html.Div(children=[
                            html.Button('Add node',id='AddNode', n_clicks=0,
                                        style={"border-color":"white","color":"white","background-color": "#4e1175","width":"33.33%"}),
                            html.Button('Edit node',id='EditNode', n_clicks=0,
                                        style={"border-color":"white","color":"white","background-color": "#4e1175","width":"33.33%"}),
                            html.Button("Delete Node", id="DeleteNode", n_clicks=0,
                                        style={"border-color":"white","color":"white","display":"inline-block","background-color":"#900C3F","width":"33.34%"})])
                        ,html.Button("Refresh the topology", id="refresh", n_clicks=0,
                                        style={"border-color":"white","color":"white","background-color":"#4e1175","width":"100%"}),
                            html.Div(children=[],style={"color": "#4e1175"},id='refresh_txt')
                        ]

                    ),
            html.Div(
                style={"background-color":"#fcfafd"},
                className="four columns",
                children=[html.Div(className="twelve columns", children=[
                    dcc.Markdown(d("###### List of posible connections: "),style={"color": "#4e1175"}),
                    dcc.Interval(
                id='interval-component2',
                interval=1 * 1000,  # in milliseconds
                n_intervals=0),

dcc.Checklist(
    options=[],style={"color": "#4e1175"},id="possible_connections")

                ])
                          ]
            ),

            html.Div( className="four columns",
                children=getSubjectInfo(Subject()),style={"color": "#4e1175"},id="details-node")


                ])
        ]),
        dcc.Tab(label='Settings', style={"color": "#4e1175"}, children=
        [
            html.Div(
                        className="four columns",
                        children=[
                            dcc.Markdown(d("###### Type in the email you want to add or delete"),style={"color": "#4e1175"}),
                            dcc.Input(id="email_to_add"
                                  ,type="text",placeholder="example@example.com", style={"color": "#4e1175","width":"100%"}
                                  ),
                            html.Button('Add email',id='AddEmail', n_clicks=0,
                                        style={"border-color":"white","color":"white","background-color": "#4e1175","width":"50%"}),
                            html.Button("Delete email", id="delEmail", n_clicks=0,
                                        style={"border-color":"white","color":"white","display":"inline-block","background-color":"#900C3F","width":"50%"}),

                            dcc.Markdown(d("""
                            ###### Currently stored mails:
                            """), style={"color": "#4e1175"}),
                            html.Div(
                                className='twelve columns',
                                id="emails_list",
                                children=wrap.getMailsDCCWrapped(),
                                style={"maxHeight": "300px", "overflow-y": "scroll", "background-color": "#fcfafd","color": "#4e1175"}
                            )

                        ]
            ),
            html.Div(
                        className="four columns",
                        style={"color": "#4e1175"},
                        children=[
                            dcc.Markdown(d("##### All settings")),
                            dcc.Markdown(d("###### Are you using SDN?")),
                            daq.ToggleSwitch(id="SDN_ON",label=["Regular","SDN"],size=70,color="#4e1175",value=True),
                            dcc.Markdown(d("###### Are you using the alert gradation?")),
                            daq.ToggleSwitch(id="Alert_grada",label=["NO","YES"],size=70,color="#4e1175",value=True)


                        ]
                    )

        ]),
        dcc.Tab(label='Statistics visualisation', style={"color": "#4e1175"}, children=
        [
        html.Div(
                className="four columns",
                style={"color": "#4e1175"},
                        children=[
                            dcc.Markdown(d("##### What do you want to visualize? ")),
                            dcc.Dropdown(
                                id='chart-subject',
                                options=[
                                    {'label': 'Forwarder', 'value': 'fwd'},
                                    {'label': 'Path', 'value': 'path'},
                                    {'label': 'Host', 'value': 'host'},
                                    {'label': 'Link', 'value': 'link'}
                                ],
                                value=1,style={"color":"#4e1175"}
                            ),
                            dcc.Markdown(d("##### Select the subject ")),
                            html.Div(
                                id="subject-dropdown",
                                children = [dcc.Dropdown(id="subject-dropdown-value")]
                            ),
                            dcc.Markdown(d("##### Select what do you want to visualize")),
                            html.Div(
                                id="value-visu-dropdown",
                                children = [dcc.Dropdown(id="value-visu-dropdown-value")]
                            ),
                            html.Div(
                                id="do-visualize",
                                children = [html.Button('VIZUALIZE',id='do-visualize-button', n_clicks=0,style={"border-color":"#4e1175","color":"#4e1175","background-color": "white"},hidden=True)]
                            )
                            ]

        ),
        html.Div(
            className="eight columns",
            id="graph-visu-continous",
            children=[dcc.Graph(id="my-graph-2",figure=getFigureWithOptions()),
                      dcc.Interval(
                          id='interval-component-graph',
                          interval=Connector.updateTime * 1000,  # in milliseconds
                          n_intervals=0
                      )
                      ]

                 )
            ])



    ])])

###################################callback for left side components
################################callback for right side components
@app.callback(dash.dependencies.Output('emails_list','children'),
              [
                  dash.dependencies.Input('AddEmail','n_clicks'),
                  dash.dependencies.Input('delEmail','n_clicks'),
                  dash.dependencies.Input('email_to_add','value'),
                  dash.dependencies.Input('interval-component', 'n_intervals')])
def emailsCallback(add, remove,text,interval):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "AddEmail" in changed_id:
        try:
            dps.addMail(text)
        except:
            tmp = wrap.getMailsDCCWrapped()
            tmp.append(dcc.Markdown(d("** {} is a not a valid email. **".format(text))))
            return tmp
    if "delEmail" in changed_id:
        try:
            dps.delMail(text)
        except:
            tmp = wrap.getMailsDCCWrapped()
            tmp.append(dcc.Markdown(d("** {} is not in the database - it cannot be deleted **".format(text))))
            return tmp
    return wrap.getMailsDCCWrapped()

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
        response = rq.get("{}SRE/autopolicy/data/{}/".format(DataHolder.ip_ctrl.replace("/v1/","/rnn/"),toret),auth=HTTPBasicAuth("karaf","karaf"))

        if response.status_code != 200:
            return dcc.Markdown(d("Nothing selected"),style={"color":"#4e1175"})
    except:
        return dcc.Markdown(d("Nothing selected"), style={"color": "#4e1175"})

    return DataHolder.getInfoFromString(response.text,type)

@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
    [
        dash.dependencies.Input('demo-dropdown', 'value'),
        dash.dependencies.Input('interval-component-log', 'n_intervals'),
        dash.dependencies.Input('srcpath','value'),
        dash.dependencies.Input('dstpath','value'),
        dash.dependencies.Input('SDN_ON','value')

    ])
def update_output123(value,interval,src,dst,sdn):

    if src != dst and src is not None and dst is not None and sdn:
        getPathBetween(src, dst)
    else:
        DataHolder.path = None

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
    return network_graph(YEAR,ACCOUNT,sdn)

@server.route("/alert/", methods=['POST'])
def postAlert():
    jBody = request.json
    try:
        success, reason, id = dps.addAlert(jBody["explanation"], jBody["subject"], int(jBody["severity"]), details=jBody["details"])
        if success:
            toSend = "We are sending this email to let you know that the Autopolicy mechanism detected an Alert - some of your devices are not" \
                     "behaving the way they should. Below you will find the details of the alert. If that's a false alert you can" \
                     "access your autopolicy dashboard and let us know by clicking false alert button for that alert. Here are the details" \
                     " for that alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(jBody["explanation"], jBody["severity"], jBody["subject"],
                                                    jBody["details"], datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            DataHolder.send("Received an alert from the AP", str(toSend))
        else:
            return "NOT OK"

    except:
        dps.addEvent("Provided JSON was not correct: " + jBody,"admin")
        return "NOT OK"
    DataHolder.alerts.append(id)
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
        alert = dps.getAlert(DataHolder.alerts[index])
        alert.ok()
        dps.changeState(alert.id, "Mitigation was correct.",resolved=True)

        dps.addEvent("Accepted the mitigation of the alert: " + str(DataHolder.alerts[index]), str(DataHolder.alerts[index]))

        try:
            toSend = "The alert was stated as a ok alert. The mitigation action taken by that alert will be carried on." \
                     "The OK button was pressed " \
                     "for the alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(alert.explanation, alert.severity, alert.subject,
                                                    alert.details, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            DataHolder.send("Received an alert from the AP", str(toSend))
        except:
            return ""
        DataHolder.alerts.remove(DataHolder.alerts[index])
    #print(str(args))
    return ""
@app.callback(dash.dependencies.Output('allow-once', 'children'),getAlertsAllowbuttonsInput())
def allowonce(*args):
    index = -1
    for i in range(len(args)):
        if args[i]==1:
            index = i
            break
    if index != -1:
        alert = dps.getAlert(DataHolder.alerts[index])
        alert.allow()
        dps.addEvent("Allowed once for the alert: "+str(DataHolder.alerts[index]),str(DataHolder.alerts[index]))
        dps.changeState(alert.id, "Mitigation was correct but allowed once", resolved=True)
        try:
            toSend = "The alert was allowed only once. The mitigation action taken by that alert will be carried on after today." \
                     "The Allow button was pressed " \
                     "for the alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(alert.explanation, alert.severity, alert.subject,
                                                    alert.details, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
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
        alert = dps.getAlert(DataHolder.alerts[index])
        alert.block()
        dps.changeState(DataHolder.alerts[index],"Added to the profile",resolved=True)
        try:
            toSend = "The alert was marked as an invalid alert. The mitigation action taken by that alert will NOT be carried out." \
                     "The Block button was pressed " \
                     "for the alert \n\n Explanation: {} \n\n Severity: {}\n\n Device identification number: {} \n\n Expanded explanation: {}\n\n Time: {}\n\nKind regards," \
                     "\nAutopolicy Provider".format(alert.explanation, alert.severity, alert.subject,
                                                    alert.details, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            DataHolder.send("Received an alert from the AP", str(toSend))
        except:
            return ""

        DataHolder.alerts.remove(DataHolder.alerts[index])
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
        dps.changeState(DataHolder.alerts[index],"Seen")
        data = dps.getAlert(DataHolder.alerts[index]).show()
        DataHolder.currentAlert = data
    return data

@app.callback(dash.dependencies.Output('refresh_txt','children'),[dash.dependencies.Input('refresh','n_clicks')])
def refreshTopo(n):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "refresh" in changed_id:
        dps.delSubjects()
        return dcc.Markdown(d("""**Topology refreshed**"""))
    return ""

@app.callback(dash.dependencies.Output('details-node','children'),
              [
                  dash.dependencies.Input('AddNode','n_clicks'),
                  dash.dependencies.Input('EditNode','n_clicks'),
                  dash.dependencies.Input('DeleteNode','n_clicks'),
                  dash.dependencies.Input('possible_connections','value'),
                  dash.dependencies.Input('type-dropdown','value'),
                  dash.dependencies.Input('node_id','value'),
                  dash.dependencies.Input('node_tag','value')

              ])
def addNode(buttonAdd,buttonEdit, buttonDelete, connections,type,iden,tag):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    OfHexPattern = "of:[0-9a-fA-F]{16}"
    MACAddresPattern ="([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}"
    if "AddNode" in changed_id:
        if iden == None:
            iden = ""
        if re.match(OfHexPattern,iden) or re.match(MACAddresPattern, iden):
            if type != None:
                if tag != None:
                    if connections==None:
                        dps.addSubject(iden, tag, type, [])
                        DataHolder.refreshTopology = True
                        return getSubjectInfo(dps.getSubjectById(iden))
                    if len(connections)!= 0:
                        cons = []
                        for con in connections:
                            link = Connection.Connection()
                            link.src = iden
                            link.dst = con
                            link.capacity = 1
                            cons.append(link)
                        dps.addSubject(iden, tag,type,cons)
                        DataHolder.refreshTopology = True
                        return getSubjectInfo(dps.getSubjectById(iden))
                    else:
                        return dcc.Markdown(d("""
                                            ###### **Node must have at least one connection**
                                            """), style={"color": "#900C3F"})
                else:
                    return dcc.Markdown(d("""
                                        ###### **Provide a tag for the added node**
                                        """), style={"color": "#900C3F"})

            else:
                return dcc.Markdown(d("""
                            ###### **Provide a type for the added node**
                            """), style={"color": "#900C3F"})

        else:
            return dcc.Markdown(d("""
            ###### Provided ID to add was incorrect. 
            
            ###### To add forwarder comply with format
             
            ###### **of:0123456789abcdef**
            
            ###### To add host comply with format
            
            ###### **01:23:45:67:89:ab**
            """),style={"color":"#900C3F"})
    if "DeleteNode" in changed_id:
        if iden == None:
            iden = ""
        if re.match(OfHexPattern,iden) or re.match(MACAddresPattern, iden):
            dps.delSubject(iden)
            return dcc.Markdown(d("""###### **Device with identifier {} was deleted.**
                   """.format(iden)), style={"color": "#900C3F"})
        else:
            return dcc.Markdown(d("""
                   ###### Provided ID to add was incorrect. 

                   ###### To add forwarder comply with format

                   ###### **of:0123456789abcdef**

                   ###### To add host comply with format

                   ###### **01:23:45:67:89:ab**
                   """), style={"color": "#900C3F"})

    return getSubjectInfo(dps.getSubjectById(iden))


@app.callback(dash.dependencies.Output('possible_connections','options'),[dash.dependencies.Input('interval-component2', 'n_intervals')])
def updateOptions(interval):
    return getOptions()

@app.callback(dash.dependencies.Output('do-visualize','children'),
              [
                  dash.dependencies.Input('chart-subject','value'),
                  dash.dependencies.Input("value-visu-dropdown-value",'value'),
                  dash.dependencies.Input("subject-dropdown-value",'value')
                ])
def doVisualizeEnable(subject,what,id):
    if subject!=None and what!=None and id!=None:
        return html.Button('VISUALIZE {} FOR {}'.format(what,id),id='do-visualize-button', n_clicks=0,style={"border-color":"white","color":"white","background-color": "#4e1175"})
    return html.Button('VIZUALIZE',id='do-visualize-button', n_clicks=0,style={"border-color":"#4e1175","color":"#4e1175","background-color": "white"},hidden=True)
@app.callback(dash.dependencies.Output('value-visu-dropdown','children'),[dash.dependencies.Input('chart-subject','value')])
def subSelectedValues(subject):
    if subject == "fwd":
        return dcc.Dropdown(id="value-visu-dropdown-value",options=
        [
            {"label":"Number of packets per second","value":"packets"},
            {"label": "Number of bytes per second", "value": "bytes"},
            {"label": "Number of flows", "value": "flows"},
            {"label": "Average delay to node", "value": "delay"},
            {"label": "Current energy consumption", "value": "energy"}
        ], value="packets")
    if subject == "path":
        return dcc.Dropdown(id="value-visu-dropdown-value",options=
        [
            {"label":"Number of packets per second","value":"packets"},
            {"label": "Number of bytes per second", "value": "bytes"},
            {"label": "Packet loss", "value": "packetloss"},
            {"label": "Average delay", "value": "delay"},
            {"label": "Current energy consumption", "value": "energy"}
        ])
    if subject == "link":
        return dcc.Dropdown(id="value-visu-dropdown-value",options=
        [
            {"label":"Number of packets per second","value":"packets"},
            {"label": "Number of bytes per second", "value": "bytes"},
            {"label": "Packet loss", "value": "packetloss"},
            {"label": "Average delay", "value": "delay"}
        ])
    if subject == "host":
        return dcc.Dropdown(id="value-visu-dropdown-value",options=
        [
            {"label":"Number of packets per second in","value":"inpackets"},
            {"label": "Number of packets per second out", "value": "outpackets"},
            {"label": "Number of bytes per second in", "value": "inbytes"},
            {"label": "Number of bytes per second out", "value": "outbytes"}
        ])
    return dcc.Dropdown(id="value-visu-dropdown-value",options=[])
@app.callback(dash.dependencies.Output('subject-dropdown','children'),[dash.dependencies.Input('chart-subject','value')])
def subjectSelected(subject):
    opt = getOptions(True)
    if subject=="fwd":
        i = 0
        for o in opt.copy():
            if "of:" in o["label"] and o["label"].count("of:")==1 and "-" not in o["label"] and " to " not in o["label"]:
                continue
            else:
                opt.remove(o)
            i+=1
    if subject == "host":
        for o in opt.copy():
            if o["label"].count(":") > 3 and "-" not in o["label"] and " to " not in o["label"]:
                continue
            else:
                opt.remove(o)
    if subject == "link":
        for o in opt.copy():
            if "-" in o["label"]and " to " not in o["label"]:
                continue
            else:
                opt.remove(o)
    if subject == "path":
        for o in opt.copy():
            if " to " in o["label"]:
                continue
            else:
                opt.remove(o)

    return dcc.Dropdown(id="subject-dropdown-value",
                            options=opt,
                            style={"color": "#4e1175"},value=1
                            )

@app.callback(dash.dependencies.Output('my-graph-2','figure'),
              [
                dash.dependencies.Input('do-visualize-button','n_clicks'),
                dash.dependencies.Input('chart-subject','value'),
                dash.dependencies.Input("subject-dropdown-value",'value'),
                dash.dependencies.Input("value-visu-dropdown-value", 'value'),
                  dash.dependencies.Input('interval-component-graph',"n_intervals")
              ])
def createGraph(clicks,type,id,param,inter):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    print(changed_id)
    if changed_id=="do-visualize-button.n_clicks":
        return getFigureWithOptions(type,id,param)

    if changed_id=="interval-component-graph.n_intervals":
        return getFigureWithOptions(type,id,param)
    return DataHolder.tmp_fig


if __name__ == '__main__':
    DataHolder.tmp_fig = getFigureWithOptions()
    DataHolder.ip_ctrl = sys.argv[1]
    dps.Data.mongoip=sys.argv[2]
    DataHolder.out_ip=sys.argv[3]

    print("Set ctrl ip to {} and mongodb connection is on {}:27017".format(DataHolder.ip_ctrl,dps.Data.mongoip))
    dps.global_init()
    DataHolder.restoreState()

    app.run_server(debug=True,host=DataHolder.out_ip,port=1111)