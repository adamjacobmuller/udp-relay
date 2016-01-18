import ffprobe
import ffmpeg
import iptools
import socket
import time
import urllib2
import json
import os

from hdhomerun import *
from pprint import pprint
import elementtree.ElementTree as ET


def get_vstatus_packed(libhdhr, device):
    vstatus = libhdhr.device_get_tuner_vstatus(device)
    return vstatus_pack(vstatus)


def vstatus_dict(vstatus):
    vstatus_dict = {}
    vstatus_dict['vchannel'] = int(vstatus[2].vchannel)
    vstatus_dict['name'] = vstatus[2].name
    vstatus_dict['auth'] = vstatus[2].auth
    vstatus_dict['cci'] = vstatus[2].cci
    vstatus_dict['cgms'] = vstatus[2].cgms

    if vstatus[2].not_subscribed == 1:
        vstatus_dict['subscribed'] = False
    else:
        vstatus_dict['subscribed'] = True

    if vstatus[2].not_available == 1:
        vstatus_dict['available'] = False
    else:
        vstatus_dict['available'] = True

    if vstatus[2].copy_protected == 1:
        vstatus_dict['copy_protected'] = True
    else:
        vstatus_dict['copy_protected'] = False

    return vstatus_dict


def vstatus_pack(vstatus):
    if vstatus[2].not_subscribed == 1:
        subscribed = 'f'
    else:
        subscribed = 't'

    if vstatus[2].not_available == 1:
        available = 'f'
    else:
        available = 't'

    if vstatus[2].copy_protected == 1:
        copy_protected = 't'
    else:
        copy_protected = 'f'
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

hdhr_ip = '10.0.8.215'
hdhr_tuner = 1
udp_relay_listen_port = 1236


libhdhr = LibHdhr()

device = libhdhr.device_create(HDHOMERUN_DEVICE_ID_WILDCARD, iptools.ip2long(hdhr_ip), hdhr_tuner)

listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listener.bind(('0.0.0.0', udp_relay_listen_port))
#listener.setblocking(False)
#listener_fh=listener.fileno()


localip = libhdhr.device_get_local_machine_addr(device)
target = 'udp://%s:%d/' % (iptools.long2ip(localip), udp_relay_listen_port)
libhdhr.device_set_tuner_target(device, target)

dir_timestamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")
os.mkdir('/www/hdhr.adam.gs/scanner/%s' % dir_timestamp)

req = urllib2.Request(
    url='http://hdhr.adam.gs/lineup.xml'
)
fh = urllib2.urlopen(req)
data = fh.read()
xdata = ET.fromstring(data)
programs = xdata.findall("Program")


want_channels = sys.argv[1:]

for program in programs:
    channel = program.find("GuideNumber").text
    name = program.find("GuideName").text
    if len(want_channels) > 0:
        if channel not in want_channels:
            #print("skipping %s - %s" % (channel,name))
            continue
    print("scanning %s - %s" % (channel, name))
    current_target = libhdhr.device_get_tuner_target(device)
    if current_target != target:
        libhdhr.device_set_tuner_target(device, target)
    vchannel_result = libhdhr.device_set_tuner_vchannel(device, str(channel))
    vstatus = libhdhr.device_get_tuner_vstatus(device)
    ffprobe_prober = ffprobe.ffprobe()
    ffmpeg_screenshotter = ffmpeg.ffmpeg()
    ffmpeg_screenshotter.output = [
        '/www/hdhr.adam.gs/scanner/%s/%s-%s.png' % (
            dir_timestamp,
            vstatus[2].vchannel.replace("/", "_"),
            vstatus[2].name
        )
    ]
    ffmpeg_screenshotter.debug = False
    ffmpeg_screenshotter.start()
    need_data = True
    last = time.time()
    started = time.time()
    meta = {}
    while need_data is True:
        try:
            data = listener.recvfrom(2048)
        except:
            continue

        need_data = False
        if ffmpeg_screenshotter is not None:
            if ffmpeg_screenshotter.need_data():
                ffmpeg_screenshotter.append_data(data[0])
                need_data = True
            else:
                print "screenshot done to %s" % (ffmpeg_screenshotter.output[0])
                ffmpeg_screenshotter = None
        if ffprobe_prober is not None:
            if ffprobe_prober.need_data():
                ffprobe_prober.append_data(data[0])
                need_data = True
            else:
                print(ffprobe_prober.pprint())
                meta['streams'] = ffprobe_prober.streams
                meta['format'] = ffprobe_prober.format
                pprint(vstatus[2].name)
                json_file = '/www/hdhr.adam.gs/scanner/%s/%s-%s.json' % (
                    dir_timestamp,
                    vstatus[2].vchannel.replace("/", "_"),
                    vstatus[2].name
                )
                json_fh = open(json_file, "w")
                try:
                    json.dump(meta, json_fh, indent=4, ensure_ascii=False)
                    print "json done to %s" % json_file
                except:
                    print("JSON dump failed? %s" % sys.exc_info)
                finally:
                    json_fh.close()
                ffprobe_prober = None
        interval = time.time() - last
        if interval > 1:
            last = time.time()
            vstatus = libhdhr.device_get_tuner_vstatus(device)
            print vstatus_pack(vstatus)
            meta['vstatus'] = vstatus_dict(vstatus)
            waiting = time.time() - started
            if waiting > 30:
                print("waiting %d seconds for channel %s - aborting!" % (waiting, channel))
                break
            elif waiting > 10:
                print("waiting %d seconds for channel %s" % (waiting, channel))
