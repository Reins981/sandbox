
'''
Created on Mar 6, 2012

@author: mortner
'''
import sys,time
sys.path.append('pyAPI.zip')      #add API-ref for modules & co
from modules.QA_Logger import QA_Logger

LOG = QA_Logger(name='Machinery', loglevel=QA_Logger.L_INFO)

class SMStateWrapper():
    '''
    state wrapper for common params, vars etc
    '''
    


class QA_Machinery():
    states = []
    current_state=None
    history = []
    
    def add(self,strName,oState,transitions):
        self.states.append(tuple([strName,oState,transitions]))       
        return 

    def getTransition(self):
        transitions = {}
        
        for s in self.states:
            strName,oState,transitions = s
            if isinstance(self.current_state,str):
                if strName==self.current_state: break 
            else:
                if oState==self.current_state: break

                    
        #transitions is set match it now
        return transitions

    def getStateByName(self,name):
        if not name: return None
        if not isinstance(name,str): return name    #this is a state object?
        
        for strName,oState,transitions in self.states:
            if name==strName: return oState
        return None
    
    def getStateName(self,instance):
        for strName,oState,transitions in self.states:
            if instance==oState: return strName
        return None
    
    def getHistory(self):
        return self.history
        

    def next(self):
        if not self.current_state: return None
        
        LOG.debug( self.getStateName(self.current_state))
        res = self.current_state.run()
                
        if self.getTransition().has_key(res):
            nextstate= self.getTransition()[res]
            self.history.append(self.current_state)
            self.current_state=self.getStateByName(nextstate)
            return True
        
        return False
    
    def run(self,baseState=None,sleep=0):
        #run until no next or error
        self.current_state = self.getStateByName(baseState) or self.states[0][1]    #get frst state object
        LOG.debug("--- START")
        while self.next(): time.sleep(sleep)
        LOG.debug("--- END")
            
