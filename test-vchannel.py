from hdhomerun import *
import iptools
import sys
import time

def pp_vstatus(libhdhr,device):
    vstatus=libhdhr.device_get_tuner_vstatus(device)

    if vstatus[2].not_subscribed==1:
        subscribed=False
    else:
        subscribed=True

    if vstatus[2].not_available==1:
        available=False
    else:
        available=True

    if vstatus[2].copy_protected==1:
        copy_protected=True
    else:
        copy_protected=False

    print("vstatus:")
    print("        vchannel         %s" % (vstatus[2].vchannel))
    print("        name             %s" % (vstatus[2].name))
    print("        auth             %s" % (vstatus[2].auth))
    print("        cci              %s" % (vstatus[2].cci))
    print("        cgms             %s" % (vstatus[2].cgms))
    print("        subscribed       %s" % (subscribed))
    print("        available        %s" % (available))
    print("        copy_protected   %s" % (copy_protected))

libhdhr = LibHdhr()

device=libhdhr.device_create(HDHOMERUN_DEVICE_ID_WILDCARD,iptools.ip2long('10.0.8.211'),0)

print iptools.long2ip(libhdhr.device_get_local_machine_addr(device))

pp_vstatus(libhdhr,device)
libhdhr.device_set_tuner_vchannel(device,'802')
time.sleep(1)
pp_vstatus(libhdhr,device)

libhdhr.device_set_tuner_vchannel(device,'1216')
time.sleep(1)
pp_vstatus(libhdhr,device)

