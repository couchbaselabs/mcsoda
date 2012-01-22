#!/usr/bin/env python

import sys
import math
import mcsoda

PRIMES = [
    3, 7, 13, 23, 47, 97, 193, 383, 769, 1531, 3067, 6143, 12289, 24571, 49157,
    98299, 196613, 393209, 786433, 1572869, 3145721, 6291449, 12582917,
    25165813, 50331653, 100663291, 201326611, 402653189, 805306357,
    1610612741
]

DEFAULT_NUM_BINS = 1531 # From ep-engine/stored-value.cc

BIN_DATA = 0
BIN_NEXT = 1

def hash_upsert(key, key_hash, bins, nbins):
    ibin = key_hash % nbins
    if ibin in bins:
        bin = bins[ibin]
        while bin and bin[BIN_DATA] != key:
            bin = bin[BIN_NEXT]
        if not bin:
            bins[ibin] = [key, bins[ibin]]
    else:
        bins[ibin] = [key, None]

def hash_delete(key, key_hash, bins, nbins):
    ibin = key_hash % nbins
    if ibin in bins:
        bin = bins[ibin]
        prev = None
        while bin:
            if bin[BIN_DATA] == key:
                if prev:
                    prev[BIN_NEXT] = bin[BIN_NEXT]
                else:
                    bins[ibin] = bin[BIN_NEXT]
                return
            bin = bin[BIN_NEXT]

def bin_length(bin):
    n = 0
    while bin:
        n += 1
        bin = bin[BIN_NEXT]
    return n


class StoreSimMicroLRU(mcsoda.Store):

    def connect(self, target, user, pswd, cfg, cur):
        self.cfg = cfg
        self.cur = cur
        self.target = target
        self.xfer_sent = 0
        self.xfer_recv = 0

        self.nbins = DEFAULT_NUM_BINS
        self.bins = {}

    def command(self, c):
        cmd, key_num, key_str, data, expiration = c
        key_hash = hash(key_str)
        if cmd == 'set':
            hash_upsert(key_str, key_hash, self.bins, self.nbins)
        elif cmd == 'delete':
            hash_delete(key_str, key_hash, self.bins, self.nbins)


if __name__ == "__main__":
    # usage: mcsoda_sim_micro_lru sim-micro-lru

    argv = (' '.join(sys.argv) +
            ' doc-gen=0 doc-cache=0 exit-after-creates=1').split(' ')

    store = StoreSimMicroLRU()

    mcsoda.main(argv,
                protocol="sim-micro-lru",
                stores=[store])

    tot = 0
    max_bin_length = 0
    for bin in store.bins.values():
        n = bin_length(bin)
        if max_bin_length < n:
            max_bin_length = n
        tot += n
        print bin
        # print(n)

    print(max_bin_length)
    print(tot)

    print('done')
