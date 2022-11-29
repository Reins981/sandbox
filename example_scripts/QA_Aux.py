#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:expandtab
'''
Created on 13.09.2011

    """
    A simple script for making random passwords, WITHOUT 1,l,O,0.  Because
    those characters are hard to tell the difference between in some fonts.
    
    """
''' 
from random import Random
import time
import zlib
import struct

class QA_StrGen(object):

    dictAlphaLow =  'abcdefghijklmnopqrstuvwxyz'
    dictAlphaCap =  'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    dictNum =       '1234567890'
    dictSpecial =   '!"§$%&/[()]=?`´}\\+*~#\'-_.:,;µ<>|€@^°'
    dictAll = dictAlphaLow+dictAlphaCap+dictNum+dictSpecial
    lstFuzz = ['%%s','%%p','%%n','....','::::::::','::1','256.256.256.256','-1.65535.1.0','65536','\\']  

 
    def gen_charset_ascii(self, c_min = 0, c_max = 255):

        cset = ""

        for i in range(c_min, c_max):

            cset += chr(i)

        return cset


    def gen_charset_unicode(self, c_min = 0, c_max = 255):


        cset = ""

        for i in range (c_min, c_max):

            cset += str(i)

        return unicode(cset)


    def gen_charset_encodings(self, c_min = 0, c_max = 255, str_encoding="utf_8"):

        cset = ""

        for i in range (c_min, c_max):

            cset += str(i)

        cset_u = cset.decode()
        cset_enc = cset_u.encode(str_encoding)
        return cset_enc

    
    def generate_bulk(self,pwdlen=8,howmany=1, charset=dictAll):
        result_pwd = ""
        result_arr = []
          
        for i in range(howmany):
            result_arr.append(self.generate(pwdlen, charset))
        
        return result_arr
    

    def generate(self,pwdlen=8, charset=dictAll):
        result_pwd = ""
        rng = Random()
        
        if isinstance(charset,str):  
            for j in range(pwdlen):
                result_pwd+=rng.choice(charset)
        elif isinstance(charset,list):
            #listenmagic .. one charset per item
            #
            # charset[0]="aklsdfjlasödfaskldf"   
            # charset[1]=['aa','bbbbb','audoooo']
            #
            # mix: random char von str charset (0) .. mixed mit charset listitem wenn liste
            #
            for j in range(pwdlen):
                curr_charset = rng.choice(charset)      #random charset list item
                result_pwd+=rng.choice(curr_charset)    #random item of charset
        else:
            raise Exception
    
        return result_pwd


    def __lstFuzzer__(self,fuzz_charset=lstFuzz):

        return fuzz_charset


    def selftest(self):
        self.generate(4, 8, self.allchars)
        
        
def pause(message="\n\nhit enter to continue (ctrl+z to abort)"):
    inp = raw_input(message)
    return inp

def wait(seconds,message=None):
    if message!=None: print "%s\n\ncontinuing in %d seconds (ctrl+z to abort)"%(message,seconds)
    time.sleep(seconds)
    

import re
class QA_Highlighter():
    
    
    def highlight(self, data,pattern,highlight=None):
        '''
        data = data to modify
        pattern = regex pattern (no compiled pattern, just plain ascii pattern)
        higlight = None (no highlighting), or a string "<starttag>;<endttag>" or a dictionary {'start':"<starttag>,'end':"</endtag<"}
        '''
        result = ""
        if highlight=="": highlight=None
        
        for i in range(0, len(data)):      
            if isinstance(highlight,str): 
                tmp=highlight.split(";")
                highlight={'start':tmp[0],'end':tmp[1]} #create dict if its not a dict
            
            lastmatch_end=0
            
        if isinstance(highlight,dict):
            for match in re.finditer(r"%s"%(pattern),data,flags=re.IGNORECASE):
                start,end = match.span()
                result+= data[lastmatch_end:start] + highlight['start'] + data[start:end] + highlight['end']
                lastmatch_end=end
            result+=data[lastmatch_end:] 
            
        return result
    
    
class Password():
    algorithm = 'sha1'
    salt=None
    
    
    def __init__(self):
        pass
    
    def __str__(self):
        pass
    
    def __repr__(self):
        pass
    
    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)

def zreceive(s):
    total = 0
    data = []
    while total < 4:
        dat = s.recv(4-total)
        if not dat:
            return #FIXME: return error
        data.append(dat)
        total += len(dat)

    length = struct.unpack("!I", "".join(data))[0]

    total = 0
    data = []
    while total < length:
        dat = s.recv(length-total)
        if not dat:
            return #FIXME: return error
        data.append(dat)
        total += len(dat)

    ret = zlib.decompress("".join(data))
    return ret

def zsend(s, data):
    d = zlib.compress(data)
    sz = len(d)
    length = struct.pack("!I", sz)
    s.sendall(length)
    s.sendall(d)
