#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
'''
Created on 27.10.2011

@author: rkoraschnigg
'''

import binascii

class Codecs_to_hex(object):

    def to_hex(self, t, nbytes):
        'Format text t as a sequence of nbyte long values separated by spaces.'
        chars_per_item = nbytes * 2
        hex_version = binascii.hexlify(t)
        #num_chunks = len(hex_version) / chars_per_item

        def chunkify():
            for start in xrange(0, len(hex_version), chars_per_item):
                yield hex_version[start:start + chars_per_item]

        return " ".join(chunkify())

