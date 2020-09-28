# Autopolicy dashboard for network
## Introduction
This solution provides the user-friendly web GUI to manage the network and autopolicy alerts.
It provides an easy and comprehensive method for maintaining the network (even without any knowledge).
It utilizes both AP4SDN mechanism as well as a standalone AP mechanism available
[https://github.com/iitis/autopolicy].

## Running the docker image

You can use (and it's recommended) an docker image for [pfrohlich/ap:latest] to run this 
server. There is only one commandline argument - and this is an URL address of the AP-Server from 
the aforementioned AP Standalone mechanism and SDN-Controller URL for the AP4SDN mechanism. 

> docker run -e "ctrl_url= CONTROLLER IP :8181/onos/v1/" -p 1111:1111 pfrohlich/ap:latest

## Requirements

To successfully run the image there must be a mongodb instance running on the hosting machine. 