import socket
import time
import sys

UDP_IP = "255.255.255.255"
UDP_PORT = 8080
MESSAGE = str.encode("helo")

print("UDP target IP:" + str(UDP_IP))
print("UDP target port:" + str(UDP_PORT))
print ("message:" + str(MESSAGE))

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(('192.168.86.20', 8080)) # need to change aa
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
