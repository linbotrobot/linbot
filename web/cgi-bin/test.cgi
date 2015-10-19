#!/usr/bin/python

import cgi
import cgitb; cgitb.enable() # Optional; for debugging only
import socket
import time

print "Content-Type: text/html"
print ""

arguments = cgi.FieldStorage()

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('localhost', 8000))
clientsocket.send(arguments["cmd"].value + "\n")
time.sleep(0.2) # wait for whole answer
data = clientsocket.recv(1024)
clientsocket.close()
print data.strip()
