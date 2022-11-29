'''
Created on 19.10.2011

@author: mortner

    Methods that allow to delegate an array of TASKS to multiple CPUs

    - sample usage: 
    
        def deploy_and_run(self,BOX,Script):
            ssh = QA_SSH()
            ssh.set_ignore_missing_host_key_warning()
            ssh.connect(BOX[0],username=BOX[1],password=BOX[2])
            output = ssh.exec_batch(Script)
            del ssh
            return output

        SCRIPT = "uptime"


        BOXES = [
                 ('10.5.6.51','root','ngf1r3wall')
                 ('10.5.6.51','root','ngf1r3wall')
                ]

        TASKS = [
                 (deploy_and_run, (box, SCRIPT)) for box in BOXES
                ]
    
    
    QA_Multiprocessing_run(TASKS)
'''
from modules.QA_Logger import QA_Logger
import multiprocessing
LOG = QA_Logger(name='MP', loglevel=QA_Logger.L_DEBUG)
    #
    # Functions used by test code
    #
    
def __dummy_func(func, args):
    '''
    PRIVATE function
    '''
    result = func(*args)
    return '[%s] processing %s%s = %s' % (
        multiprocessing.current_process().name,
        func.__name__, args, result
        )
    
def QA_Multiprocessing_LOG(QA_Logger_Instance=None,loglevel=0,msg=None):
    if not QA_Logger_Instance==None:
        LOG.log(loglevel,msg)
    return
    


def QA_Multiprocessing_run(TASKS,PROCESSES=4,QA_Logger_Instance=None):
    '''
    @param TASKS: List of TaskTuples (function,(params)) | PROCESSES: Number of Processes
    @return: Errorcode
    '''
    QA_Multiprocessing_LOG(QA_Logger_Instance,10,'cpu_count() = %d\n' % multiprocessing.cpu_count())

    #
    # Create pool
    #

    PROCESSES = PROCESSES
    QA_Multiprocessing_LOG(QA_Logger_Instance,10,'Creating pool with %d processes\n' % PROCESSES)
    pool = multiprocessing.Pool(PROCESSES)
    #print 'pool = %s' % pool
    

    #
    # Tests
    #

    results = [pool.apply_async(__dummy_func, t) for t in TASKS]
    #imap_it = pool.imap(dummy_func, TASKS)
    #imap_unordered_it = pool.imap_unordered(dummy_func, TASKS)

    QA_Multiprocessing_LOG(QA_Logger_Instance,10,'Ordered results using pool.apply_async():')
    lstOutputlines=[]
    for r in results:
        QA_Multiprocessing_LOG(QA_Logger_Instance,10,'\t%s'%(r.get()))          
        lstOutputlines.append(r.get())
    print

    #
    # Check there are no outstanding tasks
    #

    assert not pool._cache, 'cache = %r' % pool._cache

    return lstOutputlines


###########################################################
        
    


