#!/usr/bin/env python

# http ipv4 and ipv6 requests with urllib2

import sys
sys.path.append('pyAPI.zip')
import socket
import time
import datetime
import os
import struct
import errno
import threading
from threading import Condition, currentThread
from scapy.all import *
import errno
from urllib2 import Request, urlopen, URLError, HTTPError
from modules.QA_NGFW import QA_NGFW

class StoppableThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()


    def stop(self):

        if self.isAlive():
            print 'sending event to thread %s' % (currentThread())
            # set event to signal thread to terminate
            self.stop_event.set()
            # block calling thread until thread really has terminated

            print 'finally joining thread %s' % (currentThread())                

            try:
                self.join()

            except RuntimeError:
                print '%s already terminated' % (currentThread())

    def stop_specific(self):
        
        if self.isAlive():
            print "terminating thread %s" % (currentThread())
            try:
                self.join()

            except RuntimeError:
                print '%s already terminated' % (currentThread())



class StoppAll(StoppableThread):

    def __init__(self, threads):
        StoppableThread.__init__(self)
        self.threads = threads

    def stop_threads(self, All=False, ThreadId=1):
        
        if All:
            
            for listen_thread in self.threads:
                print "terminating %s ..." % (listen_thread)
                listen_thread.join()
            self.threads = []
        
        else:
            
            for k, v in self.th.getThreadDict().iteritems():
                if k == ThreadId:
                    print "terminating %s..." % (v)
                    v.stop_specific()
            print "removing thread %s out of dictionary" % (v)
            self.th.getThreadDict().pop(k)


class itemQMedia():

    def __init__(self):
        self.Mcount = 0

    def produce(self, Mnum):
        self.Mnum = Mnum
        self.Mcount += Mnum

    def consume(self):
        if self.Mcount: self.Mcount -= 1

    def isEmpty(self):
        return not self.Mcount


    def num(self):
        return self.Mcount


class TerminateCondition():

    def __init__(self):
        self.TCondition = False

    def setTerminateCondition(self,TCondition):
        self.TCondition = TCondition


    def getTerminateCondition(self):
        return self.TCondition


class ThreadDict():

    def __init__(self):
        self.threaddict = {}
        self.threadid = 1

    def addThread(self, threadid, threadname):
        self.threaddict[threadid] = threadname

    def getThreadDict(self):
        return self.threaddict

    def setThreadId(self, threadid):
        self.threadid = threadid
    
    def getThreadId(self):
        return self.threadid   

 
class Evaluate():

    def __init__(self):
        self.eval = False
        self.fincount = 0

    def set_eval(self, eval):
        self.eval = eval

    def get_eval(self):
        return self.eval

    def set_fin_count(self, fincount=1):
        self.fincount = self.fincount + fincount

    def get_fin_count(self):
        return self.fincount

    def reset_fin_count(self):
        self.fincount = 0



class Generic_Thread(StoppableThread):

    def __init__(self, cond=None,result=None,tc=None, itemq=None, PACKETS=[]):
        StoppableThread.__init__(self)

        self.cond = cond
        self.result = result
        self.tc = tc
        self.itemq = itemq
        self.sleeptime = 2
        self.data = ""
        self.datastring = ""
        self.TCondition = True
        self.eval = False

        self.PACKETS = PACKETS

        self.TASKS = [
                (self.send_scapy, (packet,)) for packet in self.PACKETS
                ]
        

    def run(self):

        while not self.stop_event.isSet():

            
            print 'Starting Generic_Thread %s' % (currentThread())
       
            for f,args in self.TASKS:
                
                self.__dummy_func(f,args)


    def send_scapy(self, packet):


            try:

                send(packet)

            except Error, e:
                print 'request error'
                print "Error code:", e.code
                self.result.set_eval(self.eval)

            else:
                print 'Request was OK'
                print '%s send data successfully' % (currentThread())
                self.eval = True
                self.result.set_eval(self.eval)

            print '%s finished work' % (currentThread())
            self.tc.setTerminateCondition(self.TCondition)
            self.result.set_fin_count()
            self.stop()

            return self.result.get_eval()

    def __dummy_func(self, func, args):

        func(*args)

    #def __set_Tasks(self, TASKS):

        #self.TASKS = TASKS

    #def __get_Tasks(self):

        #return self.TASKS

    
    def initiate_threads(self,numrun=1,numthread=1,sendlist=[]):


        self.PACKETS = sendlist
        testrun = 1
        counter=0

        threads = []
        tc = TerminateCondition()
        cond = Condition(threading.Lock())
        itemq = itemQMedia()
        st = StoppableThread()
        sa = StoppAll(threads)
        result = Evaluate()
        th = ThreadDict() 
        TCondition = True
        ThreadChild = ""
        ThreadId = 1
        do_exit = False

        for i in self.PACKETS:
            counter+=1

        fin_counter = counter * numthread


        while do_exit == False:

            try:

                time.sleep(1)

            except KeyboardInterrupt:

                do_exit = True
                print '^C received, shutting down all running threads...'

            for i in xrange(1,numrun+1):
                
                #according to hasync, let the sessions time out after the clients finished sending
                #time.sleep(3)
                print 'starting test run number %s' %(testrun)

                for x in range(numthread):
                    ThreadChild = "ThreadChild" + str(ThreadId)
                    generic_thread = Generic_Thread(cond,result,tc, itemq, self.PACKETS)
                    th.addThread(ThreadId, ThreadChild)
                    threads.append(ThreadChild)
                    generic_thread.start()


                while result.get_fin_count() < fin_counter:
                    
                    time.sleep(1) 
                

                if result.get_eval():

                    print 'Test OK'
                    testrun = testrun+1

                else:

                    print 'Test failed'
                    tc.setTerminateCondition(TCondition)
                    do_exit = True
                    return 1

                result.reset_fin_count()            

            return 0
        st.stop_event.set()
        sa.stop_threads(All=True)

