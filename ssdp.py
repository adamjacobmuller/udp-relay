import socket
import time
import struct
import uuid

class SSDP():
    def __init__(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("239.255.255.250",1900))
        mreq = struct.pack("4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
        self.listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    def send(self,host,port):
        message=[]
        message.append("NOTIFY * HTTP/1.1")
        message.append("HOST: %s:%s"% (host,port))
        #message.append("LOCATION: http://10.0.8.7/w/umsp/MediaServerServiceDesc.xml")
        message.append("LOCATION: http://10.0.8.2:8001/MediaServerServiceDesc.xml")
        message.append("SERVER: MYFAKESERVER UDP 127")
        message.append("CACHE-CONTROL: max-age=7200")
        message.append("NT: urn:schemas-upnp-org:device:MediaServer:1")
        message.append("NTS: ssdp:alive")
        message.append("USN: uuid:7ec3e01b-241b-4759-b904-3fe3affba64e::urn:schemas-upnp-org:device:MediaServer:1")
        message.append("Content-Length: 0")
        message.append("")

        msgsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.SOL_UDP)
        #msgsock.bind(("64.111.196.233",1900))
        msgsock.sendto("\r\n".join(message), (host,port))

        print "\n".join(message)
    def listen(self):
        data = self.listener.recvfrom(4096)
        print data[1]
        print data[0]
        self.send(data[1][0],data[1][1])
        print "=========================================================="

if __name__ == "__main__":
    ssdpserver = SSDP()
    while True:
        #ssdpserver.send()
        ssdpserver.listen()
        time.sleep(.01)
