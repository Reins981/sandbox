#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab

import re

class Node:


    def __init__(self, key = None, data = None):

        self.key = key
        self.data = data
        self.left = None
        self.right = None



class BTree:

    def __init__(self):

        self.root = None
        self.root_visited = False
        self.tunnel_key = ""
        self.tunnel_key_list = []
        self.tunnel_list_index = 0
        self.node_list_ids = []
        self.delimiter_dict = {}


    def __contains_all__(self, key, pattern):


        return 0 not in [c in key for c in pattern]


    def __is_number__(self, s):

        try:

            float(s)

            return True

        except ValueError:

            return False
    

    def __count_number__(self, s):

        cnt = {}
        
        for c in s:

            cnt[c] = cnt.get(c,0)+1

        return len(cnt)

    def __strip_chars__(self, s, strip_element):

        for c in s:

            if self.__contains_all__(c ,strip_element):

                s = s.strip(strip_element)

        return s

    def __check_port__(self, s, return_port=False):

        port = ""

        for c in s[0:3]:

            port+=c

        if port == "500" or port == "691":

            if return_port:

                return port

            else:

                return True

        else:

            if return_port:

                return port

            else:
            
                return False 

    def __eliminate_front_whitespaces__(self, entry, begin = None):

        begin = begin or None

        if begin == None:
            
            return entry

        else:

            entry = entry[entry.index(begin)+1:].lstrip()

            return entry

    def __get_delimited_entries__(self, s, delimiter=None):


        if delimiter == None:

            print 'nothing to deliminate'
            return s

        else:

            try:

                tmpentryleft = s[:s.index('=')]

                print tmpentryleft


            except ValueError:

                if "FW2FW" or "IPSEC" in s:

                    s = self.__strip_chars__(s,'\t')
                    s = self.__strip_chars__(s,'\n')

                    if self.__contains_all__(s,'('):

                        s = s[0:s.index('(')-1]

                        self.delimiter_dict[s] = None

                    
                return self.delimiter_dict


            s = s[s.index(delimiter)+1:]

            for position,char in enumerate(s):

                if char == " ":
                    
                    tmpentryright = s[:position]

                    self.delimiter_dict[tmpentryleft] = tmpentryright

                    return self.__get_delimited_entries__(s[position+1:], delimiter='=')

            tmpentryright = s
            self.delimiter_dict[tmpentryleft] = tmpentryright
            return self.delimiter_dict


    def __append_key__(self, tunnel_keylist, key, id_data):


        if ((not self.__contains_all__(key, "FW2FW")) and (key != "id")):

            return key + "->" + tunnel_keylist[self.tunnel_list_index-1] + ":" + id_data

        elif ((self.__contains_all__(key, "FW2FW")) and (key != "id")):
        
            return key + ":" + id_data

        
        elif ((not self.__contains_all__(key, "FW2FW")) and (key == "id")):

            return key

    def __add__(self, key, data):


        if self.root == None:

            self.root = Node(key, data)
            self.node_list_ids.append(self.root)

        else:

            currentnode = self.root
            lastvistitednode = self.root

            while currentnode != None:

        
                lastvisitednode = currentnode

                if self.__contains_all__(key, "FW2FW"):

                    self.tunnel_key = key
                    self.tunnel_key_list.append(self.tunnel_key)
                    self.tunnel_list_index += 1


                    

                if key == currentnode.key:
                    """key already exists"""
                
                    pass

                elif key < currentnode.key:

                    currentnode = currentnode.left
                    direction = -1


                else:

                    currentnode = currentnode.right
                    direction = +1
                

            if direction == -1:

                if self.tunnel_key == key:
                    self.node_list_ids[-1].key = self.node_list_ids[-1].key + "->" + self.tunnel_key_list[self.tunnel_list_index-1]

                lastvisitednode.left = Node(self.__append_key__(self.tunnel_key_list, key, self.node_list_ids[-1].data), data)
                
                if lastvisitednode.left.key == "id":
                    self.node_list_ids.append(lastvisitednode.left)


            else:
                
                if self.tunnel_key == key:
                    
                    self.node_list_ids[-1].key = self.node_list_ids[-1].key + "->" + self.tunnel_key_list[self.tunnel_list_index-1] 
                
                lastvisitednode.right = Node(self.__append_key__(self.tunnel_key_list, key, self.node_list_ids[-1].data), data)

                
                if lastvisitednode.right.key == "id":
                    self.node_list_ids.append(lastvisitednode.right)



    def __setitem__(self, key, data):
        
        self.__add__(key, data)

    def get_root_key(self):
        
        return self.root.key

    def get_root_data(self):
    
        return self.root.data

    def get_root_node(self):

        return self.root

    def pr_tree(self, node):

        if node != None:

            return "(left child %s---, ---%s=%s---, ---right child %s---)" % (self.pr_tree(node.left), node.key, node.data, self.pr_tree(node.right)) 

        else:
            return

    def get_node_data(self, key, node, data = None):


        if node == None:

            return None

        if ((key == node.key) and (data == None)):

            return node.data

        elif ((key == node.key) and (data != None)):

            if data == node.data:

                return node.data


        elif (key < node.key) and (data == None):

            return self.get_node_data(key, node.left)

        else:
            return self.get_node_data(key, node.right)



    def get_node_key(self, key, node):


        if node == None:            

            return None


        if key == node.key:

            return node.key

        elif key < node.key:

            return self.get_node_key(key, node.left)

        else:

            return self.get_node_key(key, node.right)


    def get_vpn_status_codex(self, treelist, searchstring):

        for index, item in enumerate(treelist):


            data = item.get_node_data(searchstring,item.get_root_node())

            if (index == len(treelist)-1) and (data == None):

                raise AttributeError, "data not found"      

            if data != None:
            
                return data

    def add_tree_structure(self, unsorted_list):

        final_dict = {}

        if len(unsorted_list) == 0:

            print 'nothing to add'
            return 1

        else:

            for entry in unsorted_list:



                if self.__contains_all__(entry,':'):
                    
                    singleitem = entry[entry.index(':')-1:entry.index(':')]

                    
                    if self.__is_number__(singleitem):

                        countentry = entry[0:entry.index(':')]
                        checkentry = entry[entry.index(':')+1:]

                        if self.__count_number__(countentry) ==1:

                            entry = self.__eliminate_front_whitespaces__(entry,begin=':')

                            if self.__contains_all__(entry,'='):

                                tmpdict = self.__get_delimited_entries__(entry,delimiter='=')                           
                                final_dict.update(tmpdict)

                        else:

                            if self.__check_port__(checkentry):

                                countentry = self.__strip_chars__(countentry,'\t')
                                countentry = self.__strip_chars__(countentry,'\n')

                                final_dict["localip"] = countentry

                                countentry = entry[entry.index('->')+3:]
                                countentry = countentry[:countentry.index(self.__check_port__(checkentry,return_port=True))]
                                countentry = self.__strip_chars__(countentry,'\t')
                                countentry = self.__strip_chars__(countentry,'\n')

                                final_dict["remoteip"] = countentry

                            else:

                                
                                entry = self.__eliminate_front_whitespaces__(entry,begin=':')


                                if self.__contains_all__(entry,'='):

                                    tmpdict = self.__get_delimited_entries__(entry,delimiter='=')                           
                                    final_dict.update(tmpdict)

                else:

                    if self.__contains_all__(entry,'='):
    
                        entry = self.__strip_chars__(entry,'\t')
                        entry = self.__strip_chars__(entry,'\n')

                        tmpdict = self.__get_delimited_entries__(entry,delimiter='=')                                       

        print final_dict

if __name__=="__main__":

    unsortedlist = []
    unsortedlist.append('0: id=0 IPSEC-hub2bigipsec-12.1.0.0-12.0.9.0 (11295 mins)\n')
    unsortedlist.append('\t10.10.0.1:500 -> 10.10.0.2:500 \n')
    unsortedlist.append('\tcipher=aes hash=md5 compress=(0) hc=0\n')
    unsortedlist.append('\tstatus=1 onDemand=0 bandPolicy=0 tosPolicy=256 Replay Window Size=32\n')
    unsortedlist.append('\tno-wanopt-rule type=4 \n')
    unsortedlist.append('\tin=0 KB, 0 KB (0%) out= 0 KB 0 KB (0%)\n')
    '''unsortedlist.append('\tInbound SPI: (11017)\n')'''
    unsortedlist.append('\t11017:  inbound addr=10.10.0.2 spinum=97f1518e timer=0 IPSEC-hub2bigipsec-12.1.0.0-12.0.9.0\n')
    '''unsortedlist.append('\t\t(16 mins)\n')
    unsortedlist.append('\t\tKey(16)=fdbec92c8f92e65d21cfac445eed7499\n')
    unsortedlist.append('\t\tHash(16)=5b8d448bbb00da9cbf3407123668a38f\n')
    unsortedlist.append('\t\tbytes=0 KB, 0 KB Pkts\n')
    unsortedlist.append('\tOutbound SPI: (11018)\n')
    unsortedlist.append('\t11018: outbound addr=10.10.0.1 spinum=d446108c timer=0 IPSEC-hub2bigipsec-12.1.0.0-12.0.9.0\n')
    unsortedlist.append('\t\t(16 mins)\n')
    unsortedlist.append('\t\tKey(16)=9eedbcec2325100e55bfa02f5b68e97c\n')
    unsortedlist.append('\t\tHash(16)=f69bd02de0bb7eeea8a3b3cf17f33c88\n')
    unsortedlist.append('\t\tbytes=0 KB, 0 KB Pkts\n')
    unsortedlist.append('actual usage: 1\n')
    unsortedlist.append('---------------------------------\n')


    
    unsortedlist.append('43: id=0 FW2FW-hub2small (4069 mins)\n')
    unsortedlist.append('\t10.10.0.1:691 -> 10.10.0.3:691 \n')
    unsortedlist.append('\tcipher=cast hash=sha compress=(0) hc=0\n')
    unsortedlist.append('\tstatus=1 onDemand=0 bandPolicy=129 tosPolicy=256 Replay Window Size=1024\n')
    unsortedlist.append('\tno-wanopt-rule type=2 \n')
    unsortedlist.append('\tin=0 KB, 0 KB (0%) out= 0 KB 0 KB (0%)\n')
    unsortedlist.append('\tInbound SPI: (11042)\n')
    unsortedlist.append('\t11042:  inbound addr=10.10.0.3 spinum=65098140 timer=0 FW2FW-hub2small\n')
    unsortedlist.append('\t\t(5 mins)\n')
    unsortedlist.append('\t\tKey(16)=942eb541765005298f91f8e1fb93b84a\n')
    unsortedlist.append('\t\tHash(20)=34ef364d69768d8039a851951d50d5b17e8af2f4\n')
    unsortedlist.append('\t\tbytes=0 KB, 0 KB Pkts\n')
    unsortedlist.append('\tOutbound SPI: (11041)\n')
    unsortedlist.append('\t11041: outbound addr=10.10.0.1 spinum=3328554a timer=0 FW2FW-hub2small\n')
    unsortedlist.append('\t\t(5 mins)\n')
    unsortedlist.append('\t\tKey(16)=9c8a1dc0ed21caf0e9d4b7067cc1b386\n')
    unsortedlist.append('\t\tHash(20)=6c80cbc24dff085cbb7eb4253e646fdaee8d9adb\n')
    unsortedlist.append('\t\tbytes=0 KB, 0 KB Pkts\n')
    unsortedlist.append('actual usage: 1\n')
    unsortedlist.append('---------------------------------\n')
    unsortedlist.append('orphaned transport count: 0\n')'''
    
    



    tree_initial = BTree()

    tree_initial.add_tree_structure(unsortedlist)


    treelist = []   

    tree0 = BTree()

    tree1 = BTree()
    tree1["id"] = "0"
    tree1["FW2FW-mailtraffic"] = None
    tree1["cipher"] = "aes"
    tree1["id"] = "1"
    tree1["FW2FW-BOH"] = None
    tree1["cipher"] = "blowfish"
    treelist.append(tree1)
    tree2 = BTree()
    tree2["id"] = "2"
    tree2["FW2FW-test1"] = None
    tree2["cipher"] = "cast"
    treelist.append(tree2)
    tree3 = BTree()
    tree3["id"] = "0"
    tree3["FW2FW-test2"] = None
    tree3["cipher"] = "blowfish"
    tree3["hash"] = "md5"
    tree3["Hash"] = "1x98767"
    tree3["Key"] = "c193445"
    tree3["in"] = "10 KB"
    tree3["out"] = "20 KB"
    treelist.append(tree3)
    

    print tree3.pr_tree(tree3.get_root_node())

    print "----------------------------------------------------------------------"
    
    try:

        print tree0.get_vpn_status_codex(treelist,"hash->FW2FW-test2:0")

    except:

        print "data not found"

    print "----------------------------------------------------------------------"

    print tree3.get_node_key("Hash->FW2FW-test2:4", tree3.get_root_node())



