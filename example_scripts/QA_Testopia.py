#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
'''
Created on Jul 27, 2012

@author: mortner
'''
from modules.ext.testopia_27 import Testopia
import datetime
from modules.QA_MethodDeco import method_decorator
from modules.QA_Logger import QA_Logger
LOG = QA_Logger(name='testopia', loglevel=QA_Logger.L_WARNING)



class CHECK_STATE(method_decorator):
    def __call__(self, *args, **kwargs):
        if not self.obj.testrun_status==self.obj.STATUS['RUNNING']:
            LOG.warning("STATE=%s, need STATE=RUNNING!! - resume test or create new testrun"%self.obj.testrun_status)
            return
        return method_decorator.__call__( self, *args, **kwargs )



class QA_Testopia(object):
    '''
        1) connect to testopia server
        2) getTestrun(plan_id ...) if you want to create or use an existing testrun (created by this testopia instance)
        2.1) getTestrun returns a Testrun class, use this class to set the status of individual testopia case ids (not run ids)
        
        * note: you can use multiple testruns at the same time, they'll be handled by QA_Testopia
        ** note: EITHER supply a product_name (will be matched internally with ids from defaults __dict__) or go to testopia create the first run for the testplan and let the script do the rest
                 this is due to crap testopia bindings with missing functionality.. cannot search product_id, cannot create environment..
    
    '''   
    DEFAULTS = {
                #'host':'https://testopia.cudaops.com/bugzilla/tr_xmlrpc.cgi',
                'host':'https://testopia.englab.cudanet.local/bugzilla/tr_xmlrpc.cgi',
                }    
    
    t_conn=None            #testopia connection
    testruns={}                 # maps plan_id to run_id

    
    def __init__(self,product_name):
        self.product_name=product_name
        pass
    
    def __del__(self):
        pass
    
    def connect(self,host,username,password):
        host = host or self.DEFAULTS['host']
        LOG.debug("connecting ...")
        self.t_conn=None
        self.t_conn = Testopia(host,username, password )
        LOG.info("connection established: %s"%repr(self.t_conn))
        return self.t_conn
    
    def open(self,host,username,password):
        return self.connect(host, username, password)
    
    
    def getTestrun(self,plan_id,run_name,build_name=None,delimiter=None,postfix=None):
        '''
            if testrun does not exist it wil be autogenerated
        '''
        if not self.t_conn: 
            LOG.error("not connected!")
            raise
        
        tr_key="%s_%s_%s"%(plan_id,run_name,build_name)
        
        if self.testruns.has_key(tr_key):
            LOG.debug("testplan instance (run) already exists - using this one....")
            #check if testrun already stopped (testopia connection will be None'd if test requested to stop)
            if self.testruns[tr_key].t_conn==None and self.testruns[tr_key].testrun_status == Testrun.STATUS['STOPPED']: 
                self.testruns.pop(tr_key)
                tr = Testrun(self.t_conn,self.product_name)
                self.testruns[tr_key]=tr.createTestrun(plan_id=plan_id, run_name=run_name, build_name=build_name, delimiter=delimiter, postfix=postfix)
                
        else:
            LOG.debug("testplan instance does NOT exist - creating one....")
            tr = Testrun(self.t_conn,self.product_name)
            self.testruns[tr_key]=tr.createTestrun(plan_id=plan_id, run_name=run_name, build_name=build_name, delimiter=delimiter, postfix=postfix)
        
        return self.testruns[tr_key]       #plan is already initiated and ready to go
    
    
    

class Testrun(object):
       
    WEEKDAY = { 0:'Monday',
                1:'Tuesday',
                2:'Wednesday',
                3:'Thursday',
                4:'Friday',
                5:'Saturday',
                6:'Sunday',             
               }
    
    STATUS = { 'UNKNOWN':0,
               'IDLE'   :1,      #?    dont know
               'PASSED' :2,
               'FAILED' :3,
               'RUNNING':4,
               'PAUSED' :5,
               'BLOCKED':6, 
               'ERROR'  :7, 
               
               'STOPPED':999,       #indicate testrun stopped so that runmanager can remove it    
              }
    

    DEFAULTS = { 
                 'NG Firewall':         {
                                         'product_id':25,
                                         'environment_id':86
                                         },
                 'Network Firewall':     {
                                          'product_id':32,
                                          'environment_id':171,
                                          },                   
                }
    
    ENVIRONMENT={                           #project environment (gets filled upon testplan selection/testrun selection)
                 'product_id'       :25,
                 'environment_id'   :86,    #will be overridden on testplan init
                 'testruns'         :[],    # overwritten
                 
                             }
    t_conn=None                             #testopia connection
    t_conn_backup=None                      #backup for testrun status handling
    testrun_status = STATUS['PAUSED']      #initially set run status to running :)
    
    
    
    def __init__(self,t_conn,product_name=None):
        '''
            gimme testopia connection
            either supply product_name (will take defaults from within this class defaults config, or create a testrun for the given testplan and use it to autoget environment and product id
        '''
        self.t_conn = t_conn
        self.t_conn_backup = t_conn
        
        if product_name:
            self.ENVIRONMENT=self.DEFAULTS[product_name]
            self.ENVIRONMENT['testruns']=[]
        
        self.__set_testrun_state(self.STATUS['RUNNING'])
        pass
    
    def __del__(self):
        pass
    
    
    '''
    def connect(self,host,username,password):
        host = host or self.DEFAULTS['host']
        LOG.debug("connecting ...")
        self.t_conn=None
        self.t_conn = Testopia(host,username, password )
        LOG.info("connection established: %s"%repr(self.t_conn))
        return self.t_conn
    
    def open(self,host,username,password):
        return self.connect(host, username, password)
    '''
    
    def __setEnv(self,key,value=None):
        self.ENVIRONMENT[key]=value
        
    def __getEnv(self,key):
        if not self.ENVIRONMENT.has_key(key): return None
        return self.ENVIRONMENT[key]
    
    
    def findTestrun(self,plan_id,run_name,build_name=None,delimiter=None,postfix=None):
        '''
            leave postfix==None to have    name_WEEKDAY as runname
        '''
        #check if testplan exists, if so use it, if not create it
        LOG.debug('getting testruns of testplan:'+str(plan_id))
        testopia_runs = self.t_conn.testplan_get_test_runs(plan_id)             #get environment from planid
        
        #generate weekday testrun name
        #"automated testrun"
        postfix = postfix or self.WEEKDAY[datetime.datetime.now().weekday()]
        delimiter = delimiter or " "
        fullname=run_name+ delimiter+postfix        


        got_testrun=None

        for trun in testopia_runs:
            if trun['summary']==fullname:
                got_testrun=trun
                break
                        

        # store the results, parse environmentID and fill it
        self.__setEnv('testruns',got_testrun)
        self.__setEnv('testrun_fullname',fullname)

        
        if got_testrun:
            self.__setEnv('environment_id', got_testrun['environment_id'])
            self.__setEnv('plan_id',        got_testrun['plan_id'])
            self.__setEnv('manager_id',     got_testrun['manager_id'])
            self.__setEnv('build_id',       got_testrun['build_id'])                #use found build_id :)
            self.__setEnv('run_id',         got_testrun['run_id'])
        else:
            self.__setEnv('environment_id', testopia_runs[0]['environment_id'])
            self.__setEnv('plan_id',        testopia_runs[0]['plan_id'])
            self.__setEnv('manager_id',     testopia_runs[0]['manager_id'])

        
        if build_name: 
            #check if build_name exists (version)
            self.__setEnv('build_id',self.getBuildId(build_name,autocreate=False))  #use found build_id if build_name is not set
        
        return got_testrun  

    def createTestrun(self,plan_id,run_name,build_name=None,delimiter=None,postfix=None):
        
        got_testrun = self.findTestrun(plan_id, run_name=run_name, build_name=build_name,delimiter=delimiter, postfix=postfix)
        
        build_id=self.__getEnv('build_id')
        plan_id=self.__getEnv('plan_id')
        environment_id=self.__getEnv('environment_id')
        fullname=self.__getEnv('testrun_fullname')
        run_id=self.__getEnv('run_id')
                
        if not got_testrun:
            #creating new testrun of testplan
            LOG.debug('try to create new testrun')
            testopia_testrun = self.t_conn.testrun_create(build_id, environment_id, plan_id, fullname, self.t_conn.userId, 1,None, 'unspecified')
            LOG.debug('new run id is:'+str(testopia_testrun['run_id']))
            run_id = testopia_testrun['run_id']

            
            #get all cases of testplan
            LOG.debug('try to get cases of testplan'+str(plan_id))
            returnVal = self.t_conn.testplan_get_test_cases(plan_id)

            planCaseList = []
            for entry in returnVal:
                planCaseList.append(entry['case_id'])
    
            #adding cases to testrun
            for case_id in planCaseList:
                returnVal = self.t_conn.testcaserun_create(self.t_conn.userId, build_id, int(case_id),environment_id, run_id, None, None)
                case_run_id = returnVal['case_run_id']

            self.__setEnv('testruns', [testopia_testrun])
            self.__setEnv('run_id', run_id)

        else:
            #testrun exists
            LOG.debug("testrun exists")
            
            #migrate cases to testrun
            
            tempRunCaseList = []
            LOG.debug('getting testcases of testrun:'+str(run_id))
            tempRunCaseList = self.t_conn.testrun_get_test_case_runs(run_id)

            #check if all testcases of testplan at testrun, otherwise add cases to testrun
            #so first of all get testcases of testplan
            tempPlanCaseList = []
            LOG.debug('try to get cases of testplan'+str(plan_id))
            tempPlanCaseList = self.t_conn.testplan_get_test_cases(plan_id)


            #check if testplan case is in testrun
            tempAddCaseId = []
            found = 0
            for plancase in tempPlanCaseList:
                for runcase in tempRunCaseList:
                    if(plancase['case_id'] == runcase['case_id']):
                        found = 1

                if(found == 0):
                    tempAddCaseId.append(plancase['case_id'])
                else:
                    found = 0
            
            #add missing cases
            for case_id in tempAddCaseId:
                returnVal = self.t_conn.testcaserun_create(self.t_conn.userId, build_id, int(case_id),environment_id, run_id, None, None)
                case_run_id = returnVal['case_run_id']               
                
                LOG.debug('getting testcases of testrun:'+str(run_id))
                tempRunCaseList = self.t_conn.testrun_get_test_case_runs(run_id)


            LOG.debug('update now testcases of testrun:'+str(run_id))
            for entry in tempRunCaseList:
                if entry['case_run_status_id']!=self.STATUS['IDLE']:                #set status if its not already idle
                    self.IDLE( entry['case_id'], run_id, build_id, environment_id)
        
        LOG.info("TESTRUN prepared and ready for use")
        return self
    
    def getPlanCases(self,plan_id=None):
        plan_id=plan_id or self.__getEnv('plan_id')
        LOG.debug("getting cases for plan: %s"%plan_id)
        return self.t_conn.testplan_get_test_cases(plan_id)
    
    def getRunCases(self,run_id=None):
        run_id=run_id or self.__getEnv('run_id')
        LOG.debug("getting cases for run: %s"%run_id)
        return self.t_conn.testrun_get_test_case_runs(run_id)
    
    @CHECK_STATE
    def setCaseRunStatus(self,case_id,status,run_id=None,build_id=None,environment_id=None):
        if isinstance(status,str): status=int(self.STATUS[status])
        elif not isinstance(status,int): raise "invalid format - status %s"%repr(status)
        
        run_id=run_id or self.__getEnv('run_id')
        build_id=build_id or self.__getEnv('build_id')
        case_id=int(case_id)
        environment_id=environment_id or self.__getEnv('environment_id')
        LOG.debug("setting %s testcase: %s"%(repr(status),repr(case_id)))
        self.t_conn.testcaserun_update(run_id=run_id,
                                       case_id=case_id,
                                       build_id=build_id,
                                       environment_id=environment_id,
                                       new_build_id=None,
                                       new_environment_id=None,
                                       case_run_status_id=status,
                                       update_bugs=False,
                                       assignee=None,
                                       notes=None)
        return
    
    # high level functions for failing/passing tests
    def FAIL(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='FAILED',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return

    def PASS(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='PASSED',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return
    
    def RUN(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='RUNNING',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return
    
    def PAUSE(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='PAUSED',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return

    def BLOCK(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='BLOCKED',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return
    
    def ERROR(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='ERROR',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return
    
    def IDLE(self,case_id,run_id=None,build_id=None,environment_id=None):
        self.setCaseRunStatus(case_id=case_id,status='IDLE',run_id=run_id,build_id=build_id,environment_id=environment_id)
        return

    
    def getBuildId(self,build_name,product_id=None,testplan_id=None, autocreate=False):
        product_id = product_id or self.__getEnv('product_id')
        testplan_id = testplan_id or self.__getEnv('plan_id')
        
        LOG.debug("searching for build_id for given build_name")
        retnVal = self.t_conn.build_check_by_name(build_name,product_id)
        ## check retnVal and if len(retnVAl)<=0 create build id
        LOG.debug("build found: %s"%repr(retnVal))
        if not len(retnVal) and autocreate_build:
            LOG.debug("build_name is missing, creating it...")
            LOG.debug('try to add build '+build_name+' to testopia db')
            exit()
            returnVal = self.t_conn.build_create(build_name, product_id, None, None, True)
            LOG.debug('adding build '+build_name+' to testopia db was successful')
        
        build_id = retnVal['build_id']

        return build_id
    
    def testrun_resume(self):
        self.__set_testrun_state(self.STATUS['RUNNING'])
        LOG.info("Testrun (%s) requests RESUME (dont updated further cases) (user initiated)"%repr(self))
    
    def testrun_block(self):
        self.__set_testrun_state(self.STATUS['BLOCKED'])
        LOG.info("Testrun (%s) requests BLOCK (dont updated further cases) (user initiated)"%repr(self))
    
    def testrun_pause(self):
        self.__set_testrun_state(self.STATUS['PAUSED'])
        LOG.info("Testrun (%s) requests PAUSE (dont updated further cases, new testrun will be created) (user initiated)"%repr(self))

    def testrun_stop(self):
        self.__set_testrun_state(self.STATUS['STOPPED'])
        LOG.info("Testrun (%s) requests STOPP (dont updated further cases, new testrun will be created) (user initiated)"%repr(self))


    def __set_testrun_state(self,newState):
        # we are running, and want to block or stop
        LOG.debug("traversing state from %s to %s"%(self.testrun_status,newState))
        if self.testrun_status==self.STATUS['RUNNING']:
            if newState==self.STATUS['PAUSED']:
                self.t_conn_backup=self.t_conn          #backup connection :)
                self.t_conn=None
                self.testrun_status=newState
            if newState==self.STATUS['BLOCKED']:
                self.t_conn=None                        #dont backup anything we want this to throw exception whoohaa
                self.t_conn_backup=None
                self.testrun_status=newState
            if newState==self.STATUS['STOPPED']:
                self.t_conn=None                        #dont backup anything we want this to throw exception whoohaa
                self.t_conn_backup=None
                self.testrun_status=newState
        
        if self.testrun_status==self.STATUS['PAUSED']:
            if newState==self.STATUS['RUNNING']:
                self.t_conn=self.t_conn_backup          #restore connection :)
                self.testrun_status=newState
            if newState==self.STATUS['BLOCKED']:
                self.t_conn=None                        #dont backup anything we want this to throw exception whoohaa
                self.t_conn_backup=None
                self.testrun_status=newState 
        return


if __name__=="__main__":
    t = QA_Testopia(product_name="Network Firewall")
    t.connect(QA_Testopia.DEFAULTS['host'],
              username='automated_ngfw@barracuda.com',
              password='password',
              )
    
    
    tr= t.getTestrun(579, "SELENIUM automated testrun",build_name="5.4.0",delimiter=" - ")
    for i in tr.getRunCases(9793): print i
    #print tr.FAIL(64648)
    #print [x['case_id'] for x in t.getPlanCases()]
    #print [x['case_run_id'] for x in t.getRunCases()]
    #print t.getRunCases()

    