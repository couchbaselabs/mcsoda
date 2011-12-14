#!/usr/bin/env python

import re
import os
import sys
import time
import socket
import threading

# Simple proxy, useful for recording HTTP REST protocol conversations.
#
# Usage: ./proxy.py [HOST[:PORT]]
# Ex:    ./proxy.py www.google.com:80

PORT = 9091
DEST = ("www.google.com", 80)

class Pump(threading.Thread):
    def __init__(self, tag, src, dst, sub=[], end=False):
        self.tag = tag
        self.logj = "\n" + tag + ": "
        self.src = src
        self.dst = dst
        self.sub = sub
        self.end = end
        threading.Thread.__init__(self)

    def log(self, msg):
        print self.tag, self.logj.join(msg.split("\n"))

    def run(self):
        f = open("out/" + self.tag + ".out", 'w')

        try:
            while True:
                data = self.src.recv(1024 * 1024)
                if not data:
                    break
                for patt, repl in self.sub:
                    data = re.sub(patt, repl, data)
                self.log(data)
                f.write(data)
                self.dst.send(data)
        except:
            pass

        for s, shut in [(self.src, socket.SHUT_RD), (self.dst, socket.SHUT_WR)]:
            try:
                s.shutdown(shut)
                if self.end:
                    s.close()
            except:
                pass

        f.close()

def run(port, dest):
    sub = [("Host: (127\\.0\\.0\\.1|localhost):%s" % (port,),
            "Host: %s:%s" % (dest[0], dest[1]))]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost', port))
    sock.listen(10)

    print "running on port: %s to destination: %s" % (port, dest)

    i = 0
    while True:
        client, client_address = sock.accept()
        client.settimeout(0.5)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect(dest)

        c2s = Pump("req-%s" %(i,), client, server, sub=sub)
        c2s.daemon = True
        c2s.start()

        s2c = Pump("res-%s" %(i,), server, client, end=True)
        s2c.daemon = True
        s2c.start()

        i = i + 1

if __name__ == "__main__":
    dest = DEST
    if len(sys.argv) > 1:
        dest = sys.argv[1] + ':80'
        dest = (dest.split(':')[0], int(dest.split(':')[1]))
    run(PORT, dest)
