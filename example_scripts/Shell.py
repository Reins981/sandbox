#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 29.11.2018

@author: heju271036
'''

import paramiko
import socket
import time


class SshShell:
    _ssh_object = None
    _retries = 60
    _port = 22

    # SSH connection timeout in seconds
    ssh_timeout = 2
    
    def __init__(self, host="192.168.1.4", 
                        username="root", 
                        password="root", 
                        verbose=False):
        self.host = host
        self.username = username
        self.password = password
        self.verbose = verbose
        self.success = False
        self.reconnect_triggered = False
        # NEW SSh connection object
        if self._ssh_object is None:
            # paramiko ssh does not support host based authentication without a password
            if self.password is None:
                self._ssh_object = paramiko.Transport((self.host,self._port))
            else:
                self._ssh_object = paramiko.SSHClient()
                self._ssh_object.load_system_host_keys()
                self._ssh_object.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)

    def open(self, timeout=ssh_timeout):
        print(self.__class__.__name__ + " Connecting to " + self.host)
        if self.verbose:
            print(self.__class__.__name__ + " username: " + self.username)
            print(self.__class__.__name__ + " password: " + str(self.password))
            print(self.__class__.__name__ + " timeout: " + str(timeout))

        # in case of a reconnect create a new ssh object
        if self.reconnect_triggered and self._ssh_object is None:
            if self.password is None:    
                # paramiko ssh does not support host based authentication when no password is given
                self._ssh_object = paramiko.Transport((self.host,self._port))
            else:
                self._ssh_object = paramiko.SSHClient()
                self._ssh_object.load_system_host_keys()

        try:
            if self.password is not None:
                self._ssh_object.connect(hostname=self.host, 
                                            username=self.username, 
                                            password=self.password, 
                                            timeout=timeout)
            else:
                self._ssh_object.connect()
                self._ssh_object.auth_none(self.username)
            self.success = True
            print(self.__class__.__name__ + " Successfully connected to target IP: " + self.host)
            return True
        except socket.timeout as msg:
            print(self.__class__.__name__ + " Connection timeout")
            return False

    def close(self):
        if self.verbose:
            print(self.__class__.__name__ + " Disconnecting")

        if self._ssh_object is not None:
            self._ssh_object.close()
            self._ssh_object = None
            self.reconnect_triggered = False

    def reconnect(self):
        print(self.__class__.__name__ + " Start reconnect..")
        for i in range(self._retries):
            time.sleep(0.5)
            self.close()
            self.reconnect_triggered = True
            success = self.open()
            if not success:
                if self.verbose:
                    print(self.__class__.__name__ + " Target {0} is not reachable after {1} retries".format(self.host, str(i+1)))
                if i < self._retries-1:
                    if self.verbose:
                        print(self.__class__.__name__ + " Retrying to connect ...")
            else:
                print(self.__class__.__name__ + " Successfully reconnected to target IP: " + self.host + " after " + str(i+1) + ' retries.')
                return True

        print(self.__class__.__name__ + " Could not reconnect to target IP: " + self.host + " after " +str(i+1) + ' retries. Giving up.')
        return False

    def is_host_connected(self):
        return self.success and self._ssh_object is not None

    def run(self, cmd):
        if self.verbose:
            print(self.__class__.__name__ + " Running command: " + cmd)

        if self.password is None:
            cmd_channel = self._ssh_object.open_session()
            stdin, stdout, stderr = cmd_channel.exec_command(cmd)
        else:
            stdin, stdout, stderr = self._ssh_object.exec_command(cmd)

        # wait for cmd to finish and check exit status
        exit_status = stdout.channel.recv_exit_status()

        stdout_str = stdout.read()
        stderr_str = stderr.read()
        if self.password is None:
            cmd_channel.close()

        if self.verbose:
            print(self.__class__.__name__ + " status: ", exit_status)
            print(self.__class__.__name__ + " stdout: ", stdout_str)
            # print self.__class__.__name__ + " stderr: ", stderr_str # not very useful to print

        return exit_status, stdout_str, stderr_str

    def __del__(self):
        if self._ssh_object is not None:
            self.close()
