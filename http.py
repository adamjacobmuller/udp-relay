import BaseHTTPServer
import time
import iptools
import socket
import re
import requests
import sys
import json
import cgi

import elementtree.ElementTree as ET
from elementtree.ElementTree import Element, SubElement, dump, iselement
from hdhr_helpers import get_vstatus_packed
from SocketServer import ThreadingMixIn
from hdhomerun import *


hdhrs = [
    #{'ip':'10.0.8.215','tuner':0},
    {'ip':'10.0.8.215','tuner':1},
    {'ip':'10.0.8.215','tuner':2},
    ]

local_port_base = 12340

local_port = local_port_base
for hdhr in hdhrs:
    hdhr['local_port'] = local_port
    hdhr['busy'] = False
    hdhr['ip_long'] = iptools.ip2long(hdhr['ip'])
    local_port += 1


class ThreadingHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer): 
    pass

class HDHRHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.getheader('content-length'))
        xml = self.rfile.read(length)
        try:
            self.xml = ET.fromstring(xml)
            self.log_message("xml: %s" % self.xml)
        except:
            self.log_message("unable to parse XML")

        routes = [
                {
                'pattern'   : '/MediaServerControlReply.xml',
                'function'  : self.media_server_control_reply
                },
                {
                'pattern'   : '/control-reply.php',
                'function'  : self.media_server_control_reply
                }
        ]
        for route in routes:
            re_r=re.search(route['pattern'],self.path)
            if re_r:
                args = re_r.groupdict()
                try:
                    route['function'](**args)
                except:
                    print sys.exc_info()
                return
        self.send_response(404,'Not Found')
        self.log_message("unable to find matching route for %s" % self.path)
    def media_server_control_reply(self):
        self.send_response(200,'OK')
        self.end_headers()

        #x = ET.Element("DIDL-Lite")

        #return x.tostring()

    def do_GET(self):
        routes = [
                {
                'pattern'   : '/w/channel/(?P<channel>\d+)',
                'function'  : self.send_channel
                },
                {
                'pattern'   : '/MediaServerServiceDesc.xml',
                'function'  : self.send_media_server_service_desc
                },
                {
                'pattern'   : '/MediaServerContentDirectory.xml',
                'function'  : self.send_media_server_content_directory
                },

                {
                'pattern'   : '/w/channels',
                'function'  : self.send_lineup
                }
        ]
        
        for route in routes:
            re_r=re.search(route['pattern'],self.path)
            if re_r:
                args = re_r.groupdict()
                try:
                    route['function'](**args)
                except:
                    print sys.exc_info()
                return
        self.send_response(404,'Not Found')
        self.log_message("unable to find matching route for %s" % self.path)

    def send_lineup(self):
        global hdhrs
        lineup = requests.get("http://%s/lineup.xml" % hdhrs[0]['ip'])
        self.send_response(200,'OK')
        self.send_header("Content-type","application/json")
        self.end_headers()

        root = ET.fromstring(lineup.text)
        #self.wfile.write(lineup.text)
        channels=[]
        for program in root.findall("./Program"):
            channels.append({
                'name'      : program.find("GuideName").text,
                'number'    : program.find("GuideNumber").text
                })

        self.wfile.write(json.dumps(channels))

    def send_media_server_content_directory(self):
        data = open('data/MediaServerContentDirectory.xml')
        self.send_response(200,'OK')
        self.send_header("Content-type","application/xml")
        self.end_headers()
        while True:
            block = data.read(1024)
            if block == "":
                break
            self.wfile.write(block)
        
    def send_media_server_service_desc(self):
        data = open('data/MediaServerServiceDesc.xml','r')
        self.send_response(200,'OK')
        self.send_header("Content-type","application/xml")
        self.end_headers()
        while True:
            block = data.read(1024)
            if block == "":
                break
            self.wfile.write(block)
        
    def send_channel(self,channel):
        global hdhrs
        for hdhr in hdhrs:
            if hdhr['busy'] == False:
                hdhr['busy'] = True
                break
            hdhr = None
        if hdhr is None:
            self.send_response(503,'No HDHR avaliable')
            return
        
        print "%s:%s" % (hdhr['ip'],hdhr['tuner'])
        try:
            libhdhr = LibHdhr()
            device=libhdhr.device_create(HDHOMERUN_DEVICE_ID_WILDCARD,hdhr['ip_long'],hdhr['tuner'])

            localip=libhdhr.device_get_local_machine_addr(device)
            target='udp://%s:%d/' % ( iptools.long2ip(localip) , hdhr['local_port'])
            libhdhr.device_set_tuner_target(device,target)

            listener=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            listener.bind(('0.0.0.0',hdhr['local_port']))
            listener_fh=listener.fileno()

            self.log_message("tuning to channel %s" % channel)
            vchannel_result=libhdhr.device_set_tuner_vchannel(device,channel)
            if vchannel_result == 0:
                self.send_response(404, 'Channel not found or unable to tune')
                self.send_header("X-Tuner","%s:%s" % (hdhr['ip'],hdhr['tuner']))
                self.end_headers()
                return
            self.send_response(200,'OK')
            vstatus = get_vstatus_packed(libhdhr,device)
            self.log_message(vstatus)
            self.send_header("X-V-Status",vstatus)
            self.send_header("X-Tuner","%s:%s" % (hdhr['ip'],hdhr['tuner']))
            self.send_header("X-Local-Port",hdhr['local_port'])
            self.send_header("Content-type","video/mp2t")
            self.end_headers()
            while True:
                data = listener.recvfrom(2048)
                self.wfile.write(data[0])
        finally:
            hdhr['busy'] = False

server_address = ('', 8001)

#server = ThreadingHTTPServer(server_address,HDHRHTTPHandler)
server = BaseHTTPServer.HTTPServer(server_address,HDHRHTTPHandler)
server.daemon_mode = True


while True:
    server.handle_request()
