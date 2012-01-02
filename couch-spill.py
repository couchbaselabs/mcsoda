#!/usr/bin/env python

import re
import sys
import copy
import math
import time
import socket
import threading
import mcsoda

class Reader(threading.Thread):
    def __init__(self, src, reader_go, reader_done):
        self.src = src
        self.reader_go = reader_go
        self.reader_done = reader_done
        self.inflight = 0
        self.received = 0
        threading.Thread.__init__(self)

    def run(self):
        self.reader_go.wait()
        self.reader_go.clear()
        while True:
            data = self.src.recv(4096)
            if not data:
                break

            self.received += len(data)

            found = len(re.findall("HTTP/1.1 ", data))

            self.inflight -= found
            if self.inflight == 0:
                self.reader_done.set()
                self.reader_go.wait()
                self.reader_go.clear()


# Stream some mcsoda onto a couch for performance testing.
#
class StoreCouch(mcsoda.Store):

    def connect(self, target, user, pswd, cfg, cur):
        self.cfg = cfg
        self.cur = cur
        self.target = target
        self.host_port = (target + ":5984").split(':')[0:2]
        self.host_port[1] = int(self.host_port[1])
        self.queue = []
        self.ops = 0
        self.seq = 0
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.skt.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.skt.connect(tuple(self.host_port))
        self.reader_go = threading.Event()
        self.reader_done = threading.Event()
        self.reader = Reader(self.skt, self.reader_go, self.reader_done)
        self.reader.daemon = True
        self.reader.start()
        self.xfer_sent = 0
        self.xfer_recv = 0

    def show_some_keys(self):
        pass

    def gen_doc(self, key_num, key_str, min_value_size, json=True, cache=None):
        # Always json and never cache.
        #
        # seqno : 4 bytes
        # cas :  8 bytes
        # length : 4 bytes
        # flags : 4 bytes
        #
        self.seq = self.seq + 1
        seqno = self.seq
        if self.cfg.get('ratio-sets', 0) >= 1.0 and \
           self.cfg.get('ratio-creates', 0) >= 1.0:
            # If we're only creating docs, then seqno should be 1.
            seqno = 1

        # suffix_ex = '"_rev":"1-0286dbb6323b61e7f0be3ba5d1633985",'
        suffix_ex = '"_rev":"%s-00000000000000000000000000000000",' % (seqno,)

        d = mcsoda.gen_doc_string(key_num, key_str, min_value_size,
                                  self.cfg['suffix'][min_value_size],
                                  True, cache=None, key_name="_id",
                                  suffix_ex=suffix_ex,
                                  whitespace=False)

        strip = len('"_id":"00003e3b9e533668",') + len(suffix_ex)
        dlen = len(d) - strip
        dlen = hex(dlen)[2:].rjust(8, '0')
        suff = '-0000000000000000%s00000000' % (dlen,)
        d = d.replace("-00000000000000000000000000000000", suff)

        return (d, str(seqno) + suff) # Returns (doc, rev-id).

    def command(self, c):
        self.queue.append(c)
        if len(self.queue) > (self.cur.get('batch') or \
                              self.cfg.get('batch', 100)):
            self.flush()
            return True
        return False

    def flush(self):
        revs_diff_arr = [ "POST /default/_revs_diff HTTP/1.1\r\n" \
                          "Content-Type: application/json\r\n" \
                          "Accept: application/json\r\n" \
                          "Host: %s:%s\r\n" % (self.host_port[0], self.host_port[1]),
                          "Content-Length: ", None, "\r\n\r\n",
                          '{' ]
        revs_diff_len = len(revs_diff_arr[-1]) # Content length.

        bulk_docs_arr = [ "POST /default/_bulk_docs HTTP/1.1\r\n" \
                          "X-Couch-Full-Commit: false\r\n" \
                          "Content-Type: application/json\r\n" \
                          "Accept: application/json\r\n" \
                          "Host: %s:%s\r\n" % (self.host_port[0], self.host_port[1]),
                          "Content-Length: ", None, "\r\n\r\n",
                          '{"new_edits":false,"docs":[' ]
        bulk_docs_len = len(bulk_docs_arr[-1]) # Content length.

        docs_num = 0 # Number of actual docs to be sent.

        for c in self.queue:
            cmd, key_num, key_str, doc_rev, expiration = c
            if doc_rev:
                doc, rev = doc_rev

                if docs_num > 0:
                    revs_diff_arr.append(',')
                    revs_diff_len += 1

                    bulk_docs_arr.append(',')
                    bulk_docs_len += 1

                x = '"%s":["%s"]' % (key_str, rev)
                revs_diff_arr.append(x)
                revs_diff_len += len(x)

                bulk_docs_arr.append(doc)
                bulk_docs_len += len(doc)

                docs_num += 1

        revs_diff_arr.append("}")
        revs_diff_len += 1

        bulk_docs_arr.append("]}")
        bulk_docs_len += 2

        if docs_num > 0:
            revs_diff_arr[2] = str(revs_diff_len) # Fill content length placeholders.
            bulk_docs_arr[2] = str(bulk_docs_len)

            if True:
                # Use separate sends()'s for revs_diff and bulk_docs.
                to_send = [(''.join(revs_diff_arr), 1), (''.join(bulk_docs_arr), 1)]
            else:
                # Send revs_diffs + bulk_docs in one send().
                to_send = [(''.join(revs_diff_arr) + ''.join(bulk_docs_arr), 2)]

            for m, num_posts in to_send:
                self.reader.inflight += num_posts
                self.skt.send(m)
                self.xfer_sent += len(m)

                r = self.reader.received
                self.reader_go.set()
                self.reader_done.wait()
                self.reader_done.clear()
                self.xfer_recv += self.reader.received - r

        self.ops += len(self.queue)
        self.queue = []


if __name__ == "__main__":
    if sys.argv[1].find("http") != 0:
        raise Exception("usage: %s http://HOST:5984 ..." % (sys.argv[0],))

    argv = (' '.join(sys.argv) + ' doc-gen=0').split(' ')

    mcsoda.main(argv, protocol="http", stores=[StoreCouch()])
