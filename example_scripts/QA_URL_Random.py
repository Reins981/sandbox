'''
Created on 07.09.2011

@author: mortner
'''
import httplib,time

class QA_URL_Random(object):
    
    proxyIP=""
    proxyPort=0
    conn=None
    response=None
    timeout = 0.2
    
    def __init__(self,proxyIP,proxyPort,timeout=0.2):
        self.proxyIP=proxyIP
        self.proxyPort=proxyPort
        self.timeout=timeout
        self.connect()
        
    def __del__(self):
        if self.is_connected(): del self.conn
    
    def connect(self):
        if self.conn==None:
            self.conn = httplib.HTTPConnection(self.proxyIP, self.proxyPort)
            
    def reconnect(self):
        self.conn=None
        self.connect()
        
    def is_connected(self):
        if self.conn==None: 
            return False
        else:
            return True
        
    def generateURLs(self,number):
        reslt = []
        for i in range(1, number):
            reslt.append(self.generate())
            time.sleep(self.timeout)
            
        return reslt
        
    def generate(self):
        retnstr = None
        self.reconnect()
        if self.is_connected():
            self.conn.request("GET", "http://random.yahoo.com/bin/ryl")
            #try:
            self.response = self.conn.getresponse()
            #except: pass
            if self.response.status==302:            #redirect
                message=str(self.response.msg)
                start=message.find("Location: ")+10
                end=message.find("\r",start)
                retnstr=message[start:end]
        
        return retnstr