# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at https://mozilla.org/MPL/2.0/.

import asyncore
import getopt
import socket
import sys

class ProxyClient(asyncore.dispatcher):
    def __init__(self, address, port, serverHandler):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((address, port))
        self.serverHandler = serverHandler
        self.buffer = ''

    def handle_connect(self):
        pass

    def handle_close(self):
        self.close()

    def handle_read(self):
        read_data = self.recv(8192)
        self.serverHandler.sendToClient( read_data )

    def writable(self):
        try:
            return (len(self.buffer) > 0)
        except:
            return false

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def sendToServer(self, data):
        self.buffer= self.buffer + data;

    def handle_close(self):
        self.serverHandler.close()

class ProxyHandler(asyncore.dispatcher_with_send):
    initialized = False
    client = None
    inputBuffer = ''

    def handle_read(self):
        toServer = self.recv(8192)
        headers = {}
        if toServer:
            if not self.initialized:
                self.inputBuffer = self.inputBuffer + toServer
                items = self.inputBuffer.split("\r\n\r\n")
                remaining = ''
                if len(items) > 1:
                    headers, others = items[0], items[1:]
                    remaining = "\r\n\r\n".join(others)
                else:
                    return
                headerLines = headers.split('\r\n', 1)
                req = headerLines[0]
                verb, endpoint, version = req.split(' ')
                address, portString = endpoint.split(':')
                port = int(portString)
                print "connection requested to %s:%i" % (address, port)
                if address.endswith(".example.com"):
                    address = "localhost"
                    port = 8443
                print "establishing connection to %s:%i" % (address, port)
                self.client = ProxyClient(address, port, self)
                self.send("HTTP/1.1 200 Connection established\r\n\r\n");
                self.initialized = True
                self.client.sendToServer(remaining)
            else:
                self.client.sendToServer(toServer)

    def handle_close(self):
        if self.initialized:
            self.client.close()

    def sendToClient(self, toClient):
        self.send(toClient)

class ProxyServer(asyncore.dispatcher):
    def __init__(self, address, port):
        print("starting server on %s port %i" % (address, port))
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((address, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            handler = ProxyHandler(sock)

def main(argv):
    address = '0.0.0.0'
    port = 8088

    try:
        opts, args = getopt.getopt(argv, "a:p:", ["address=", "port="])
        for opt, arg in opts:
            if opt in ("-a", "--address"):
                address = arg
            if opt in ("-p", "--port"):
                port = int(arg)
    except:
        print('There was a problem with the options')
    server = ProxyServer(address, port)
    asyncore.loop()

if __name__ == '__main__':
    main(sys.argv[1:])
