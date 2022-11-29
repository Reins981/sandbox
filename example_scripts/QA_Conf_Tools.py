#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
# -*- coding: utf-8 -*-
'''
Created on 13.09.2012
@author: rkoraschnigg
''' 
import operator

class Bnf_Db():

    def __init__(self):

        self.database_elem_last = None
        self.database_final_elem_list = []
        self.database_initial_list_elem = True
        self.database_start_counter = True
        self.database_counter_list = []
        self.database_duplicate_counter = 0
        self.database_return_list = False
        self.database_unsorted_dict = {}
        self.database_root = {}
        self.database_indices_list = []
        self.database_overload = False
        self.initial = True
        self.desired_length = 0


    def __list_elem__(self,elem=""):

        position = 0

        if elem == None:

            return position

        for position,char in enumerate(elem):

            if char == '[':
                
                return position

        position = 0
        
        return position

    def __elem_index__(self,elem=""):

        return elem[elem.index('[')+1:elem.index(']')]   

    def __set_unsorted_elem_dict__(self,key,value): 

       self.database_unsorted_dict[key] = value

    def __get_unsorted_elem_dict__(self):

        return self.database_unsorted_dict

    def __sort_elem_dict__(self,unsorted_elem_dict): 

        unsorted_dict = {}
        sorted_elem_dict = {}

        for key,value in unsorted_elem_dict.iteritems():
            unsorted_dict[int(key)] = value[0].strip()

        sorted_elem_dict = unsorted_dict

        for key,value in sorted_elem_dict.iteritems():

            self.database_final_elem_list.append(value)
        
        return self.database_final_elem_list

    def __clear_final_elem_list(self):

        self.database_final_elem_list = []

    def __get_database_max_indices__(self,data,element_list):

        counter = 0
        databasename = ""
        element_list_index = 0

        elms=data.split("|")

        for item in range(len(elms)):

            elms[item].strip()

            for position,char in enumerate(elms[item]):

                if char == '[':

                    databasename = elms[item][0:position].strip()

                    counter = elms[item][position+1:elms[item].index(']')]

                    if self.database_start_counter:

                        self.database_counter_list.append(int(counter))

                        self.database_elem_last = databasename

                        element_list.append((databasename,self.database_counter_list[-1]))

                        self.database_start_counter = False

                    elif self.__is_duplicate_list_elem(databasename):


                        self.database_counter_list.append(int(counter))

                        self.database_counter_list.sort()

                        element_list[-1] = (databasename,self.database_counter_list[-1])

                    else:

                        self.database_counter_list = []

                        self.database_counter_list.append(int(counter))
                        
                        element_list_index += 1
                        
                        element_list.append((databasename,self.database_counter_list[-1]))


        return element_list



    def __create_list_elem__(self,elem="",position=0):

        return elem[0:position]

    def __is_duplicate_list_elem(self,elem_next=""):

        if elem_next == self.database_elem_last:
            return True

        else:
            self.database_elem_last = elem_next
        
            return False

    def __check_entry_max_index__(self,indices_list,top_element):

        return [x[0] for x in indices_list].index(top_element)    
        

    def __rekr_parse__(self,root,data,indices_list):

        duplicate = False

        index = 0

        elms=data.split("|")


        if elms[0] == '':

            del elms[0]

        if self.initial:

            if len(elms) > 6:
                
                self.desired_length = len(elms)-3

                self.database_overload = True
                
                self.initial = False

        top_elem=str(elms[0]).strip()   # global

        if len(top_elem) == 0:
    
            top_elem = None

        #print "-",elms,len(elms)

        position = self.__list_elem__(top_elem)


        if position:

            index = self.__elem_index__(top_elem)
        
            top_elem = self.__create_list_elem__(top_elem,position)

            if self.__is_duplicate_list_elem(top_elem):

                duplicate = True

                self.database_initial_list_elem = False

                self.database_duplicate_counter += 1


        if position and self.database_initial_list_elem:

            self.__clear_final_elem_list()

            if self.database_indices_list[self.__check_entry_max_index__(self.database_indices_list,top_elem)][1] == self.database_duplicate_counter:

                if self.database_overload:

                    self.database_final_elem_list.append(elms[1:])

                    self.database_initial_list_elem = True

                    self.database_duplicate_counter = 0

                    self.database_return_list = True


                else:

                    self.database_final_elem_list.append(tuple(elms[1:]))

                    self.database_initial_list_elem = True

                    self.database_duplicate_counter = 0

                    self.database_return_list = True
                

            else:
               
                if self.database_overload:

                    self.__set_unsorted_elem_dict__(index,elms[1:])

                else:
 
                    self.__set_unsorted_elem_dict__(index,tuple(elms[1:]))



        elif position and duplicate:


            if self.database_indices_list[self.__check_entry_max_index__(self.database_indices_list,top_elem)][1] == self.database_duplicate_counter:


                if self.database_overload:

                    self.__set_unsorted_elem_dict__(index,elms[1:])

                    self.__sort_elem_dict__(self.__get_unsorted_elem_dict__())

                    self.database_initial_list_elem = True

                    self.database_duplicate_counter = 0

                    self.database_return_list = True


                else:

                    self.__set_unsorted_elem_dict__(index,tuple(elms[1:]))

                    self.__sort_elem_dict__(self.__get_unsorted_elem_dict__())

                    self.database_initial_list_elem = True

                    self.database_duplicate_counter = 0
                
                    self.database_return_list = True

            else:

                if self.database_overload:

                    self.__set_unsorted_elem_dict__(index,elms[1:])

                else:

                    self.__set_unsorted_elem_dict__(index,tuple(elms[1:]))

        if self.database_overload: 

            if not self.database_return_list and self.desired_length == len(elms):

                self.__set_unsorted_elem_dict__(index,elms[0:])

                self.__sort_elem_dict__(self.__get_unsorted_elem_dict__())

                self.database_overload = False

                self.initial = True

                return self.database_final_elem_list

            elif self.database_return_list and self.desired_length == len(elms):


                self.database_return_list = False

                self.database_overload = False

                self.initial = True
                
                return self.database_final_elem_list

        else:

            if not self.database_return_list and len(elms) ==3: 
       
                self.initial = True
                
                return tuple(elms[0:2])          #tuple = ( a,b,c,..) ... liste= [1,2,3,4]

            elif self.database_return_list and len(elms) ==3:

                self.initial = True
                
                self.database_return_list = False            

                return self.database_final_elem_list
        # use elms[0] = top elem = current
        # rekr pass rest to myself

        if not top_elem in root:
        
            root[top_elem] = {}

        root[top_elem] = self.__rekr_parse__(root[top_elem],"|".join(elms[1:]),self.database_indices_list) #pass other elems to myself

        # behandel, top elems
        #root [top_elem]=retn

        self.__clear_final_elem_list()

        return root


    def format_database(self,databaselist):

        for item in range(len(databaselist)):

            self.__get_database_max_indices__(databaselist[item],self.database_indices_list)

        self.database_elem_last = None

        for item in range(len(databaselist)):

            self.__rekr_parse__(self.database_root,databaselist[item],self.database_indices_list)

        return self.database_root
    

if __name__ == "__main__":

    repo = Bnf_Db()

    root = {}

    mylist1 = ['| global |  | fw_net_obj_exc_members[0] | exc^10.0.0.0/8||,exc^172.16.0.0/12||,exc^192.168.0.0/16|| | 0 |','| global |  | fw_net_obj_exc_members[1] | exc^11.0.0.0/8||,exc^173.16.0.0/12||,exc^193.168.0.0/16|| | 0 |']

    mylist5 = ['| global |  | fw_net_obj_exc_members | exc^10.0.0.0/8||,exc^172.16.0.0/12||,exc^192.168.0.0/16|| | 0 |','| global |  | fw_net_test | exc^11.0.0.0/8||,exc^173.16.0.0/12||,exc^193.168.0.0/16|| | 0 |']

    mylist2 = ['| global |  | fw_net_obj_exc_members[0] | DO_NAT | 0 |','| global |  | fw_net_obj_exc_members[1] | NO_NAT | 0 |']

    mylist3 = ['| global |  | fw_net_obj_exc_members[0] | exc^10.0.0.0/8||,exc^172.16.0.0/12||,exc^192.168.0.0/16|| | 0 |']

    mylist4 = ['| global |  | fw_access_rule_sel_apps[0] | 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255 | 0 |']

    mylist5 = ['| global |  | fw_access_rule_name[0] | VPNCLIENTS-2-LAN | 0 |','| global |  | fw_access_rule_name[10] | BLOCKALL | 0 |','| global |  | fw_access_rule_name[1] | P1-P3-BRIDGE | 0 |','| global |  | fw_access_rule_name[2] | LAN-2-BARRACUDA-SERVERS | 0 |','| global |  | fw_access_rule_name[3] | TRANSPARENT-PROXY | 0 |','| global |  | fw_access_rule_name[4] | LOCALDNSCACHE | 0 |','| global |  | fw_access_rule_name[5] | LAN-2-INTERNET-SIP | 0 |','| global |  | fw_access_rule_name[6] | INTERNET-2-LAN-SIP | 0 |','| global |  | fw_access_rule_name[7] | LAN-2-INTERNET | 0 |','| global |  | fw_access_rule_name[8] | LAN-2-LAN | 0 |','| global |  | fw_access_rule_name[9] | KNIGHT-RIDER| 0 |']

    root = repo.format_database(mylist5)
    print root


