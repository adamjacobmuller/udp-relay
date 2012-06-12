import socket
listener=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listener.bind(('0.0.0.0',udp_relay_listen_port))
listener.setblocking(False)
