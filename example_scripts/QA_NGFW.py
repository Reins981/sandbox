#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
'''
Created on 28.10.2011

@author: mortner
'''
from QA_Testrun import QA_Testrun
from QA_Logger import QA_Logger
from QA_Aux import QA_Highlighter
from QA_Conf_Tools import Bnf_Db
import os, re
from datetime import datetime, timedelta
import subprocess
import platform,shutil
import time, socket
LOG = QA_Logger(name='NGFW', 
                loglevel=QA_Logger.L_INFO,
                logline_format= "[%(asctime)s] %(levelname)s - %(message)s ",
                print_stats_on_exit=False,
                )
try:
    from QA_SSH import QA_SSH
except:
    LOG.warn(" !!! no paramiko support !!! - local connections only")

from QA_MethodDeco import method_decorator,GenericError

'''
------------ Decorator for ngfonly checks ------------------
'''


class BNNGF_ONLY(method_decorator):
    def __call__(self, *args, **kwargs):
        if not self.obj.is_BNNGF():
            raise GenericError("Call <xx> is BNNGF_ONLY!")
            return
        return method_decorator.__call__( self, *args, **kwargs ) 
class BNF_ONLY(method_decorator):
    def __call__(self, *args, **kwargs):
        if not self.obj.is_BFW():
            raise GenericError("Call <xx> is BNF_ONLY!")
            return
        return method_decorator.__call__( self, *args, **kwargs )
class LINUX_ONLY(method_decorator):
    def __call__(self, *args, **kwargs):
        if not self.obj.is_LINUX():
            raise GenericError("Call <xx> is LINUX_ONLY!")
            return
        return method_decorator.__call__( self, *args, **kwargs )  
class WINDOWS_ONLY(method_decorator):
    def __call__(self, *args, **kwargs):
        if not self.obj.is_WINDOWS():
            raise GenericError("Call <xx> is WINDOWS_ONLY!")
            return
        return method_decorator.__call__( self, *args, **kwargs )         


class QA_NGFW(object):
    ssh_conn=None           #connection object
    BoxConn = ('LOCAL')     #define
    NGFW_version=None
    BFW_version=None
    scp=None                # scp channel

    #scp options for raw scp only
    default_raw_SCP_options=[ 'StrictHostKeyChecking=no','CheckHostIP=no','UserKnownHostsFile=/dev/null']
    #------------------------------------
    PATH = {
            'packages':'/var/phion/packages',
            'tgz':'/var/phion/packages/tgz',
            'release':'/etc/phion-release',
            'repo_base':'/root/repo',        #BASEPATH="/root/repo/<version>/>type>
            'conf_root':'/opt/phion/config/configroot',
            'conf_active':'/opt/phion/config/active',
            'conf_activate':'/etc/phion/bin/activate',
            'sys_logs':'/var/phion/logs',
            'kdump':'/var/phion/crash',
            'ips':'/var/phion/mcdownload/ips',
            }
    
    REGEX = {
             'ls-lsa':'(\d+) ([lrwsxdt-]+) +(\d+) (\w+) (\w+) +(\d+) ([\d-]+) ([\d:])+ ([\w_\-.]+)',
             'logline':'^(\d{4} \d{2} \d{2}) (\d{2}:\d{2}:\d{2}) (\w+).*(\+\d{4}) (.*)$',
             'logline_grep':'^(.*):(\d{4} \d{2} \d{2})\s(\d{2}:\d{2}:\d{2})\s+(\w+)\s*(?:([\+-]\d{2}:\d{2}))?\w*(.*)$',
             'logline_test':'(.*):(.*)',
             }
    
    CREDENTIALS = [ 
                           ('root','a'),
                           ('root','ngf1r3wall'),
                           ('root','AngryZeedonk'),
                   ]

    MARKER = {
              'WHITELIST':'WHITELISTED',
              'BLACKLIST':'',
              'DEFAULT':None,
             }
    
 
    
    ERROR_STRINGS=['error','warning','broken']          #add strings that point to errors here
    
    #------------------------------------
 
    def __init__(self, BoxConn=('LOCAL')):
        self.BoxConn=BoxConn
        return        
   
   
    def __del__(self):
        if self.ssh_conn: self.ssh_conn.close()
        if LOG: LOG.debug("---destroyed & disconnected---")
        return
        
    #-------------------------------------
    def __connect(self):
        if self.ssh_conn==None and self.is_REMOTE(): #no conn
            LOG.debug('initiating connection')
            try:
                self.ssh_conn=QA_SSH()
                self.ssh_conn.set_ignore_missing_host_key_warning()              
                self.ssh_conn.connect(hostname=self.BoxConn[1],port=self.BoxConn[2], username=self.BoxConn[3], password=self.BoxConn[4])
                self.is_BNF()   #checks bnngf and bnf
            except:
                self.ssh_conn=None
                raise
        elif not self.is_REMOTE():
            LOG.warn("BoxConn not set to REMOTE! - %s"%(str(self.BoxConn[0])))
        elif self.ssh_conn!=None:
            pass        # ssh connection exists
        else:            
            LOG.error("unhandled connection error")
            
        return self.ssh_conn

    def __exec_command(self,COMMAND,asString=False,write_stdin=None,bufsize=-1):
        output =None
        if str(self.BoxConn[0]).upper()=='REMOTE' :
            if asString:
                output = self.__connect().exec_command_stdoutEX(COMMAND,write_stdin=write_stdin,bufsize=bufsize)
            else:
                output = self.__connect().exec_command_stdout(COMMAND,write_stdin=write_stdin,bufsize=bufsize)
        else:
            if self.is_WINDOWS():
                #output=subprocess.call(COMMAND,shell=True)
                p=platform.popen(COMMAND)
                output=p.readlines()
                if asString: "".join(output)
            else:
                p=os.popen(COMMAND)
                output = p.readlines()
                if asString: "".join(output)     
        return output

    def __setBoxConn(self,type,ip,port,user,passwd,params=None):
        if params==None:
            params=()
        self.BoxConn=(type.upper(),ip,port,user,passwd)+params
        LOG.info("Connection changed to %s"%repr(self.BoxConn))
        return
    
    def connect_local(self):
        self.BoxConn=("LOCAL")
        return
    
    def open(self,ip=None,port=22,user=None,passwd=None,retrycnt=None,retrydelay=None,guess_credentials=False,scp=False):
        return self.connect_remote(ip=ip, port=port, user=user, passwd=passwd, retrycnt=retrycnt, retrydelay=retrydelay,guess_credentials=guess_credentials,scp=scp)
    
    def connect_remote(self,ip=None,port=22,user=None,passwd=None,retrycnt=None,retrydelay=None,guess_credentials=False,scp=False):
        port=port or 22
        retrydelay=retrydelay or 10
        
        #check if boxconn was set previously and use it to reopen connection
        params=None
        if not ip and self.BoxConn[0]=="REMOTE":
            # use stored settings if ip is not set! ( reconnect feature )
            ip = ip or self.BoxConn[1]
            port = port or self.BoxConn[2]
            user= user or self.BoxConn[3]
            passwd = passwd or self.BoxConn[4]
            try:
                retrycnt=retrycnt or self.BoxConn[5]
                retrydelay=retrydelay or self.BoxConn[6]
                guess_credentials=guess_credentials or self.BoxConn[7]
                scp=scp or self.BoxConn[8]
            except:
                pass        #seems like not every option was supplied by user (__init__.. by user)
            params=(retrycnt,retrydelay,guess_credentials,scp)      #we'll attach the params to set_boxconn
            
            # finally check ip for None!
            if not ip: raise Exception("connect_remote() - unable to reconnect! Reason: connection settings missing")
        else:
            # use supplied values and check if ip is a parsable ip string beforehand
            o = self.match_connection_uri(type=["ssh://","scp://"], data=ip)
            user = o['user'] or user
            passwd = o['password'] or passwd
            ip = o['host'] or ip
            port = o['port'] or port        
        
        if user and passwd:         #add supplied user to pos 0 of credentials list (will try all of them if guess_credentials=true)
            self.CREDENTIALS.insert(0, (user,passwd))
        elif (user and not passwd) or (not user and passwd):
            LOG.warn("mixed missing user name or password not implemented.. file a ticket! :p")
        else:
            LOG.warning("Missing username or passward... FALLBACK to guess credentials")
            guess_credentials=True
        
        if guess_credentials: LOG.debug("+ credentials guessing = on")
        if retrycnt and isinstance(retrycnt,int): LOG.info("+ autoretry = on, try %s delay %s"%(retrycnt,retrydelay))
        
        if retrycnt==None or retrycnt<=0:
            if guess_credentials:
                for c in self.CREDENTIALS:
                    try:
                        self.__setBoxConn("REMOTE",ip,port,c[0],c[1],params)
                        self.__connect()        #do a normal connect and throw exception on failure
                        if scp: self.open_scp()
                        return self
                    except:
                        LOG.debug("obviously wrong credentials (%s,%s) :( ..."%(c[0],c[1]))
                        pass
                    
            else:
                c=self.CREDENTIALS[0]       #get first item (only try this one.. 
                self.__setBoxConn("REMOTE",ip,port,c[0],c[1],params)
                self.__connect()
                if scp: self.open_scp()
        else:
            for c in range(retrycnt):
                if guess_credentials:
                    for c in self.CREDENTIALS:
                        try:
                            self.__setBoxConn("REMOTE",ip,port,c[0],c[1],params)
                            self.__connect()
                            if scp: self.open_scp()
                            return self
                        except:
                            #simply catch all as I dont want to import socket for socket.error
                            LOG.debug("try %d of %d, waiting %0.2fsec"%(c+1,retrycnt,retrydelay))
                            self.sleep(retrydelay)
                else:
                    try:
                        c=self.CREDENTIALS[0]       #get first item (only try this one.. 
                        self.__setBoxConn("REMOTE",ip,port,c[0],c[1],params)
                        self.__connect()
                        if scp: self.open_scp()
                        return self
                    except:
                        #simply catch all as I dont want to import socket for socket.error
                        LOG.debug("try %d of %d, waiting %0.2fsec"%(c+1,retrycnt,retrydelay))
                        self.sleep(retrydelay)
        if not self.ssh_conn: 
            LOG.fatal("Connection FAILED - please check credentials, ip settings, ..")
            raise
        return self
        
    def reconnect(self):
        return self.connect_remote()
   
    
    def match_connection_uri(self,data,type=["ssh://","scp://"]):
        o={
           'user':None,
           'password':None,
           'host':None,
           'port':None,
           'path':None,           
           }
        if not isinstance(type,list): type=[type]           #make list :)
        
        for t in type:
            if t in data:     
                ssh_patterns=[r"%s(?P<user>[\w\.]+):(?P<passwd>\w+)@(?P<host>[\.\w]+):(?P<port>\d*)(?P<path>/+[\w/_-]*)"%t,           #ssh://user:pass@host:port
                              r"%s(?P<user>[\w\.]+):(?P<passwd>\w+)@(?P<host>[\.\w]+)(?P<path>/+[\w/_-]*)"%t,                         #ssh://user:pass@host
                              r"%s(?P<user>[\w\.]+)@(?P<host>[\.\w]+):(?P<port>\d*)(?P<path>/+[\w/_-]*)"%t,                           #ssh://user@host:port       #default port
                              r"%s(?P<user>[\w\.]+)@(?P<host>[\.\w]+)(?P<path>/+[\w/_-]*)"%t,                                         #ssh://user@host            #guess it
                              r"%s(?P<host>[\.\w]+):(?P<port>\d*)(?P<path>/+[\w/_-]*)"%t,
                              r"%s(?P<host>[\.\w]+)(?P<path>/+[\w/_-]*)"%t, 
                              ]
                # check if "ip" is a ssh:// uri connection string
                for p in ssh_patterns:
                    m = re.match(p,data)
                    if m:
                        try:
                            o['user']=m.group('user')
                        except: pass
                        try:
                            o['password']=m.group('passwd')
                        except: pass
                        try:
                            o['port']=int(m.group('port'))
                        except: pass
                        try:
                            o['path']=m.group('path')
                        except: pass
                        o['host']=m.group('host')                              #throw exception if not existent!
                        break       #done
        return o
        
    
    #-------------------------------------
    def sleep(self,seconds):
        time.sleep(seconds)
    
    def shellSSHRaw(self,command):
        #returns stdin,stdout,stderr = self.exec_command(command, bufsize)
        return self.ssh_conn.exec_command(command, -1)

    def shell(self,Command,write_stdin=None,bufsize=-1):
        '''
        use bufsize=0 (receive buffer) if you dont expect an answer .. = nonblocking operation
        '''
        LOG.debug(Command)
        return self.__exec_command(Command,bufsize=bufsize)
        
    
    
    def shellEx(self,Command,write_stdin=None,bufsize=-1):
        '''
        use bufsize=0 (receive buffer) if you dont expect an answer .. = nonblocking operation
        '''
        LOG.debug(Command)
        return self.__exec_command(Command,asString=True,bufsize=bufsize)
    #----------------------------------
    
    def set_defaults(self):
        LOG.debug("--- setting defaults :) ---")
        #a-pass
        #term width
        #ssh disconnect timeout
        #. ...
        return
    
    def beep(self,times=1):
        if self.is_BNNGF() or self.is_BNF():
            self.shellEx("modprobe pcspkr")
            for j in range(times):
                self.shellEx("hwtool --sound")
        elif self.is_LINUX():
            self.shellEx("modprobe pcspkr")
            for j in range(times):
                for i in range(5):
                    self.shellEx("echo -e '\a' > /dev/tty1")
        else:
            LOG.error("BEEP not implemented!")
        return
    
    #---------------------------------
    #
    # filesyystem commands
    #
    #  save filesystem ops
    #
    #
    #
    def grep(self,haystack,needle,case=True):
        if self.is_LOCAL():                     #prefer local fileops :)
            o = self.shell(haystack)
            if case:
                o = [needle in x for x in o]
            else:
                o = [str(needle).lower() in str(x).lower() for x in o]
        else:
            param = ""
            if not case: param="-i"
            o = self.shell("%s | grep %s '%s'"%(haystack,param,needle))  
        return o
                    
    
    def touch(self,path,data=None):
        o=""
        if self.is_LOCAL():                     #prefer local fileops :)
            o = open(path,'w')
            if not data:data=""
            o.write(data)
            o.close()
        else:
            self.rm(path)
            o +=self.shellEx("touch '%s' "%(path))
            if data and isinstance(data,str):
                o += self.shellEx("echo '%s' > '%s'"%(data,path))
            elif data and isinstance(data,list):
                for line in data:
                   o += self.shellEx("echo '%s' >> '%s'"%(line.rstrip("\n"),path))
            elif not data:
                pass                #pass this, just touch the file
            else:
                LOG.error("Incompatible Data for touch - %s"%path) 
        return o             
    def rm(self,path):
        if self.is_LOCAL():                     #prefer local fileops :)
            o = shutil.rmtree(path)
        else:
            o =self.shellEx("rm -rf '%s' "%(path))
        return o
    
    def isdir(self,path):
        if self.is_LOCAL():
            o = os.path.isdir(path)
        else:
            o = bool(len(self.shellEx("stat \"%s\" | grep -i 'directory'"%path)))         #True/false
        return o
    
    def isfile(self,path):
        if self.is_LOCAL():
            o = os.path.isfile(path)
        else:
            o = bool(len(self.shellEx("stat \"%s\" | grep -i 'regular file'"%path)))
        return o
    
    def islink(self,path):
        if self.is_LOCAL():
            o = os.path.islink(path)
        else:
            o = bool(len(self.shellEx("stat \"%s\" | grep -i 'symbolik link'"%path)))
        return o
    
    def mkdir(self,path,recursive=False):
        if self.is_LOCAL():                     #prefer local fileops :)
            if recursive:
                o = os.makedirs(path)
            else:
                o = os.mkdir(path)
        else:
            if recursive:
                o =self.shellEx("mkdir -p '%s' "%(path))
            else:
                o = self.shellEx("mkdir '%s'"%path)
        return o
    def mv(self,source,destination):
        if self.is_LOCAL():                     #prefer local fileops :)
            o = shutil.move(source,destination)
        else:
            o =self.shellEx("mv -rf '%s' '%s'"%(source,destination))
        return o  
    def cp(self,source,destination,recursive=False):
        if self.is_LOCAL():                     #prefer local fileops :)
            if recursive:
                o = shutil.copytree(source,destination)
            else:
                o = shutil.copy(source,destination)
        else:
            if recrusive:
                o =self.shellEx("cp -f '%s' '%s'"%(source,destination))
            else:
                o =self.shellEx("cp -rf '%s' '%s'"%(source,destination))
        return o
    def cat(self,path):
        if self.is_LOCAL():
            o = open(path,'r').readlines()
        else:
            o = self.shell("cat '%s'"%path)
        return o
    #---------------------------------
    
    
    def get_Version(self):
        return (self.NGFW_version,self.BFW_version)
    
    def get_Version_Build(self):
        res = "".join(self.cat(self.PATH['release']))
        g = re.search(r"(\d+)\.(\d+)\.(\d+)-(\d+)",res)
        
        try:
            return g.groups()
        except:
            pass
        return None

    def get_Model(self):
        hwtool_out = self.shell("hwtool -e")
        retn = {}        
        for i in hwtool_out:
            data = i.split("=")
            retn[data[0].strip()]=data[1].strip()
        return retn
    
    def get_SysInfo(self):
        o = {}  
        o['model']=self.get_Model()
        o['firmware']=self.get_Version()
        o['os']=self.get_Version_OS()
        
        return o

    def get_Box_Date(self):
        data = self.shellEx("date +%s")
        return datetime.fromtimestamp(float(data))
    
    def get_Version_OS(self):
        o={}

        if self.is_LOCAL():
            o['platform']=platform.platform()
            o['architecture']=platform.architecture()
            o['machine']=platform.machine()
            o['node']=platform.node()
            o['processor']=platform.processor()
            o['python-version']="%s-%s"%(platform.python_version(),platform.python_revision())
            o['release']=platform.release()
            o['system']=platform.system()
            o['uname']=platform.uname()
            o['version']=platform.version()
        else:
            uname = self.shellEx('uname -a').split(" " )
            o['platform']=self.shellEx('')
            o['architecture']=(uname[11],None)
            o['machine']=uname[11]
            o['node']=uname[1]
            o['processor']=None
            o['python-version']=self.shellEx('python -V')
            o['release']=uname[2]
            o['system']=uname[0]
            o['uname']=(uname[0],uname[1],uname[2]," ".join(uname[3:10]),uname[11],uname[12])
            o['version']=" ".join(uname[3:10])
            self.shellEx("uname -a")
        return o
    
    def get_Hostname(self):
        return self.shellEx("hostname")
    
    def get_Current_User(self):
        return self.shellEx("whoami")
    
    def set_Password(self,oldPass,newPass):
        return 
       
    def box_reboot(self):
        return self.shell("reboot")
    
    def box_halt(self):
        return self.shell("halt")
        
    
    def net_acpf_sra(self,enable=True):
        return self.shell("acpfctrl ips sra dis")
        
        
    def net_acpf_ips(self,enable=True):
        self.shell("acpfctrl ips dis")
        return
    
    def net_acpf_terminate_tcp_sessions(self,show=None):
        if show==None:
            show="noshow"
        else:
            show=""
        return self.shell("acpfctrl term fwd %s"%(show))
    
    def net_acpf_install_ips_patterns(self):
        return
    
    def net_configure(self):
        return
    
    def net_list_interfaces(self):
        final_iflist=[]
        for ifl in self.cat("/proc/net/dev"):
            if not ":" in ifl: continue
            final_iflist.append(ifl.split(":")[0].strip())
        return final_iflist
    
    def net_get_interfaces_offloading(self):
        iflist = self.net_list_interfaces()
        ifs={}
        for i in iflist:
            if_ethtool = self.shell("ethtool -k %s"%i)
            data = {}
            for x in if_ethtool:
                if ":" not in x: continue
                s_ifeth=x.split(":")
                if s_ifeth[1]=="\n":continue
                data[str(s_ifeth[0])]=s_ifeth[1].strip()
            ifs[i]=data
        return ifs
    
    @BNNGF_ONLY
    def conf_activate(self,conf_path):
        if not self.is_NGFW(): 
            LOG.debug("-- activate not available for non NGFW systems --")
            return False
       
        # validate conf path
        if not conf_path.startswith("%s/"%self.PATH['conf_root']) or not conf_path.endswith(".conf"):
            LOG.debug("-- invalid config file for config update: %s"%conf_path)
            return False
        
        #prepare copy to active
        print self.PATH['conf_root']
        print self.PATH['conf_active']
        print conf_path
        conf_active=conf_path.replace(self.PATH['conf_root'],self.PATH['conf_active'])
        print conf_active        
        #magic
        
        #self.shell("cp %s %s"%(conf_path,conf_path))
        self.shell("cp %s %s"%(conf_path,conf_active))
        return self.shell("%s"%(self.PATH['conf_activate']))
    
    @BNNGF_ONLY
    def get_net_acpf_stats(self):
        o = {       # list [ (x,y) ] of x,y tuples
            'in_out': {},
            'cpu'   : {},
            'field' : {},
            }
        rex = {  'in_out':    r'(\w+)\s+([0-9\.]+)\s+(\d+)\s+(\d+)\s+(\d+)',
                    'cpu':       r'CPU\[(\d+)\]:\s+(\d+)\s+(\d+)\s+(\d+.\d+)',
                  'field':     r'([\w ]+)=\s*(\d+)',
              }
        data = self.cat("/proc/phion/acpf_prof")
        for line in data:
            for k,v in rex.iteritems():
                m = re.search(v,line)
                if m: 
                    m=m.groups()
                    kname=str(m[0]).strip()
                    if not o[k].has_key(kname):
                        o[k][kname]=None
                    if len(m[1:])==1:
                        o[k][kname]=(m[1])
                    else:
                        o[k][kname]=(m[1:])
        return o
    
    
    def phibstest(self,scheme,username,password,returnBoolean=False):
        '''
            returns phibstest
            
            returnBoolean - return true or false on authentication ok
        
        '''
        x = self.shellEx("phibstest 127.0.0.1 e authscheme=%s user=%s password='%s'|head -1"%(scheme,username,password))
        
        if not returnBoolean:
            return x
    
        if not "Authentication OK" in x:
            return False
        else:
            return True
    
    
    def tcpdump(self,int="eth0",output="out.pcap",count=50, opts="", filter="", ):
        ''' Remote TCPDump and scp file to current dir'''
        #self.shell("rm -f %s"%filename)
        output_file=str.split(output,"\\")[-1]
        output_file=str.split(output_file,"/")[-1]
        retn = self.shellEx("tcpdump -i %s -w /tmp/%s -c %s %s %s"%(int,output_file,count,opts,filter))
        return self.ssh_conn.scp_get(remote_filename="/tmp/%s"%output_file,local_filename=output)
    
    def service_block(self,service):
        return
    
    def service_start(self,service):
        return
    
    def service_restart(self,service):
        return
    
    def set_interface_status(self,ifName,status):
        return self.shell("ifconfig %s %s"%(ifName,status))
    
    def get_interface_status(self,ifName=None):
        return
    
    def set_interface_default_gw(self):
        return
    
    def dmesg(self,human_readable_time=True,highlight=None):
        '''
        
        highlight= (pattern, highlight_profile)  ... pattern = ascii regex "\[.*\]", highlgiht profile= dict start:.. end:..or str starttag;endtag
        '''
        result=[]
        dmesg_data = self.shell('dmesg')
        if human_readable_time:
            uptime_data = "".join(self.cat('/proc/uptime'))
            _datetime_format = "%Y-%m-%d %H:%M:%S"
            _dmesg_line_regex = re.compile("^\[ *(?P<time>\d+\.\d+)\](?P<line>.*)$")
            now = self.get_Box_Date()
            uptime_diff = None
            
            try:
                uptime_diff = uptime_data.strip().split()[0]
                #print "uptime_diff = %s"%(uptime_diff)
                #print "box_date    = %s"%(now)
                #exit()
            except IndexError:
                LOG.warn("Index Error uptime data")
                return
            else:
                try:
                    uptime = now - timedelta(seconds=int(uptime_diff.split('.')[0]), microseconds=int(uptime_diff.split('.')[1]))
                except IndexError:
                    LOG.warn("index error uptime_diff")
                    return

            for line in dmesg_data:
                '''
                if not line:
                    print "not line - %s"%line
                    continue
                '''
                
                match = _dmesg_line_regex.match(line)
                if match:
                    try:
                        seconds = int(match.groupdict().get('time', '').split('.')[0])
                        nanoseconds = int(match.groupdict().get('time', '').split('.')[1])
                        microseconds = int(round(nanoseconds * 0.001))
                        line = match.groupdict().get('line', '')
                        t = uptime + timedelta(seconds=seconds, microseconds=microseconds)
                    except IndexError:
                        LOG.warn( "indexerror - line matching")
                        pass
                    else:
                        result.append("[%s]%s" % (t.strftime(_datetime_format), line))   
                        #print result[-1]
            
            #do some highlighting?
            if isinstance(highlight,list):
                #valid input is a list of higlight specs
                #defaults
                if len(highlight)<=0:
                    highlight=[]
                    highlight.append( tuple([ "\[[0-9-]{0,13} [0-9:]+\]","<font color=lightblue>;</font>" ])  )
                    highlight.append( tuple([ "fault","<SPAN style='BACKGROUND-COLOR:#ffff00'>;</SPAN>" ])  )
                    highlight.append( tuple([ "error","<SPAN style='BACKGROUND-COLOR:#ffff00'>;</SPAN>" ])  )
                    highlight.append( tuple([ "failure","<SPAN style='BACKGROUND-COLOR:#ffff00'>;</SPAN>"  ])  )
                    highlight.append( tuple([ "warn","<SPAN style='BACKGROUND-COLOR:#ffff00'>;</SPAN>"  ])  )
                    highlight.append( tuple([ "critical","<SPAN style='BACKGROUND-COLOR:#ffff00'>;</SPAN>"  ])  )
                #for every pattern
                highlight_data=[]
                qha = QA_Highlighter()
                
                    #for every line
                for line in result:
                    tmp=line
                    for ppp,highlight_profile in highlight:
                        tmp=qha.highlight(tmp, ppp, highlight_profile)
                    highlight_data.append(tmp )
                
                return result,highlight_data
            
        return result,dmesg_data
    

    
    def get_users(self):
        return self.shell("w")
    
    def query_rpm(self,rpmname):
        return self.shell("rpm -qa | grep %s"%(rpmname))
    
    def kernel_sysrq_trigger(self,trigger):
        return self.shell("echo %s > /proc/sysrq-trigger"%(trigger))
    
    def du(self,path):
        result = self.shellEx('du -s -b %s'%path)
        mSize=re.match(r"(\d+)",result)
        if mSize==None: return None
        return mSize.group(0)
    
    def is_LINUX(self):
        if self.is_NGFW(): return True
        LOG.debug("platform NOT LINUX")
        return False
    
    def is_NGFW(self):
        try:
            if self.NGFW_version==None: self.NGFW_version=self.get_Version_Build()
            if self.NGFW_version and len(self.NGFW_version)>0: return True
        except:
            LOG.debug("Exception - is_NGFW") 
        LOG.debug("platform NOT NGFW")
        return False
    
    #alias
    def is_BNNGF(self):
        return self.is_NGFW()
    
    def is_BFW(self):
        if self.is_NGFW():
            if self.BFW_version==None:
                tmp=self.shellEx('rpm -q phionnet_webui')
                if ("not installed" not in tmp): self.BFW_version="".join(self.cat("/home/product/code/firmware/current/revision"))
            if self.BFW_version and len(self.BFW_version)>0: return True
        return False
    #alias
    def is_WEBUI(self):
        return self.is_BFW()
    def is_BNF(self):
        return self.is_BFW()
    def is_LINUX(self):
        return "linux" in str(platform.platform()).lower()
    def is_WINDOWS(self):
        return "windows" in str(platform.platform()).lower()
    def is_LOCAL(self):
        return not self.is_REMOTE()
    def is_REMOTE(self):
        return self.BoxConn[0]=="REMOTE"
    
    
    def stat(self,path):
        #reStat = re.compile("\d{2}-\d{2}-\d{4}-\d{2}-\d{2}")
        #Size: (\d+).*Blocks: (\d+).*IO Block: (\d+).*([a-z])
        #fDate =  reDate.search(path).group()
        #result = self.shell('stat %s'%path)
        return
           
    def pwd(self):
        return self.shellEx("pwd")
        
    def ls(self,path,args='',filter=None):
        result=[]
        
        data = self.shell("ls %s %s"%(args,path))
        
        for f in data:
            if filter==None:
                result.append(f.replace("\n",""))
            else:
                filter=re.compile(filter)
                try:
                    m=re.match(filter,f).group(0)
                    result.append(f.replace("\n",""))
                except:
                    continue                
        return result
    
    def lsa(self,path,filter=None,options="-lsat",postcmd=""):
        # sample output
        # 4 drwxrwxrwt  2 root root    4096 2012-01-09 15:16 .X11-unix
        # filter = regex .. please escape the dot
        # cmdpost .. example  ls -lsat /path/to <cmdpost> like ls -lsat /path/to | grep bla
        result=[]
        data = self.ls(path + postcmd,options)    #-t sort by time
        for line in data:
            #print line
            fields=re.match(r' *(\d+) ([lrwsxdt-]+) +(\d+) (\w+) (\w+) +(\d+) .* ([\w_\-.]+)',line)
            if fields==None: continue
            #try:
            if filter!=None:
                filter = re.compile(filter)
                try:
                    m=re.match(filter,fields.group(7)).group(0)
                    result.append(tuple([fields.group(1),fields.group(2),fields.group(3),fields.group(4),fields.group(5),fields.group(6),fields.group(7)]))
                except:
                    continue  
            else:
                result.append(tuple([fields.group(1),fields.group(2),fields.group(3),fields.group(4),fields.group(5),fields.group(6),fields.group(7)])) 
            #except:
            #    pass
        return result
    
    def sys_request(self,cmd):
        '''
        0-9  ... set loglevel to 0-9
        c    ... crashdump
        B    ... reboot
        O    ... poweroff
        S    ... sync
        U    ... umount
        http://de.wikipedia.org/wiki/Magische_S-Abf-Taste
        '''
        self.shell("echo '%s' > /proc/sysrq-trigger"%cmd,bufsize=0)
    
    def sys_log_read(self,logfile=None,raw_output=False):
        '''
            read and parse the logfile
            raw_output= False: plaintext
            raw_output= True: column-wise parsed logfile
        '''
        assert(logfile) 
        res = []
        
        logfile = logfile.replace(self.PATH['sys_logs']+"/","")
        
        data = self.cat("%s/%s"%(self.PATH['sys_logs'],logfile))
        if raw_output: return "".join(data)
        
        for line in data:
            try:
                g = re.search(self.REGEX['logline'],line.rstrip())
                res.append(g.groups())
            except:
                LOG.warn("Exception parsing logline: %s"%line)
            
        return res
    
    def sys_log_check_rough(self,search_words=['error','failed','failure','fatal',' fault','nfault','abnormal','gfault'],exclusions=['default'],filename=None,raw_output=False):
        '''
            Perform content based logcheck
        '''
        search = str.lower("|".join(search_words))

        filename=filename or ""
        data=  self.shell("grep -r -i -E '%s' %s"%(search,self.PATH['sys_logs']+"/"+filename))    
        
        if filename:
            #append filename as first tuple element to maintain logfile structure <filename>:<date> <time> <Category> <UTC> <Logline>
            data = [ filename+":"+line for line in data]
            
        LOG.debug("LOGCHECK (rough) - found suspicious %d entries"%len(data))
        if raw_output: return "".join(data)    
        return data
    
    def sys_log_check_dmesg(self,search_words=['error','failed','failure','fatal',' fault','nfault','abnormal','gfault'],exclusions=['default'],raw_output=False):
        '''
            Perform content based logcheck
        '''
        search = str.lower("|".join(search_words))
        
        data=  self.shell("dmesg | grep -i -E '%s'"%(search))
                            
        LOG.debug("LOGCHECK (dmesg) - found suspicious %d entries"%len(data))
        if raw_output: return "".join(data)    
        return data
    
    def sys_log_check(self,search_words=['error','failed','failure','fatal',' fault','nfault','abnormal','gfault'],exclusions=['default'],whitelist=[],filename=None,raw_output=False,filter_duplicates=False):
        '''
            Perform log_level / Log_category based logcheck
            checks loglevel and logmessage for search_words
            * search_words: search for these words
            * exclusions:   exclude results with these words
            * whitelist:    mark entry as whitelisted (known errors)
        '''
        res=[]
        uniqe_messages=[]       #message history for filter_duplicates
        
        
        data = self.sys_log_check_rough(search_words=search_words,filename=filename)
        for line in data: 
            g = re.search(self.REGEX['logline_grep'],line.rstrip())
            try:
                rex_result = g.groups()
                # 0. filename
                # 1. date
                # 2. time
                # 3. loglevel
                # 4. [optional] timezone (+0200)
                # 5. message
                
                # check loglevel match
                if str.lower(rex_result[3]) in search_words and str.lower(rex_result[3]) not in exclusions:
                    if filter_duplicates and rex_result[-1] in uniqe_messages:
                        continue
                    # check whitelist
                    if rex_result[-1] in whitelist:
                        res.append( (self.MARKER['WHITELIST'],rex_result) )
                    else:
                        res.append( (self.MARKER['DEFAULT'],rex_result) )
                    #add to uniqe list
                    uniqe_messages.append(rex_result[-1])
                # check message match
                # check last field =message for occurance
                elif str.lower(rex_result[-1]) in search_words and str.lower(rex_result[-1]) not in exclusions:
                    if filter_duplicates and rex_result[-1] in uniqe_messages:
                        continue
                    # check whitelist
                    if rex_result[-1] in whitelist:
                        res.append( (self.MARKER['WHITELIST'],rex_result) )
                    else:
                        res.append( (self.MARKER['DEFAULT'], rex_result) )
                    #add to uniqe list
                    uniqe_messages.append(rex_result[-1])

            except:
                LOG.warn("Exception parsing logline: %s"%line) 
                raise

        LOG.debug("LOGCHECK (fine) - found suspicious %d entries"%len(res))
        
        for l in self.sys_log_check_dmesg(search_words=search_words,exclusions=exclusions):
            if rex_result[-1] in whitelist:
                res.append( (self.MARKER['WHITELIST'],tuple(['DMESG',None,None,None,None,l])))
            else:
                res.append( (self.MARKER['DEFAULT'],tuple(['DMESG',None,None,None,None,l]) ))
        LOG.debug("LOGCHECK (total) - found suspicious %d entries"%len(res))
        
        #if raw_output: return "".join(res)
        if raw_output: return "\n".join([ repr(entry) for entry in res])
        return res
    
    def sys_import_par(self):
        #copy par to /opt/phion/update
        #filename must be box.par
        #restart
        return
    
    def sys_export_par(self):
        return
    
    def sys_fw_restart(self):
        if len( self.shell("phionctrl shutdown") ) <=0: 
            LOG.warn("phionctrl NOT started")
            
        if len(self.shellEx("acpfctrl stop | grep -i -E 'FATAL|ACPF NOT'") )>0: return False
        acpfstart=self.shellEx("acpfctrl start")
        if "SUCCESS" not in acpfstart or "already loaded" in acpfstart or len(acpfstart)<=1: return False
        if len( self.shell("phionctrl startup"))>0: return False
        return True
    
    def sys_update(self,archive,force=False):
        #allow this only on NGFW systems (check version on connect)
        if not self.is_NGFW(): return
        
        res = []
        LOG.info("check if archive file is in remote location")
        if self.du(archive)==None:
            LOG.error("Missing archive in remote: %s"%archive)
            return
        
        LOG.info("check that archive contains str 'udpate'")
        # match                  update   .GWAY-5.4.0-274.nightbuild.tgz
        # groups                  0             1 2 3  4   5     
        archive_type=""
        try:
            archive_version =re.search(r"([a-zA-Z]+)\.GWAY-(\d+)\.(\d+)\.(\d+)-(\d+)\.([a-z]+)",archive).groups()
            LOG.info("got archive: type=%s, version=%s . %s . %s - %s,reltype=%s"%(archive_version))
            
            archive_type=archive_version[0]
            archive_version=archive_version[1:]     #realign to be on same indices            
        except:
            # maybe its a hotfix file
            try:
                # match                                 dhcp-424-5.2.1-41065.tgz
                # groups                                  1   2  3 4 5  6
                # rearrange filename to be compatible with other checks
                archive_data=re.search(r"([a-zA-Z]+)-(\d+)-(\d+)\.(\d+)\.(\d+)-(\d+)",archive).groups() 
                archive_type="hotfix"
                #rearrange_data
                archive_version=tuple([archive_data[3],archive_data[4],archive_data[5],archive_data[1],archive_data[2],archive_data[6]])
            except:
                pass

        LOG.info("check that update version > /etc/phion/release")        
        box_version = self.NGFW_version
        if archive_type != "update" and archive_type !="patch" and archive_type !="extra" and archive_type !="hotfix":
            LOG.error("invalid archive type: >>%s<<"%archive_type)
            return res
            
        elif archive_type == "update":
            #common test: check archive version is suitable
            if archive_version[0]<box_version[0]: 
                LOG.error("%s - archive major is lower than box version"%archive_type.capitalize())
                return res                   
            if archive_version[0]==box_version[0] and archive_version[1]<box_version[1]:
                LOG.error("%s - archive submajor is lower than box version"%archive_type.capitalize())
                return res        
            if archive_version[0]==box_version[0] and archive_version[1]==box_version[1] and archive_version[2]<box_version[2]:
                LOG.error("%s - archive minor is lower than box version"%archive_type.capitalize())
                return res            
            if archive_version[0]==box_version[0] and archive_version[1]==box_version[1] and archive_version[2]==box_version[2] and archive_version[3]<=box_version[3]:
                LOG.error("%s - archive is same major version as box version, use patch instead!"%archive_type.capitalize())
                return res
            
        elif archive_type == "patch":
            if archive_version[0]<box_version[0]: 
                LOG.error("%s - archive major is lower than box version"%archive_type.capitalize())
                return res                   
            if archive_version[0]==box_version[0] and archive_version[1]<box_version[1]:
                LOG.error("%s - archive submajor is lower than box version"%archive_type.capitalize())
                return res        
            if archive_version[0]==box_version[0] and archive_version[1]==box_version[1] and archive_version[2]<box_version[2]:
                LOG.error("%s - archive minor is lower than box version"%archive_type.capitalize())
                return res            
            if archive_version[0]==box_version[0] and archive_version[1]==box_version[1] and archive_version[2]==box_version[2] and archive_version[3]<=box_version[3]:
                LOG.error("%s - archive is same major version as box version, use patch instead!"%archive_type.capitalize())
                return res
        elif archive_type == "extra" or archive_type=="hotfix": 
            if archive_version[0]<box_version[0]: 
                LOG.error("%s - archive major is lower than box version"%archive_type.capitalize())
                return res                   
            if archive_version[0]==box_version[0] and archive_version[1]<box_version[1]:
                LOG.error("%s - archive submajor is lower than box version"%archive_type.capitalize())
                return res        
            if archive_version[0]==box_version[0] and archive_version[1]==box_version[1] and archive_version[2]<box_version[2]:
                LOG.error("%s - archive minor is lower than box version"%archive_type.capitalize())
                return res
            
            #extra package must be same version
            if not (archive_version[0]==box_version[0] and archive_version[1]==box_version[1] and archive_version[2]==box_version[2]):
                LOG.error("%s - Version Mismatch - archive version not suitable. "%archive_type.capitalize())
                return res                                      
        else:
            LOG.error("archive is not suitable for this box release")
            return res
        
        LOG.info("remove old files in /var/phion/packages/tgz")
        res.append(self.shellEx("rm -f %s/*"%self.PATH['tgz']))
        LOG.info("create /var/phion/packages/tgz")
        res.append(self.shellEx("mkdir -p %s"%self.PATH['tgz']))
        LOG.info("extract tar to /var/phion/packages")
        res.append(self.shellEx("tar xzf %s -C %s"%(archive,self.PATH['tgz'])))
        LOG.info("check if everything got extracted")
                
        LOG.info("modify hotfixrpms")
        res.append(self.shellEx("sed -i \"s/install_range = ('5/install_range = ('%s.%s.%s', '5/g\" %s/hotfixrpms.py"%(box_version[0],box_version[1],box_version[2],self.PATH['tgz'])))
        if force:
            LOG.info("modify to force rpm update")
            res.append(self.shellEx("sed -i \"s/rpm -Uvh --i/rpm -Uvh --force --i/g\" %s/doit"%(self.PATH['tgz'])))
        
        LOG.info("install updates")
        res.append(self.shell("cd %s && %s/doit"%(self.PATH['tgz'],self.PATH['tgz'])))
        
        LOG.info("install done, checking results for errors, warnings, etc")
        
        for entry in res:
            for errstr in self.ERROR_STRINGS:
                #check if one of theses strings occurs in one entry
                if errstr in entry:
                    LOG.warn("[found: %s] %s"%(errstr,entry))
            
                   
        LOG.info("updated finished, check result") 
        
        #LOG.info("cleaning up")
        #res.append(self.shellEx("rm -f %s/*"%self.PATH['tgz']))
        return res
    
    def sys_update_from_repofile(self,repo,filename,repobase=None,force=False):
        #need a filename only
        if not isinstance(repo,QA_NGFW) and not isinstance(repo,str):
            LOG.error("repo argument not suitable! (expected: QA_NGFW,str)")
            return
        
        
        #get version and type from filename
        if "/" in filename:
            #this is a path, discourage it or use it as full path
            LOG.debug("%s is a path!"%filename)
            remote_file=filename
            filename=filename.split("/")[-1]    #get last part of file
        else:
            LOG.debug("%s is a filename, parsing"%filename)
            remote_file=self.repofile_to_dir(filename,repobase)
            
        LOG.debug("local filename: %s/%s\tremote filename:%s"%(self.PATH['packages'],filename,remote_file))
        result = self.scp_raw_get(repo, remote_file, '%s/%s'%(self.PATH['packages'],filename))
        if not result[0]:
            LOG.error("scp error: %s"%repr(result))
            return

        return self.sys_update('%s/%s'%(self.PATH['packages'],filename),force)
        
    
    def scp_raw_cmd(self,cmd,timeout=25):
        # 
        # timeout per received line
        #
        SUCCESS=False
        if not self.is_LINUX(): return (False,None)
        
        LOG.debug(cmd)
        
        chan = self.ssh_conn.invoke_shell()
        chan.settimeout(timeout)
        chan.send("\n\n")
        self.sleep(3)
        chan.send(cmd)
        
        buff=''
        prevlen=-1
        while buff=='' or len(buff)!=prevlen:
            chan.settimeout(timeout)
            prevlen=len(buff)
            tmp=chan.recv(9999)
            #print tmp
            buff+=tmp
            tmp=str(tmp).lower()
            if "(yes/no)?" in tmp: 
                chan.send("yes\n")
            elif "password:" in tmp: 
                chan.send("a\n")
            elif "100%" in tmp: 
                SUCCESS=True
                break
            elif "no such" in tmp: break
        return (SUCCESS,buff)
    
    
    def scp_raw_put(self,local_file,remote_host,remote_file,user=None,password=None,scpOptions=default_raw_SCP_options):
        # remote_hoss should be QA_NGFW type
        res=[]
        if scpOptions==None:
            scpOptions=[]
        elif isinstance(scpOptions,str):
            scpOptions=[(scpOptions)]
        
        scpOptionsParam = ' -o '.join(scpOptions)
        if len(scpOptions)<=0:
            scpOptionsParam=""
        else:
            scpOptionsParam = "-o %s"%(scpOptionsParam)

        if isinstance(remote_host,QA_NGFW):
            LOG.debug("got QA_NGFW object for file transfer")
            user=remote_host.BoxConn[3]
            password=remote_host.BoxConn[4]
            remote_host=remote_host.BoxConn[1]
        elif isinstance(remote_host,str):
            LOG.debug("got host string")
        else:
            LOG.error("no suitable remote host")

        return self.scp_raw_cmd("scp %s %s %s@%s:%s\n"%(scpOptionsParam,local_file,user,remote_host,remote_file))

    def scp_raw_get(self,remote_host,remote_file,local_file,user=None,password=None,scpOptions=default_raw_SCP_options):
        # remote_hoss should be QA_NGFW type
        res=[]
        if scpOptions==None:
            scpOptions=[]
        elif isinstance(scpOptions,str):
            scpOptions=[(scpOptions)]
        
        scpOptionsParam = ' -o '.join(scpOptions)
        if len(scpOptions)<=0:
            scpOptionsParam=""
        else:
            scpOptionsParam = "-o %s"%(scpOptionsParam)

        if isinstance(remote_host,QA_NGFW):
            LOG.debug("got QA_NGFW object for file transfer")
            user=remote_host.BoxConn[3]
            password=remote_host.BoxConn[4]
            remote_host=remote_host.BoxConn[1]
        elif isinstance(remote_host,str):
            LOG.debug("got host string")
        else:
            LOG.error("no suitable remote host")
        
        return self.scp_raw_cmd("scp %s %s@%s:%s %s\n"%(scpOptionsParam,user,remote_host,remote_file,local_file))

        
    def repofile_to_dir(self,filename,repobase=None):
        # translate fw update filename to path
        # maybe dir and search for file in subdirs
        repobase = repobase or self.PATH['repo_base']
        
        REPO_CONVERSION = {
                     'extra':'extra-packages',
                     'update':'updates',
                     'patch':'patches',
                     'hotfix':'hotfixes',
                     #hotfixes missing
                     }
        #match filename
        try:
            archive_version =re.search(r"([a-zA-Z]+).GWAY-(\d+)\.(\d+)\.(\d+)-(\d+)\.([a-z]+)",filename).groups()
            archive_versionstring = "%s.%s.x"%(archive_version[1],archive_version[2])
            remote_file = "%s/%s/%s/%s"%(repobase,archive_versionstring,REPO_CONVERSION[str(archive_version[0])],filename)
        except:
            #match hotfixes
            try:
                archive_version =re.search(r"([a-zA-Z]+).*-(\d+)\.(\d+)\.(\d+)-(\d+)\.([a-z]+)",filename).groups()
                archive_versionstring = "%s.%s.x"%(archive_version[1],archive_version[2])
                remote_file = "%s/%s/%s/%s"%(repobase,archive_versionstring,REPO_CONVERSION['hotfix'],filename)
            except:
                return None
        
        return remote_file
    
    @BNF_ONLY
    def BNF_lic_fake(self,action=None):
        '''
            Fake bfw lics to be able to load IDP
            
            action == add    --- creates fake lic
            action == None   --- just print it
            action == del    --- kill all lics,
        '''
        msg=""
        fw_version = "".join(self.get_Version_Build()[:-1])
        model = self.get_Model()
        dbg=""
        
        files = ['/etc/barracuda/activated',
                 '/var/tmp/update_cache.firmware',

                 '/art/barracuda/keys/bcc.csr',
                 '/art/barracuda/keys/barrsec-serial.key',
                 '/art/barracuda/keys/barrsec-serial.csr',
                 '/art/barracuda/keys/barrsec-serial.bcc.crt',
                 
                 '/home/bfw/code/firmware/%s/bin/spinco.pl'%fw_version,
                 '/home/product/code/firmware/current/bin/update.pl',
                 
                 ]
        
        

        
        if action=="add":
            dbg+="FAKE\n"
            LOG.debug("killing spinco ...")
            dbg+=self.shellEx("/etc/init.d/spinco stop")   
            dbg+=self.shellEx("killall -9 update.pl")   
            
            if "No such file" in self.shellEx("ls /etc/barracuda/fakelic"):
                dbg+="no fakelic found\n"
                LOG.debug("backing up files ...")
                # backup all files :)
                for f in files:
                    #self.shellEx("cp %s %s.bak"%(f,f))
                    self.cp(f,f+".bak")
                
                
                dbg+=self.touch('/home/product/code/firmware/current/bin/update.pl', 'exit 0;')
                dbg+=self.touch("/home/bfw/code/firmware/%s/bin/spinco.pl"%fw_version,'exit 0;')
                #dbg+=self.shellEx("echo 'exit 0;' > /home/product/code/firmware/current/bin/update.pl")
                #dbg+=self.shellEx("echo 'exit 0;' > /home/bfw/code/firmware/%s/bin/spinco.pl"%fw_version)
            else:
                dbg+="fakelic found\n"
    
            LOG.debug("creating empty fake keys ...")
            #dbg+=self.shellEx("mkdir /art/barracuda/keys/")
            dbg+=self.mkdir("/art/barracuda/keys/",recursive=True)
            dbg+=self.touch("/art/barracuda/keys/barrsec-%s.bcc.crt"%model['SN'])
            dbg+=self.touch("/art/barracuda/keys/barrsec-%s.csr"%model['SN'])
            dbg+=self.touch("/art/barracuda/keys/barrsec-%s.key"%model['SN'])
            dbg+=self.touch("/art/barracuda/keys/bcc.csr")
            '''
            dbg+=self.shellEx("touch /art/barracuda/keys/barrsec-%s.bcc.crt"%model['SN'])
            dbg+=self.shellEx("touch /art/barracuda/keys/barrsec-%s.csr"%model['SN'])
            dbg+=self.shellEx("touch /art/barracuda/keys/barrsec-%s.key"%model['SN'])
            dbg+=self.shellEx("touch /art/barracuda/keys/bcc.csr")
            '''     
            lic_tpl='''Ga-Versions:
Energize-Status: 1
Barracuda-Timestamp: 1348650734
Update-File-Type: full
Ea-Versions:
Full-Serial: BAR-FW-##SERIAL##
Barracuda-Server: upd03
Full-Prodname: Firewall ##MODEL##
Subscription-Expired: FALSE
Req-Status: 0
New-Date:
Update-File-Size:
Premium-Expiration: 1378018799
WebSecurity-Status: 1
Rem-Address: 80.109.152.164
Req-Method: POST
Inst-Replace-Expiration: 1378018799
Rem-Location: AT
Inst-Replace-Nag: N
Inst-Replace-Status: 1
Update-Release-Notes:
Activation: 1346371200
File-Size:
WebSecurity-Expiration: 1378018799
Release-Notes:
Premium-Status: 1
Update-Version:
Update-Date:
Activated-Status: 1
Energize-Expiration: 1378018799
New-Version:
Fakelic-TimeStamp: %s'''%time.time()
            
            
            lic_tpl=lic_tpl.replace("##SERIAL##",model['SN'])
            lic_tpl=lic_tpl.replace("##MODEL##", model['MODEL'])
                    
            #clear config
            LOG.debug("write lic conf ...")
            
            dbg+=self.touch("/var/tmp/update_cache.firmware",data=lic_tpl.split("\n"))
            '''
            for l in lic_tpl.split("\n"):    
                dbg+=self.touch("echo '%s' >> /var/tmp/update_cache.firmware"%l)
            '''
            LOG.debug("tell everyone im activated ...")
            dbg+=self.touch("/etc/barracuda/activated")

            self.touch("/etc/barracuda/fakelic")
            msg="Successfully faked lic :)\n\n"
        elif action=="del":
            dbg+="RESTORE\n"
            if "No such file" in self.shellEx("ls /etc/barracuda/fakelic"):
                return "Not a fakelic - lic :( cannot restore"
            
            # restore all files
            for f in files:
                self.rm(f)
                self.mv(f+".bak",f)
                #dbg+=self.shellEx("rm -f %s"%f)            #kill the files :)
                #dbg+=self.shellEx("mv -f %s.bak %s"%(f,f)) #restore them if bakcup file exists
                
            #delete fakelic file :p
            dbg+=self.rm("/etc/barracuda/fakelic")
            dbg+=self.shellEx("/etc/init.d/spinco start")
            msg="Successfully Restored lic :)\n\n"
            
        LOG.debug("comit ...")
        output = self.shellEx("/etc/phion/bin/bfwsetup.cnf")
        return (msg+output,dbg)
    
    def open_scp(self,socket_timeout =None, progress = None):
        if self.ssh_conn: 
            self.scp= self.ssh_conn.open_scp(socket_timeout =socket_timeout, progress = progress)
            return self.scp
        else:
            
            LOG.warning("SCP: NON-Existent SSH Connection - cannot open scp transport... (%s)"%self.ssh_conn)
        return None
    
    def open_sftp(self):
        return self.ssh_conn.open_sftp()
    
    def service_control_disable_ssl(self):
        #/opt/phion/config/active/boxadm.conf   NOSSL=1
        return
    
    def dbg_dbg(self):
        return self.shell("date")
    @BNF_ONLY
    def BNF_get_db(self):
        data = self.shell("webuicmd db2conf rawdump /opt/phion/preserve/cuda.vars -")
        return Bnf_Db().format_database(data)
    
    def check_host(self, ip=None, port=22,tries=25, trydelay=60, minSuccessfulConnections=6,successdelay=15, startdelay=0):
        '''
           Args:
               ip               ... if None, use own ip
               tries            ... number of tries
               delay            ... between each try
               successdelay     ... delay between successful tries
               minSuccessfulConnections ... minimum successfull connections to pass this test 
               
        '''
        if not self.BoxConn[0]=="LOCAL":
            ip = ip or self.BoxConn[1]
        if self.BoxConn[0]=="LOCAL" and ip ==None:
            LOG.error("Checkhost - missing host/IP (connection type=LOCAL and IP=None)")
            raise
        
        LOG.info("Checkhost - %s:%s"%(ip,port))
        if startdelay:
            LOG.info("Checkhost - startdelay set - waiting for %d seconds before starting to check ..." % startdelay)
            time.sleep(startdelay)
        
        for i in range(tries):
            LOG.info("Checkhost - Try ... #%s"%(i+1))
            try:
                c = 0
                while c < minSuccessfulConnections:
                    time.sleep(successdelay)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((ip, port))
                    LOG.SUCCESS("Checkhost - connected ... %s"%(c+1))
                    s.close()
                    c += 1
                return True
            except socket.error:
                s.close()
            time.sleep(trydelay)     
        LOG.warning("Checkhost - Host is down")
        return False
        
        
     
#---------- testme
if __name__=='__main__':
    mybox = QA_NGFW()
    mybox.open("10.17.67.123",user="root")
    print mybox.shellEx("echo hi")
    #mybox.BNF_get_db()
    exit()
    #repo = QA_NGFW()
    #mybox.connect_local()
    #mybox.connect_remote('10.17.71.245', 22,guess_credentials=True)
    #mybox.open("ssh://10.17.71.151")        #now allows full ssh:// uri :)))
    #print mybox.BNF_lic_fake(action='add')
    #mybox.open("scp://www:www@aaa.com:/alala/fff/asa")
    mybox.open("ssh://root:a@10.17.71.241:/",scp=True)
    mybox.scp.put(files="c:\\_tmp\\skipfish\skipfish",remote_path="/var/www/skipfish2",recursive=True)
    #s = mybox.open_scp()
    #s.put(files="c:\\_tmp\\skipfish\skipfish",remote_path="/var/www/skipfish2",recursive=True)
    #s = mybox.open_scp()
    #a,b= mybox.BNF_lic_fake(action='fake')
    print "bla"
    exit()
    #for item in mybox.sys_log_check(): print item
    #print "---"
    #for item in mybox.sys_log_check(filename="box_Control_admin.log"): print item
    #for line in  mybox.sys_log_read("/var/phion/logs/box_Network_shaping.log"): print line
    #print "---"
    #for line in  mybox.sys_log_read("box_Network_shaping.log"): print line
    #print "---"
    #for line in mybox.sys_log_check_rough():print line
    #repo.connect_remote('10.17.67.90')
    #mybox.connect_remote('10.17.70.25', 22, 'root', 'a')
    #for l in mybox.connect_remote('10.17.71.10').dmesg(highlight=[])[1]: print l
    #print data[1]
    #for l in mybox.connect_remote('10.0.6.169').dmesg(): print l
    #for item in mybox.connect_remote('10.17.71.198').sys_log_check(raw_output=False): print item
    #print mybox.is_BFW()
    #print mybox.sleep(2)
    #print mybox.get_net_acpf_stats()
    #x = mybox.open_scp()
    for i in mybox.sys_log_check(filter_duplicates=True,search_words=["error","fault"],whitelist=[' atd: Exec faile for mail command: No such file or directory']): print i
    
    #mybox.conf_activate("/opt/phion/config/configroot/aaa.conf")
    #print mybox.ls("/")
    #print mybox.sys_update_from_repofile(repo, "/root/repo/5.4.x/updates/update.GWAY-5.4.0-321.nightbuild.tgz")

    #for i in repo.lsa("/root/repo/5.2.x/updates/",filter=".*\.tgz"):print i
    #print repo.shell('ls /root/repo/5.4.x/updates')
    #print mybox.shell("ls /root")
    #print "transferring.."
    #for i in mybox.dmesg(human_readable_time=True): print i
    #print mybox.shellEx("dmesg")
    #repo.scp_transfer(local_file="/root/repo/5.4.x/updates/update.GWAY-5.4.0-286.nightbuild.tgz", remote_host='10.0.66.49', remote_file="/var/phion/packages/",user="root",password="a")
    #print mybox.scp_raw_get(remote_host=repo,remote_file="/root/repo/5.4.x/updates/update.GWAY-5.4.0-286.nightbuild.tgzd",local_file="/var/phion/packages")
    #print mybox.sys_update("/var/phion/packages")
    #shell = repo.ssh_conn.invoke_shell()
    #stdin,stdout,stderr= repo.shellSSHRaw("dmesg")
    #stdin.write("a\n")
    #stdin.flush()
    #print stdout.readlines()
    #print stderr.readlines()
    #print repo.scp_transfer(local_file="/root/repo/5.4.x/updates/update.GWAY-5.4.0-286.nightbuild.tgz", remote_host=mybox, remote_file="/var/phion/packages/")
    #print mybox.shell("ls /var/phion/packages/")
    #print mybox.dbg_dbg()
    #print mybox.get_Version_Build()
    #print mybox.du("/var/phion/packages/")
    #print mybox.shell("ls")
    #print mybox.shellEx("ls")
    #print mybox.sys_update(archive="/var/phion/packages/update.GWAY-5.4.0-287.nightbuild.tgz",force=True)
    print "--end--"
