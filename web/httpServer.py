#!/usr/bin/env python
import CGIHTTPServer

def main():

    server_address = ('192.168.2.110', 8080)
    #server_address = ('raspberrypi', 8080)
    handler = CGIHTTPServer.CGIHTTPRequestHandler
    handler.cgi_directories = ['/cgi-bin']
    server = CGIHTTPServer.BaseHTTPServer.HTTPServer(server_address, handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

if __name__ == '__main__':
    main()
    
