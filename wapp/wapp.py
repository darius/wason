# Copyright 2004, 2007 Darius Bacon, under the terms of the MIT X license.

from BaseHTTPServer import HTTPServer
import sys

import webserver


def main(resource, address=None):
    try:
        try:
            start(resource, address)
        except KeyboardInterrupt:
            print '^C received, shutting down server'
            sys.stdout.flush()
            server.socket.close()
    finally:
        resource.shut_down()

server = None

def start(resource, address=None):
    if address is None:
        address = ('', 7002,)
    global server
    print 'Starting HTTPServer at %s...' % (address,)
    server = HTTPServer(address, make_HTTPRequestHandler(resource))
    print 'Started.'
    sys.stdout.flush()
    serve()

def serve():
    server.serve_forever()


Resource = webserver.MetaDispatcher

make_HTTPRequestHandler = webserver.make_dispatching_handler_class
