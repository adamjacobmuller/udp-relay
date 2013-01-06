import socket
import time
import math
import select
import os
import sys
import iptools
import re
import ffprobe
import ffmpeg
import BaseHTTPServer

from hdhomerun import *
from pprint import pprint

def save_receivers(receivers):
    return True

def get_vstatus_packed(libhdhr,device):
    vstatus=libhdhr.device_get_tuner_vstatus(device)
    return vstatus_pack(vstatus)

def vstatus_pack(vstatus):
    if vstatus[2].not_subscribed==1:
        subscribed='f'
    else:
        subscribed='t'

    if vstatus[2].not_available==1:
        available='f'
    else:
        available='t'

    if vstatus[2].copy_protected==1:
        copy_protected='t'
    else:
        copy_protected='f'
    return 'vchannel=%s:name=%s:auth=%s:cci=%s:cgms=%s:subscribed=%s:avaliable=%s:copy_protected=%s' % (
        vstatus[2].vchannel,
        vstatus[2].name,
        vstatus[2].auth,
        vstatus[2].cci,
        vstatus[2].cgms,
        subscribed,
        available,
        copy_protected
        )

def pprint_bytes(bytes):
    bytes=float(bytes)
    units=['','k','M','G','T','P','E','Z','Y'];
    index=1
    for unit in units:
        if bytes<math.pow(1000,index):
            return '%.2f %s' % ((bytes/math.pow(1000,index-1)),unit)
        index=index+1
    return False


udp_relay_listen_port=1234
udp_control_listen_port=1235
hdhr_ip='10.0.8.215'
hdhr_tuner=0

libhdhr = LibHdhr()

device=libhdhr.device_create(HDHOMERUN_DEVICE_ID_WILDCARD,iptools.ip2long(hdhr_ip),hdhr_tuner)

localip=libhdhr.device_get_local_machine_addr(device)
target='udp://%s:%d/' % ( iptools.long2ip(localip) , udp_relay_listen_port )
libhdhr.device_set_tuner_target(device,target)

control=socket.socket(socket.AF_INET6,socket.SOCK_DGRAM)
control.bind(('::0',udp_control_listen_port))
control.setblocking(False)
control_fh=control.fileno()

listener=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listener.bind(('0.0.0.0',udp_relay_listen_port))
listener.setblocking(False)
listener_fh=listener.fileno()

transmitter=socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

receivers=[]
packets=0
data_length=0
total_packets=0
total_data_length=0
start=time.time()
last=time.time()
interval_counter=0
vstatus=None
current_target=None

prober=None

screenshot_default_count=1
screenshotter=None

segdir="/www/hdhr.adam.gs/hls/"
segindex=0
segfile="/www/hdhr.adam.gs/hls/%016d.ts" % segindex
segfh=open(segfile,"w")
segwrote=0
segsize=1024*1024*15
segments=[]


while 1:
    did_something=False
    try:
        data=listener.recvfrom(2048)
        data_length+=len(data[0])*8
        packets+=1
        total_packets+=1
        total_data_length+=len(data[0]*8)
    
        for reciever in receivers:
            transmitter.sendto(data[0],reciever)

        if prober is not None:
            if prober.need_data():
                prober.append_data(data[0])
            else:
                print prober.pprint()
                prober=None

        if screenshotter is not None:
            if screenshotter.need_data():
                screenshotter.append_data(data[0])
            else:
                screenshotter.finish()
                print "screenshot done I think"
                screenshotter=None

        if segdir is not None:
            segfh.write(data[0])
            segwrote+=len(data[0])

            if segwrote > segsize:
                segfh.close()
                segindex+=1
                segfile="/www/hdhr.adam.gs/hls/%016d.ts" % segindex
                segfh=open(segfile,"w")
                segwrote=0
                segments.append(segfile)
        
        did_something=True
    except socket.error:
        pass

    interval=time.time()-last
    if interval>1:
        interval_counter+=1
        if interval_counter%10 == 0 or vstatus is None or current_target is None:
            current_target=libhdhr.device_get_tuner_target(device)
            if current_target!=target:
                libhdhr.device_set_tuner_target(device,target)
            vstatus=libhdhr.device_get_tuner_vstatus(device)
        bps=data_length/interval
        pps=packets/interval
        sys.stdout.write("\r%s - receiving %30sbps at %30spps sending to %4d receivers [ channel = %s - %s ]" % (
            time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            pprint_bytes(bps),
            pprint_bytes(pps),
            len(receivers),
            vstatus[2].vchannel,
            vstatus[2].name
            ))
        sys.stdout.flush()
        data_length=0
        packets=0
        last=time.time()
    try:
        data=control.recvfrom(2048)
        if data:
            did_something=True
            dsplit=data[0].rstrip().split(" ")
            command=dsplit[0]
            args=dsplit[1:]
            if command=="ADD_RECEIVER":
                ip=args[0]
                port=int(args[1])
                if re.match("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",ip):
                    ip="::ffff:%s" % ip
                receivers.append((ip,port))
                print "\n%s - %s:%d : added receiver %s:%d" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    ip,port
                    )
                save_receivers(receivers)
                control.sendto("RECEIVER_ADDED",data[1])
            elif command=="REMOVE_RECEIVER":
                new_receivers=[]
                print "\n%s - %s:%d : remove receiver %s:%d started (%d receivers)" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    args[0],int(args[1]),
                    len(receivers)
                    )
                removed=0
                for reciever in receivers:
                    if reciever[0]==args[0] and reciever[1]==int(args[1]):
                        print "%s - %s:%d : found receiver matching %s:%d, removing" % (
                            time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                            data[1][0],
                            data[1][1],
                            args[0],int(args[1])
                            )
                        removed+=1
                        continue
                    new_receivers.append(reciever)
                receivers=new_receivers
                save_receivers(receivers)
                print "%s - %s:%d : remove receiver %s:%d completed (%d receivers)" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    args[0],
                    int(args[1]),
                    len(receivers)
                    )
                control.sendto("RECEIVERS_REMOVED %d"%removed,data[1])
            elif command=="LIST_RECEIVERS":
                print "\n%s - %s:%d : currently broadcasting to %d receivers" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    len(receivers)
                    )
                control.sendto("RECEIVER_LIST_BEGINS\n",data[1])
                for receiver in receivers:
                    control.sendto("RECEIVER %s %s\n"%(receiver[0],receiver[1]),data[1])
                    print "%s - %s:%d : %s:%d" % (
                        time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        data[1][0],
                        data[1][1],
                        receiver[0],
                        receiver[1]
                        )
                control.sendto("RECEIVER_LIST_ENDS\n",data[1])
            elif command=="FLUSH_RECEIVERS":
                print "\n%s - %s:%d : flushing %d receivers" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    len(receivers)
                    )
                receivers=[]
                save_receivers(receivers)
            elif command=="SCREENSHOT":
                screenshotter=ffmpeg.ffmpeg()
                screenshotter.output=[
                    '/www/hdhr.adam.gs/screenshot/%s-%s-%s.png' %
                        (
                            time.strftime("%Y-%m-%d_%H:%M:%S_%Z"),
                            vstatus[2].vchannel,
                            vstatus[2].name
                        )
                ]
                screenshotter.start()
                print "\n%s - %s:%d : making screenshot" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    )
            elif command=="PROBE":
                prober=ffprobe.ffprobe()
                print "\n%s - %s:%d : probing" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    )
            elif command=="SET_CHANNEL":
                prober=ffprobe.ffprobe()
                print "\n%s - %s:%d : setting vchannel to %d" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    int(args[0])
                    )
                vchannel_result=libhdhr.device_set_tuner_vchannel(device,args[0])
                if vchannel_result==0:
                    control.sendto("SET_CHANNEL_RESULT FAILED",data[1])
                    print "\n%s - %s:%d : setting vchannel to %d failed" % (
                        time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        data[1][0],
                        data[1][1],
                        int(args[0])
                        )
                else:
                    vstatus_packed=get_vstatus_packed(libhdhr,device)
                    control.sendto("SET_CHANNEL_RESULT SUCCESS %s" % vstatus_packed,data[1])
                    print "\n%s - %s:%d : setting vchannel to %d success %s" % (
                        time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                        data[1][0],
                        data[1][1],
                        int(args[0]),
                        vstatus_packed
                        )
                    
            elif command=="QUIT":
                print "\n%s - %s:%d : quit" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1]
                    )
                sys.exit(128)
            elif command=="RESTART":
                print "\n%s - %s:%d : restart " % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1]
                    )
                sys.exit(0)
            else:
                print "\n%s - %s:%d : received unknown command %s" % (
                    time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    data[1][0],
                    data[1][1],
                    command
                    )
    except socket.error:
        pass

    if did_something == False:
        r=[listener_fh,control_fh]
        w=[]
        e=[]
        select.select(r,w,e,1)
