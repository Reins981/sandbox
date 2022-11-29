'''
    paramiko ++
        + scp_put    ## binary put! tested win -> linux
        + scp_get    ## binary get! tested get file from linux -> windows 
        
'''


"""
Utilities for sending files over ssh using the scp1 protocol.
credits: https://github.com/jbardin/scp.py
"""

import os,fnmatch
from socket import timeout as SocketTimeout

class SCPClient(object):
    """
    An scp1 implementation, compatible with openssh scp.
    Raises SCPException for all transport related errors. Local filesystem
    and OS errors pass through. 

    Main public methods are .put and .get 
    The get method is controlled by the remote scp instance, and behaves 
    accordingly. This means that symlinks are resolved, and the transfer is
    halted after too many levels of symlinks are detected.
    The put method uses os.walk for recursion, and sends files accordingly.
    Since scp doesn't support symlinks, we send file symlinks as the file
    (matching scp behaviour), but we make no attempt at symlinked directories.
    """
    def __init__(self, transport, buff_size = 16384, socket_timeout = 5.0, progress = None):
        """
        Create an scp1 client.

        @param transport: an existing paramiko L{Transport}
        @type transport: L{Transport}
        @param buff_size: size of the scp send buffer.
        @type buff_size: int
        @param socket_timeout: channel socket timeout in seconds
        @type socket_timeout: float
        @param progress: callback - called with (filename, size, sent) during transfers
        @type progress: function(string, int, int)
        """
        self.transport = transport
        self.buff_size = buff_size
        self.socket_timeout = socket_timeout
        self.channel = None
        self.preserve_times = False
        self._progress = progress
        self._recv_dir = ''
        self._utime = None
        self._dirtimes = {}
        
    def __del__(self):
        if self.channel:
            self.channel.close()
        

    def put(self, files, remote_path = '.', 
            recursive = False, preserve_times = False):
        """
        Transfer files to remote host.

        @param files: A single path, or a list of paths to be transfered.
            recursive must be True to transfer directories.
        @type files: string OR list of strings
        @param remote_path: path in which to receive the files on the remote
            host. defaults to '.'
        @type remote_path: str
        @param recursive: transfer files and directories recursively
        @type recursive: bool
        @param preserve_times: preserve mtime and atime of transfered files
            and directories.
        @type preserve_times: bool
        """
        self.preserve_times = preserve_times
        self.channel = self.transport.open_session()
        self.channel.settimeout(self.socket_timeout)
        scp_command = ('scp -t %s', 'scp -r -t %s')[recursive]
        self.channel.exec_command(scp_command % remote_path)
        self._recv_confirm()
       
        if not isinstance(files, (list, tuple)):
            files = [files]
        
        self._send_files(files,recursive=recursive)
        
    
    def get(self, remote_path, local_path = '',
            recursive = False, preserve_times = False):
        """
        Transfer files from remote host to localhost

        @param remote_path: path to retreive from remote host. since this is
            evaluated by scp on the remote host, shell wildcards and 
            environment variables may be used.
        @type remote_path: str
        @param local_path: path in which to receive files locally
        @type local_path: str
        @param recursive: transfer files and directories recursively
        @type recursive: bool
        @param preserve_times: preserve mtime and atime of transfered files
            and directories.
        @type preserve_times: bool
        """
        self._recv_dir = local_path or os.getcwd() 
        rcsv = ('', ' -r')[recursive]
        prsv = ('', ' -p')[preserve_times]
        self.channel = self.transport.open_session()
        self.channel.settimeout(self.socket_timeout)
        self.channel.exec_command('scp%s%s -f %s' % (rcsv, prsv, remote_path))
        self._recv_all()
        #if self.channel:
        #    self.channel.close()


    def _read_stats(self, name):
        """return just the file stats needed for scp"""
        stats = os.stat(name)
        mode = oct(stats.st_mode)[-4:]
        size = stats.st_size
        atime = int(stats.st_atime)
        mtime = int(stats.st_mtime)
        return (mode, size, mtime, atime)
    
    def _send_single_files(self,files):
        if isinstance(files,str):files=[files]
        for name in files:
           basename = os.path.basename(name)
           (mode, size, mtime, atime) = self._read_stats(name)
           if self.preserve_times:
               self._send_time(mtime, atime)
           file_hdl = file(name, 'rb')
           self.channel.sendall('C%s %d %s\n' % (mode, size, basename))
           self._recv_confirm()
           file_pos = 0
           buff_size = self.buff_size
           chan = self.channel
           if self._progress:
               self._progress(name, size, 0)        #send 0 progress to detect begin :)
           while file_pos < size:
               chan.sendall(file_hdl.read(buff_size))
               file_pos = file_hdl.tell()
               if self._progress:
                   self._progress(name, size, file_pos)
           chan.sendall('\x00')
           file_hdl.close()
        

    def _send_files(self, files,filter=[],recursive=False): 
        """
        Send files to remote destination
            
        @param files: list of files or paths to be transferred to remote destination (all files are put into the dest. dir!)
        @type files: either str or list
        @param filter: list of fnmatch filters (*,*.c,..) empty list = no filtering
        @type filter: either str or list
        @param recursive: recurse into subdirs
        @type recursive: boolean
        """
        # for loop for recursive transfers
        # will only return one dir if recursive = False
        #handle multiple paths
        if isinstance(files,str):files=[files]
        for base in files:
            if os.path.isfile(base):
                #is file
                self._send_single_files(base)               
            elif os.path.isdir(base):
                #is pure dir
                last=base   #save base for get_dir_level_diff
                for root, fls in self._list_dir(base,filter,recursive=recursive):
                    # build file-list for transfer, and transfer file by file
                    pop,push= self.__traverse_dir_instruction(last,root)
                    last = root
                    for i in range(pop):
                        self._send_popd()
                    for i in range(push):
                        self._send_pushd(root)
                    
                    #actually transfer files
                    self._send_single_files([os.path.join(root, f) for f in fls])
            elif not os.path.isfile(base) and not os.path.isdir(base):
                #wildcarded filename               
                for root,fls in self._list_dir(os.path.dirname(base),filters=os.path.basename(base),recursive=False):
                    self._send_single_files([os.path.join(root, f) for f in fls])
                
                

              
    def _list_dir(self,paths,filters=[],recursive=False):
        ffiles=[]
        if isinstance(filters,str):filters=[filters]  
        if isinstance(paths,str):paths=[paths]    
        
        for root in paths:
            for root,dirs,files in os.walk(root,topdown=True):
                if len(filters)>0:
                    ffiles=[]
                    for f in filters:
                        ffiles+= fnmatch.filter(files,f)   #join with prev. files  
                    #return root dir + unique files
                    files=ffiles    #filtered files
                yield root,set(files) 
                if not recursive: break 
             
             
    def __normalize_path(self,p):
        p = os.path.normpath(p) # normalize /x/../A/./../b/ to /b/
        p=p.replace("\\","/")   # normalize path to unix path
        return p 
                  
    def __traverse_dir_instruction(self,a,b):
        '''
        Calculate the number of POPs and PUSHs to get from dir a to dir b
        Returns (pops,pushs)
        '''
        a=self.__normalize_path(a)
        b=self.__normalize_path(b)
        if a[-1]=="/": a=a[:-1] # kill trailing / (to avoid extra pushes/pops)
        if b[-1]=="/": b=b[:-1]
        last = a.split("/")      # listify
        current = b.split("/")
        #compare last to current
        pos=0
        for e in last:
            if pos>=len(current) or e!=current[pos]: break
            pos +=1 
        #calc_pops / pushes from last_dir to current dir
        num_pops= len(last)-pos
        num_pushs= len(current)-pos
        return num_pops,num_pushs
        
    def _send_pushd(self, directory):
        (mode, size, mtime, atime) = self._read_stats(directory)
        basename = os.path.basename(directory)
        if self.preserve_times:
            self._send_time(mtime, atime)
        self.channel.sendall('D%s 0 %s\n' % (mode, basename))
        self._recv_confirm()

    def _send_popd(self):
        self.channel.sendall('E\n')
        self._recv_confirm()

    def _send_time(self, mtime, atime):
        self.channel.sendall('T%d 0 %d 0\n' % (mtime, atime))
        self._recv_confirm()

    def _recv_confirm(self):
        # read scp response
        msg = ''
        try:
            msg = self.channel.recv(512)
        except SocketTimeout:
            raise SCPException('Timout waiting for scp response')
        if msg and msg[0] == '\x00':
            return
        elif msg and msg[0] == '\x01':
            raise SCPException(msg[1:])
        elif self.channel.recv_stderr_ready():
            msg = self.channel.recv_stderr(512)
            raise SCPException(msg)
        elif not msg:
            raise SCPException('No response from server')
        else:
            raise SCPException('Invalid response from server: ' + msg)
    
    def _recv_all(self):
        # loop over scp commands, and recive as necessary
        command = {'C': self._recv_file,
                   'T': self._set_time,
                   'D': self._recv_pushd,
                   'E': self._recv_popd}
        while not self.channel.closed:
            # wait for command as long as we're open
            self.channel.sendall('\x00')
            msg = self.channel.recv(1024)
            if not msg: # chan closed while recving
                break
            code = msg[0]
            try:
                command[code](msg[1:])
            except KeyError:
                raise SCPException(repr(msg))
        # directory times can't be set until we're done writing files
        self._set_dirtimes()
    
    def _set_time(self, cmd):
        try:
            times = cmd.split()
            mtime = int(times[0])
            atime = int(times[2]) or mtime
        except:
            self.channel.send('\x01')
            raise SCPException('Bad time format')
        # save for later
        self._utime = (atime, mtime)

    def _recv_file(self, cmd):
        chan = self.channel
        parts = cmd.split()
        try:
            mode = int(parts[0], 8)
            size = int(parts[1])
            path = os.path.join(self._recv_dir, parts[2])
        except:
            chan.send('\x01')
            chan.close()
            raise SCPException('Bad file format')
        
        try:
            file_hdl = file(path, 'wb')
        except IOError, e:
            chan.send('\x01'+e.message)
            chan.close()
            raise

        buff_size = self.buff_size
        pos = 0
        chan.send('\x00')
        try:
            while pos < size:
                # we have to make sure we don't read the final byte
                if size - pos <= buff_size:
                    buff_size = size - pos
                file_hdl.write(chan.recv(buff_size))
                pos = file_hdl.tell()
                if self._progress:
                    self._progress(path, size, pos)
            
            msg = chan.recv(512)
            if msg and msg[0] != '\x00':
                raise SCPException(msg[1:])
        except SocketTimeout:
            chan.close()
            raise SCPException('Error receiving, socket.timeout')

        file_hdl.truncate()
        try:
            os.utime(path, self._utime)
            self._utime = None
            os.chmod(path, mode)
            # should we notify the other end?
        finally:
            file_hdl.close()
        # '\x00' confirmation sent in _recv_all

    def _recv_pushd(self, cmd):
        parts = cmd.split()
        try:
            mode = int(parts[0], 8)
            path = os.path.join(self._recv_dir, parts[2])
        except:
            self.channel.send('\x01')
            raise SCPException('Bad directory format')
        try:
            if not os.path.exists(path):
                os.mkdir(path, mode)
            elif os.path.isdir(path):
                os.chmod(path, mode)
            else:
                raise SCPException('%s: Not a directory' % path)
            self._dirtimes[path] = (self._utime)
            self._utime = None
            self._recv_dir = path
        except (OSError, SCPException), e:
            self.channel.send('\x01'+e.message)
            raise

    def _recv_popd(self, *cmd):
        self._recv_dir = os.path.split(self._recv_dir)[0]
        
    def _set_dirtimes(self):
        try:
            for d in self._dirtimes:
                os.utime(d, self._dirtimes[d])
        finally:
            self._dirtimes = {}


class SCPException(Exception):
    """SCP exception class"""
    pass

import sys
import paramiko # apt-get install python-paramiko
# scp.py
# Copyright (C) 2008 James Bardin <jbar...@bu.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


class QA_SSH(paramiko.SSHClient):  
    
    
    '''    
    def __init__(self):
        return super(self.__class__,self).__init__()        #paramiko.SSHClient.__init__(self)
        
        
    def connect(self, hostname, port=22, username=None, password=None, pkey=None, 
                  key_filename=None, timeout=None, allow_agent=True, look_for_keys=True, 
                  compress=False):
        return super(self.__class__,self).connect(hostname=hostname,port=port,username=username,password=password,pkey=pkey, 
                  key_filename=key_filename, timeout=timeout, allow_agent=allow_agent, look_for_keys=look_for_keys, 
                  compress=compress)
    '''          
    '''
    SCP PUT file to remote location
    @param local_filename source path and file
    @param remote_filename destination path and file
    '''
    def set_ignore_missing_host_key_warning(self):
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    def get_script_path(self):
        return os.path.abspath(sys.argv[0])
    
    def open_scp(self,socket_timeout =None, progress = None):
        """
        Open SCP Connection
        progress = callback function (name,size,sent)
        socket_timeout = timeout float
        """
        t = self.get_transport()
        c = SCPClient(t,socket_timeout = socket_timeout, progress = progress)
        return c

    
    def scp_put(self,local_filename,remote_filename):
        t = self.get_transport()
        scp_channel = t.open_session()
        f = file(local_filename,'rb')
        scp_channel.exec_command('scp -v -t %s\n' % '/'.join(remote_filename.split('/')[:-1]))
        scp_channel.send('C%s %d %s\n' %(oct(os.stat(local_filename).st_mode)[-4:],os.stat(local_filename)[6],remote_filename.split('/')[-1]))
        scp_channel.sendall(f.read())
        f.close()
        scp_channel.close()
        return True
    
    '''
    @deprecated: 
    '''
    def scp_put_from_string(self,input,remote_filename):
        local_filename=self.get_script_path()       #dummy file for stat/file options
        t = self.get_transport()
        scp_channel = t.open_session()
        scp_channel.exec_command('scp -v -t %s\n' % '/'.join(remote_filename.split('/')[:-1]))
        scp_channel.send('C%s %d %s\n' %(oct(os.stat(local_filename).st_mode)[-4:],os.stat(local_filename)[6],remote_filename.split('/')[-1]))
        scp_channel.sendall(input)
        scp_channel.close()
        return True
    
    '''
    SCP GET file from remote location
    @param remote_filename source path and file
    @param local_filename destination path and file
    '''
    def scp_get(self,remote_filename="",local_filename=None):
        t = self.get_transport()
        #stdout = scp_channel.exec_command('cat %s\n' % remote_filename)
        stdin,stdout,stderr = self.exec_command("cat \"%s\""%remote_filename)
        data=stdout.read()    
        if local_filename==None:
            #no file output
            return data
        else:
            #output new file
            fh = open(local_filename, "wb")
            fh.write(data)
            fh.close()
        return True
    
    
    def exec_file(self,local_filename, remote_filename):
        self.scp_put(local_filename,remote_filename)
        self.exec_command("chmod 755 \"%s\""%remote_filename)       #chmod it :)
        return self.exec_command("%s"%(remote_filename))
    
    def __process_script_file(self,filename):
        f=open(filename,'r')
        script=""
        for line in f:
            if not len(line)==0 and not line=='\n' and not line[0]=='#':        #leave out blank lines
                script = "%s%s"%(script,line)
        f.close()
        return script
        
    def exec_batch_from_file(self,filename):
        script=self.__process_script_file(filename)
        return self.exec_batch(script)        
    
    def exec_batch_from_file_native(self,filename):
        script=self.__process_script_file(filename)
        return self.exec_batch_native(script)
    
    def exec_batch(self,script):
        '''
            exec the lines in script and return output
            returns outputlines from stdout as string per line
        '''
        outputLines = self.exec_batch_native(script)
        resultstr=""
        for stdin,stdout,stderr in outputLines:    
            resultstr="%s\n%s"%(resultstr,stdout.readlines())
        return resultstr
    
    '''
        batch execute commands
        delim: \n   one command per line
        returns results in reverse order
    '''
    def exec_batch_native(self,script):
        results = []
        script=str(script)
        scriptline = str.split(script,"\n")
        for line in scriptline:
            (stdin,stdout,stderr) = self.exec_command(line)
            results.append((stdin,stdout,stderr))
            
        return results
    
    def exec_command_stdout(self,command,bufsize=-1,write_stdin=None):
        '''
        bufsize=0 ... fire and foget command,stdin not allowed
        '''
        if bufsize==0:
            chan = self._transport.open_session()
            chan.exec_command(command)
            return
        
        stdin,stdout,stderr = self.exec_command(command, bufsize)
        if write_stdin!=None:
            stdin.write(write_stdin)
            stdin.flush()
        
        return stdout.readlines()
        
    
    def exec_command_stdoutEX(self,command,bufsize=-1,write_stdin=None):
        '''
        bufsize=0 ... fire and forget command
        '''
        if bufsize==0:
            chan = self._transport.open_session()
            chan.exec_command(command)
            return
        
        stdin,stdout,stderr = self.exec_command(command, bufsize)
        if write_stdin!=None:
            stdin.write(write_stdin)
            stdin.flush()
            
        return ''.join(stdout.readlines())
    
        
    '''
    
    '''
    def selftest(self):
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        s = self.connect("10.0.66.64",username="root",password="a")
        stdin,stdout,stderr = self.exec_command("uptime")  
        print stdout.readlines()
        self.scp_put("log.txt","/tmp/log.txt")
        print self.scp_get("/tmp/log.txt","c:\\_tmp\\tst.txt")





if __name__=="__main__":
    numfile=0
    def progress( filename, size, sent):
        global numfile
        numfile+=1
        print numfile,filename
        
    sshc = QA_SSH()
    sshc.set_ignore_missing_host_key_warning()
    sshc.connect('10.17.72.2', username='root', password='a')
    #stdin,stdout,stderr = sshc.exec_command("uptime")  
    scp = sshc.open_scp(progress=progress)
    #scp.get("/etc/phion-*",".")
    scp.put("c:\\_tmp\\skipfish\\skipfish\\n*.png",remote_path="/var/tmp/",recursive=False,)
    #scp.put("c:\\_tmp\\skipfish\\skipfish\\",remote_path="/var/tmp/",recursive=False,)
    print numfile
    print "done"
