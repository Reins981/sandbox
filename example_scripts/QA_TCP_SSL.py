'''
Created on Feb 7, 2012

@author: mortner
based on http://code.activestate.com/recipes/483732/

add hooks on receiver [receive,send],sender [receive,send]
'''

import inspect
import socket,asyncore, ssl, zlib, time
from modules.QA_Logger import QA_Logger
#logline_format= "[%(asctime)s] %(levelname)s - %(message)s "
LOG = QA_Logger(loglevel=QA_Logger.L_INFO,name="ncssl2",)

KEYWORDS= { 'dossl\n':None,                 #init ssl             client init
            '+ ok to switch now\n': None,   #init ssl reply       srv reply
            '+ compress switch now\n':None, #compress stuff :)    srv reply
           }

'''
    hook a command and perform funny things
    (argument will be data, you can manipulate it before it gets logged)
'''
CMD_HOOKS = {
             'dossl\n':    {
                             'server':None,
                             'client':None,
                             },
             '+ ok to switch now\n':    {
                             'server':None,
                             'client':None,
                             },
             '+ compress switch now\n':    {
                             'server':None,
                             'client':None,
                             } ,        
         
            }
'''
DATA_HOOKS = {
       TCP_SSL_sender:   {
                           'handle_data_sent':someFunc,
                           'handle_response' :someFunc,
                           },
       TCP_SSL_receiver: {
                           'handle_data_sent':someFunc,
                           'handle_response':someFunc,
                          }              
       }
'''
# hook data originating from TCP_SSL_sender or TCP_SSL_receiver 
# that comes from calling function handle_data_sent or handle_response
# and perform specific functions on it


class TCP_SSL_node(asyncore.dispatcher):
    ssl_sock=None   #ssl connection
    
    DATA_HOOKS = None           #reserved for data hooks

    
    def __init__(self,logger):
        #asyncore.dispatcher.__init__(self)
        if logger==None:
            print "default logger"
            #logline_format= "[%(asctime)s] %(levelname)s - %(message)s "
            logger = QA_Logger(loglevel=QA_Logger.L_ERROR,)
        self.logger=logger
        logger.debug("init async tcp_ssl node (super)")
        pass
    
    def _send(self,data):
        '''
            send data\n to socket
        '''
        if self.ssl_sock!=None:
            numbytes = self.ssl_sock.write(data)
        elif self.socket!=None:
            #fallback send sock
            numbytes = self.send(data)
        else:
            self.logger.error( "[*]  no sock available")
            return
        
        return numbytes
    
    def _sendRcv(self,command):
        self._send(command)
        return (command,self.read())

    def wrapClientSocketSSL(self,
                            keyfile=None,
                            certfile=None,
                            ca_certs=None,
                            cert_reqs=ssl.CERT_NONE,
                            ciphers="ALL"
                            ):
        if self.socket==None:
            self.logger.error( "[*]  error - no socket")
            return
        if self.ssl_sock!=None:
            self.logger.error( "[*]  socket allready wrapped!")
            return
        
        self.ssl_sock = ssl.wrap_socket(self.socket,
                       #ca_certs="/etc/ca_certs_file",
                       ca_certs=ca_certs,
                       keyfile=keyfile,
                       certfile=certfile,
                       #cert_reqs=ssl.CERT_REQUIRED
                       cert_reqs=cert_reqs,
                       do_handshake_on_connect=True,
                       #ssl_version=ssl.PROTOCOL_TLSv1,
                       ciphers=ciphers,
                       )   
        
        self.logger.debug("\t [client] using SSL Cipher: %s"%repr(self.ssl_sock.cipher()))
        return 
        
    def wrapServerSocketSSL(self,
                            keyfile=None,
                            certfile=None,
                            ca_certs=None,
                            cert_reqs=ssl.CERT_NONE,
                            ciphers="ALL"
                            ):
        if self.socket==None:
            self.logger.error( "[*]  error - no socket")
            return
        if self.ssl_sock!=None:
            self.logger.error( "[*]  socket allready wrapped!")
            return

        self.ssl_sock = ssl.wrap_socket(self.socket,
                                        server_side=True,
                                        do_handshake_on_connect=True,
                       keyfile=keyfile,
                       certfile=certfile,
                       ca_certs=ca_certs,
                       #cert_reqs=ssl.CERT_REQUIRED
                       cert_reqs=cert_reqs,
                       #ssl_version=ssl.PROTOCOL_TLSv1,
                       ciphers=ciphers,
                       )   
       
        self.logger.debug("\t [server] using SSL Cipher: %s"%repr(self.ssl_sock.cipher()))       
        return 
    
    def _log(self,message):
        #get caller method to derive direction
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        caller= calframe[1][3]
        # name "handle_data_sent"        ... outgoing
        # bane "handle_data_received"    ... incoming
        #
        # only print 
        #                TCP_SSL_sender.handle_data_sent
        #                TCP_SSL_receiver.handle_response

        
        if (isinstance(self,TCP_SSL_receiver) and caller=="handle_data_sent") or (isinstance(self,TCP_SSL_sender) and caller=="handle_data_sent"):
            if (isinstance(self,TCP_SSL_sender)): 
                txtsrv="#> "
            else:
                txtsrv=""
            #self.logger.log(self.logger.L_INFO+2,tuple([self,caller,(message)]))
            if message[-1]=='\n': 
                message=message.rstrip("\n")+"\\n"
            else:
                self.logger.FAIL("[!!] PROTOCOL ERROR! - Response terminator missing (\\n): - %s"%message)
            self.logger.log(self.logger.L_INFO+2,txtsrv+message)
        
    def decompress(self,data):
        return zlib.decompress(data)
        

class TCP_SSL_receiver(TCP_SSL_node):
    def __init__(self,conn,keyfile,certfile,timeout=5,logger=None,):
        asyncore.dispatcher.__init__(self,conn)
        TCP_SSL_node.__init__(self, logger)
        self.from_remote_buffer=''
        self.to_remote_buffer=''
        self.sender=None
        self.socket.settimeout(timeout)
        self.keyfile=keyfile
        self.certfile=certfile
        return

    def handle_connect(self):
        pass


    def handle_response(self,data):
        #log data
        self._log(data)
        
        if data=="+ ok to switch now\n":
            #log it
            self.logger.debug(" prepare for ssl handshake ")
        return
    
    def handle_data_sent(self,data):    
        #print "%s <-- [server]"%data.replace("\n","")
        self._log(data)
            
        if data=="+ ok to switch now\n":
            #self._log( "[server] init serverside wrapping of sslsock")

            self.wrapServerSocketSSL(certfile=self.certfile,
                                     keyfile=self.keyfile)   
        return

    def handle_read(self):
        if self.ssl_sock!=None:
            # use ssl socket :)
            resp = self.ssl_sock.read()            
        elif self.socket!=None:
            # use 
            resp = self.recv(4096)
        else:
            self.logger.error("[*]  no sock available")
        
        self.handle_response(resp)
        # print '%04i -->'%len(read)
        self.from_remote_buffer += resp
        return 


    def writable(self):
        return (len(self.to_remote_buffer) > 0)

    def handle_write(self):
        sent = self._send(self.to_remote_buffer)
        self.handle_data_sent(self.to_remote_buffer)
        # print '%04i <--'%sent
        self.to_remote_buffer = self.to_remote_buffer[sent:]
        


    def handle_close(self):
        self.logger.debug("closing connection")
        self.close()
        if self.sender:
            self.sender.close()
        
class TCP_SSL_sender(TCP_SSL_node):
    '''
        sends data to server
        
        client <---> [receiver]
                        |    
                        \-------[sender]<-----> server
    
    '''
    ssl_sock=None
    
    def __init__(self, receiver, remoteaddr,remoteport,timeout=5,logger=None):
        asyncore.dispatcher.__init__(self)
        TCP_SSL_node.__init__(self, logger)
        self.receiver=receiver
        receiver.sender=self
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((remoteaddr, remoteport))
        self.socket.settimeout(timeout)
        return

    def handle_connect(self):
        self.logger.debug(" ")
        pass
    
    def handle_response(self,data):   
        self._log(data)   
        
        if data=="+ ok to switch now\n":
            self.logger.debug( "\t[client] wrapping client socket")
            self.wrapClientSocketSSL()
            self.logger.debug("\t[client] socket wrapped!")
        return
    

    def handle_data_sent(self,data):  
        self._log(data)      
        
        if data=="dossl\n":
            #self._log("[client] prepare for ssl handshake (initial) ;)")
            pass
        return
                     

    def handle_read(self):
        if self.ssl_sock!=None:
            # use ssl socket :)
            resp = self.ssl_sock.read()            
        elif self.socket!=None:
            # use 
            resp = self.recv(4096)
        else:
            self.logger.error("[*]  no sock available")
        
        self.handle_response(resp)
        # print '%04i -->'%len(read)
        self.receiver.to_remote_buffer += resp
        return


    def writable(self):
        return (len(self.receiver.from_remote_buffer) > 0)

    def handle_write(self):
        sent = self._send(self.receiver.from_remote_buffer)
        
        self.handle_data_sent(self.receiver.from_remote_buffer)
        # print '--> %04i'%sent
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]
        return
        
    def handle_close(self):
        self.close()
        self.receiver.close()    
        return

class TCP_SSL_client(object):
    # class stuff
    sock = None
    ssl_sock = None
    
    HOST=None
    PORT=None
    
    SSL_KEYWORD="dossl\n"
    capture=None        #capture to file
    
    def __init__(self, host=None,port=None,socktimeout=1,capture=None):
        print "[*] start"
        
        if isinstance(capture,str): self.capture = open(capture,'w')
        if host!=None and port !=None:
            print "[*] client-mode ahead"
            self.HOST=host
            self.PORT=port
            self.connect(socktimeout=socktimeout)
        # leave it
        pass

    
    def __del__(self):
        if self.ssl_sock!=None:
            self.ssl_sock.close()
            print "[*] disconnected (SSL)"
        elif self.sock!=None:
            print "[*] disconnected"
            self.sock.close()
        else:
            print "[*] nice del :)"
            
        if self.capture!=None: 
            print "[*] capture file closed :)"
            self.capture.close()
            
        return

    def connect(self,host=HOST,port=PORT,socktimeout=1):
        '''
                returns output as a list
        '''    
        if host!=None: self.HOST = host
        if port!=None: self.PORT = port
        
        print "[*] connecting to %s:%s"%(self.HOST,self.PORT)
          
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect ((self.HOST,self.PORT))
        self.sock.settimeout(socktimeout)
        return self.sock
    
    def initSSL(self,keyword=SSL_KEYWORD):
        if self.sock==None:
            print "[*]  error - no socket"
            return
        if self.ssl_sock!=None:
            print "[*]  socket allready wrapped!"
            return
        
        if keyword!=None:
            self.SSL_KEYWORD=keyword
            
        return self.sendRcv(self.SSL_KEYWORD)
        
    def doSSL(self,keyword=None):
        if self.sock==None:
            print "[*]  error - no socket"
            return
        if self.ssl_sock!=None:
            print "[*]  socket allready wrapped!"
            return
        
        resp = self.initSSL(keyword)
        if resp[1][0] != "+ ok to switch now\n":
            print resp
            print "[*]  something went wrong!"
            return
        
        self.ssl_sock = ssl.wrap_socket(self.sock,
                       #ca_certs="/etc/ca_certs_file",
                       #cert_reqs=ssl.CERT_REQUIRED
                       cert_reqs=ssl.CERT_NONE,
                       do_handshake_on_connect=True,
                       #ssl_version=ssl.PROTOCOL_TLSv1,
                       ciphers="ALL",
                       )   
        output = []
        output.append(('dossl',resp))
        output.append(("<changeCipherSpec>",tuple([self.ssl_sock.read(),self.ssl_sock.cipher()])))
        
        return output
            
    
      
    def read(self,socktimeout=1):
        data=""
        resp=data
        try:
            if self.ssl_sock!=None:
                # use ssl socket :)

                resp = self.ssl_sock.read()
                #if resp == "+ data follows\n" or False:
                if len(resp)>0 and resp[0]=="+":
                    #multiline response
                    LOG.debug( resp)
                    data_part="<initial value :)>"
                    while not ".\n" in data_part[-2:] and data_part!="":
                        self.ssl_sock.settimeout(socktimeout*2)
                        data_part=self.ssl_sock.read(2)
                        #print "[p]<%s>"%data_part
                        data+=data_part
            
            elif self.sock!=None:
                # use 
                resp = self.sock.recv(1024)
            else:
                print "[*]  no sock available"
                return

        except socket.error:
            # catch timeouts.. maybe there is no data
            LOG.warn("command timed out - resp[%s]{%s}"%(repr(resp),repr(data)))
            pass
 
        return (resp,data)
    
    def send(self,data):
        '''
            send data\n to socket
        '''
        if self.ssl_sock!=None:
            self.ssl_sock.write("%s\n"%data)
        elif self.sock!=None:
            #fallback send sock
            self.sock.send("%s\n"%data)
        else:
            print "[*]  no sock available"
            return
        
        return
    
    def sendRcv(self,command):
        self.send(command)
        retn =(command,self.read())
        if not self.capture==None:
            self.log_capture("#>%s"%retn[0])  #client command (prefixed #>)
            self.log_capture("|%s"%str(retn[1]))  #server response (prefixed |)
        return retn
    
    def interactive(self,mode=None):
        data = ""
        tlast=time.time()
        while not data=="exit":
            tdelta=time.time()-tlast
            data=raw_input("+%0.3fs #>"%(tdelta))
            # do not allow \n OR " "* (spaces) as commands
            tlast=time.time()
            if not data=="\n" and not data.count(" ")==len(data):
                if mode=='text':
                    resp="".join(self.sendRcv(data)[1])
                    if len(resp)>0 and resp[-1]=='\n': 
                        resp=resp.rstrip("\n")+"\\n"
                    else:
                        LOG.warn("[!!] PROTOCOL ERROR! - Response terminator missing (\\n): - %s"%resp)
                    print resp
                else:
                    print self.sendRcv(data)
                    
    def replay(self,filepath,mode=None,timeout=None):
        data=""

        with open(filepath,'r') as f:
            cmds=f.readlines()
        
        tlast=time.time()
        for c in cmds:
            if '|' in c[:1]: continue       # | marks server responses in file :)
            if c=="\n" or c.count(" ")==len(c): continue #empty command
            if 'dossl' in c: continue       # dont perform dossl
            c= c.lstrip("#>")                  # #> client marker.. strip it
            if data=="exit": break          #stop processing
            c = c.rstrip("\n")                #normalize linenedings
            
            tdelta=time.time()-tlast
            if timeout==None or float(timeout)<0: 
                data=raw_input("+%0.3fs | REPLAY#> %s"%(tdelta,c))
            else:
                time.sleep(float(timeout))
                print "+%0.3fs | REPLAY #> %s"%(tdelta,c)
            c="%s\n"%c                         #fix missing \n
            tlast=time.time()
            if mode=='text':
                print "".join(self.sendRcv(c)[1]).rstrip("\n")
            else:
                print self.sendRcv(c)     
            
                    
        LOG.info("--End-of-Replay--")
        
    def log_capture(self,message):
        self.capture.write("\n%s"%message)
 



class TCP_SSL_proxy(TCP_SSL_node):
    '''
        client <-> [      forwarder     ]  <---> realTCPSrv
                   [ reveiver ][ sender ]
                   
                   
                   conn accept -> receiver (local) -> sender (remote)
    '''
    
 
    
    def __init__(self, ip, port, remoteip,remoteport,keyfile="./modules/data/box-key.pem",certfile="./modules/data/box-cert.pem",backlog=5,timeout=5, logger=None):
        asyncore.dispatcher.__init__(self)
        TCP_SSL_node.__init__(self, logger)
        self.remoteip=remoteip
        self.remoteport=remoteport
        self.ip=ip
        self.port=port
        self.backlog=backlog
        self.timeout=timeout
        self.keyfile=keyfile
        self.certfile=certfile
        if logger==None:
            #logline_format= "[%(asctime)s] %(levelname)s - %(message)s "
            logger = QA_Logger(loglevel=QA_Logger.L_ERROR,)
        self.logger=logger
        self.logger.debug("forwarding %s:%d -> %s:%d (socket_backlog=%d, socket_timeout=%d)"%(ip,port,remoteip,remoteport,backlog,timeout))
        self.connect()
        return
        
        
    def connect(self):
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((self.ip,self.port))
        self.listen(self.backlog)
        self.settimeout(self.timeout)
        self.logger.debug("[%s:%d] listening ..."%(self.ip,self.port))
        self.loop()
        return

    def handle_accept(self):
        conn, addr = self.accept()
        self.logger.debug("[%s:%d] new connection %s ..."%(self.ip,self.port,addr))
        TCP_SSL_sender(
                       TCP_SSL_receiver(conn,
                                        logger=self.logger,
                                        keyfile=self.keyfile,
                                        certfile=self.certfile,),
                       self.remoteip,
                       self.remoteport,
                       logger=self.logger
                       )
        return

    def loop(self):
        asyncore.loop()

if __name__=='__main__':
    log = QA_Logger(loglevel=5,name="ngadmin",logline_format= "[%(asctime)s] %(levelname)s - %(message)s ")
    #log.enable_LogFile("a.txt")
    log.debug("--- app start ----")
    log.debug("* client terminal app tests ahead")
    s = TCP_SSL_client("10.0.66.252",801)
    for out in s.doSSL(): print out        #alternate way, also print handshake details and ctrlmessages
    #s.doSSL()
    #print s.initSSL()
    #s.doSSL()
    #exit()
    print s.sendRcv("login root a")
    print s.sendRcv("showdhcpstatus")
    print s.sendRcv("showlicstate")
    print s.sendRcv("loadipsprevversion")
    #exit()
    # magic off
    del s
    log.debug("* proxy features ahead")
    TCP_SSL_proxy('127.0.0.1',801,"10.0.66.251",801,logger=log)
    TCP_SSL_proxy('127.0.0.1',809,"10.0.66.251",809,logger=log)
    log.debug("----- waiting for connections -----")
    asyncore.loop()