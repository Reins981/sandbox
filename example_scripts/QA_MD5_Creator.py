#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
'''
Created on 24.10.2011

@author: rkoraschnigg
'''

import hashlib
import sys

class QA_MD5_Create(object):

    def __init__(self, datastream='', filename='', block_size=128, sample_Data=True, attackdir='/root/ips/'):
        self.datastream = datastream
        self.filename = filename
        self.block_size = block_size
        self.sample_Data = sample_Data
        self.attackdir = attackdir
        
        
    
    def md5_for_file(self, datastream='', filename='', block_size=128, sample_Data=True):
        
        if self.sample_Data:
            self.filename = filename
            
        else:
            self.filename = self.attackdir + filename
            
        self.block_size = block_size
        self.datastream = datastream
        self.sample_Data = sample_Data
        md5 = hashlib.md5()
        
        if len(self.datastream) == 0:
            
            try:
                f = open(self.filename, "rb")
                
            except IOError:
                print "file not found in %s" % (self.filename)
                sys.exit(1)
                
            while True:
                data = f.read(block_size)
                
                if not data:
                    f.close()
                    break
                md5.update(data)
                
            f.close() 
            return md5.hexdigest()
        
        elif len(self.filename) == 0:
            
            md5.update(self.datastream)
            return md5.hexdigest() 
            
