#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
import sys
import os
sys.path.append('pyAPI.zip')
from modules.QA_Aux import QA_StrGen
from modules import QA_Optparser
import time
from scapy.all import *

'''class DNSRR_Packet(Packet):

    name = "DNS Resource Record"
    show_indent = 0
    fields_desc = [ DNSStrField("id", "0"), DNSStrField("qr","1"), DNSStrField("aa","1"), DNSStrField("tc","0"), DNSStrField("rd","0"), DNSStrField("ra","1"), DNSStrField("z","0"), DNSRRCountField("qdcount", None, "qd"), DNSRRCountField("ancount",None, "an"), DNSRRCountField("nscount",None, "ns"), DNSRRCountField("arcount", None, "ar"), DNSQRField("qd", "qdcount"), DNSRRField("an", "ancount"), DNSRRField("ns", "nscount"), DNSRRField("ar","arcount",0)]'''

'''class DNSRR_Packet(Packet):

    name = "DNS Resource Record"
    show_indent = 0
    fields_desc = [ ShortField("id", 0), BitField("qr",0,1), BitField("aa",0,1), BitField("tc",0,1), BitField("rd",0,1), BitField("ra",0,1), BitField("z",0,1),DNSRRCountField("qdcount", None, "qd"), DNSRRCountField("ancount",None, "an"), DNSRRCountField("nscount",None, "ns"), DNSRRCountField("arcount", None, "ar"), DNSQRField("qd", "qdcount"), DNSRRField("an", "ancount"), DNSRRField("ns", "nscount"), DNSRRField("ar","arcount")]'''


'''class DNS_Packet(Packet):

    name = "DNS"
    show_indent = 0
    fields_desc = [ ShortField("id", 0), BitField("qr",0,1), BitField("aa",0,1), BitField("tc",0,1), BitField("rd",0,1), BitField("ra",0,1), BitField("z",0,1),DNSRRCountField("qdcount", None, "qd"),DNSQRField("qd", "qdcount")]'''


class DNSQR_Packet(Packet):

    name = "DNS Question Record"
    fields_desc =[ DNSStrField("qname", "ns1.target.ch"), ShortEnumField("qtype", 1, dnsqtypes), ShortEnumField("qclass", 1, dnsclasses)]


class DNS_Packet(Packet):

    name = "DNS"
    show_indent = 0
    fields_desc = [ ShortField("id", 0), BitField("qr",0,1), BitField("aa",0,1), BitField("tc",0,1), BitField("rd",0,1), BitField("ra",0,1), BitField("z",0,1),DNSRRCountField("qdcount", None, "qd"),DNSQRField("qd", "qdcount")]


class DNSRR_Packet(Packet):

    name = "DNS Resource Record"
    show_indent = 0
    fields_desc = [ DNSStrField("rrname", "ns1.target.ch"), ShortEnumField("type",1, dnstypes), ShortEnumField("rclass",1, dnsclasses), RDLenField("rdlen"), DNSStrField("rdata", "212.1.2.3")]


class DNSRR_Packet_RDLEN(Packet):

    name = "DNS Resource Record"
    show_indent = 0
    fields_desc = [ DNSStrField("rrname", "ns1.target.ch"), ShortEnumField("type",1, dnstypes), ShortEnumField("rclass",1, dnsclasses), RDLenField("rdlen"), DNSStrField("rdata", "212.1.2.3")]


class QA_DNS_BL(object):

    def __init__(self):

        self.dns_server = ""
        self.querystring = ""
        self.expectedcounter = ""
        self.namelist = []
        self.ruletype = ""
        self.pwdlen = 8
        self.howmany = 8
        self.charset = ""
        self.encoding = ""
        self.cset = ""
        self.str_list = []
        self.dns_server = '10.0.6.90'
        self.source = '10.17.68.17'
        self.sendlist = []
        self.id_to_name={0:4,1:1,2:RandInt(),3:100,4:-5}


    def bulk(self, pwdlen=8, howmany=1, charset='dictAll', encoding='utf_8', dns_server='10.0.6.90', source='10.17.68.17'):

        self.pwdlen = pwdlen
        self.howmany = howmany
        self.charset = charset
        self.encoding = encoding
        self.dns_server = dns_server
        self.source = source
        packetcounter = 0
        index = 0

        if self.charset == 'ascii':

            x = QA_StrGen()

            self.cset = x.gen_charset_ascii()

        elif self.charset == 'unicode':

            x = QA_StrGen()

            self.cset = x.gen_charset_unicode()


        elif self.charset == 'encoding':

            x = QA_StrGen()

            self.cset = x.gen_charset_encodings(str_encoding=self.encoding)


        elif self.charset == 'Fuzz':

            x = QA_StrGen()

            self.str_list = x.generate_bulk(pwdlen=self.pwdlen,howmany=self.howmany,charset = x.__lstFuzzer__())

        elif self.charset == 'dictAll':

        
            x = QA_StrGen()

            self.str_list = x.generate_bulk(pwdlen=self.pwdlen,howmany=self.howmany,charset = self.charset)

        else:

            print 'no valid charset defined !'
            sys.exit(1)


        if self.charset == 'dictAll' or self.charset == 'Fuzz':

            dns_fields = {'DNSQR_Packet': ['qname'], 'DNSRR_Packet': ['rrname','rdata']}


            '''sendpacket = IP(src="10.17.68.17", dst="10.0.6.90")/UDP(sport="domain",dport=RandShort())/DNS(id=0,qr=1L,opcode="QUERY",aa=1L,tc=0L,rd=1L,ra=1L,z=0L,rcode=0L,qdcount=1,ancount=1,nscount=0,arcount=0,qd=DNSQR(qname="ns1.target.ch" ,qtype="A",qclass="IN"),an=DNSRR(rrname="ns1.target.ch", type="A",rclass="IN",rdata="212.1.2.3"))
            sendpacket.show()'''


 
            for pattern in self.str_list:

                print "------------------------------------------------------------------"
                print pattern
                print "------------------------------------------------------------------"

                for packettype, fieldname in dns_fields.items():
    
                    for fname in fieldname:

                        classname = getattr(sys.modules[__name__], packettype)


                        if packettype == "DNSQR_Packet":

                            dnsrr_packet = DNSRR_Packet()

                            test_packet = "test_packet" + str(packetcounter)
                            packetcounter+=packetcounter+1

                            result_packet1 = DNS(qr=1,aa=1,ra=1,qdcount=self.id_to_name[index],ancount=self.id_to_name[index],qd=classname(qname=pattern),an=dnsrr_packet)
                            test_packet = IP(src=self.source, dst=self.dns_server)/UDP(sport=random.randint(1025, 65000))/result_packet1
                            self.sendlist.append(test_packet)


                            if index == 4:
                                index = 0

                            else:
                                index=index+1


                        else:

                            dnsqr_packet = DNSQR_Packet()
        
                            test_packet = "test_packet" + str(packetcounter)
                            packetcounter+=packetcounter+1

                            result_packet1 = DNS(qr=1,aa=1,ra=1,qdcount=self.id_to_name[index],ancount=self.id_to_name[index],qd=dnsqr_packet,an=classname(rrname=pattern))
                            test_packet = IP(src=self.source, dst=self.dns_server)/UDP(sport=random.randint(1025, 65000))/result_packet1


                            self.sendlist.append(test_packet)

                            if index == 4:
                                index = 0

                            else:
                                index=index+1

                            test_packet = "test_packet" + str(packetcounter)
                            packetcounter+=packetcounter+1

                            result_packet3 = DNS(qr=1,aa=1,ra=1,qdcount=self.id_to_name[index],ancount=self.id_to_name[index],qd=dnsqr_packet,an=DNSRR_Packet_RDLEN(rdata=pattern))
                            test_packet = IP(src=self.source, dst=self.dns_server)/UDP(sport=random.randint(1025, 65000))/result_packet3
                   
                            self.sendlist.append(test_packet)

                            if index == 4:
                                index = 0

                            else:
                                index=index+1
                            



        else:
            
            dnsrr_packet = DNSRR_Packet()
            
            test_packet = "test_packet" + str(packetcounter)
            packetcounter+=packetcounter+1


            result_packet1 = DNS(qr=1,aa=1,ra=1,qdcount=self.id_to_name[index],ancount=self.id_to_name[index],qd=DNSQR_Packet(qname=self.cset),an=dnsrr_packet)
            test_packet = IP(src=self.source, dst=self.dns_server)/UDP(sport=random.randint(1025, 65000))/result_packet1


            self.sendlist.append(test_packet)

            if index == 4:
                index = 0

            else:
                index=index+1

            test_packet = "test_packet" + str(packetcounter)
            packetcounter+=packetcounter+1
 
            result_packet7 = DNS(qr=1,aa=1,ra=1,qdcount=self.id_to_name[index],ancount=self.id_to_name[index],qd=DNSQR_Packet(),an=DNSRR_Packet(rrname=self.cset))
            test_packet = IP(src=self.source, dst=self.dns_server)/UDP(sport=random.randint(1025, 65000))/result_packet7

            self.sendlist.append(test_packet)

            if index == 4:
                index = 0

            else:
                index=index+1

            test_packet = "test_packet" + str(packetcounter)
            packetcounter+=packetcounter+1

            result_packet9 = DNS(qr=1,aa=1,ra=1,qdcount=self.id_to_name[index],ancount=self.id_to_name[index],qd=DNSQR_Packet(),an=DNSRR_Packet_RDLEN(rdata=self.cset))
            test_packet = IP(src=self.source, dst=self.dns_server)/UDP(sport=random.randint(1025, 65000))/result_packet9
            
            self.sendlist.append(test_packet)
       
            if index == 4:
                index = 0

            else:
                index=index+1
       

        return self.sendlist        

    def __handle_multiple_entries__(self,q):

        querydomain = q

        sendpacket = IP(dst=self.dns_server)/UDP(sport=RandShort())/DNS(rd=1,qd=DNSQR(qname=querydomain))

        try:

            ans = sr1(sendpacket, retry=1)
    
        except:

            print 'sending failed'
            return 1

        if self.querystring != "name_error":

            if ans[DNS].rcode == 0L:

                if self.ruletype != "app_redirect": 
                

                    for i in range(0,3):
            
                        self.namelist.append(ans[DNS].an[DNSRR][i].rdata)

                    if len(self.namelist) ==  self.expectedresultcount:

                        cnt = len(self.namelist)

                        for i in range(0,cnt):

                            if self.querystring == self.namelist[i]:

                                print 'blacklisted ip for multiple.target.ch is %s' %(self.namelist[i])
                            
                            else:

                                print "we expected blacklsited ip %s but got %s" %(self.querystring,self.namelist[i])
                                return 1 

                    else:

                        print 'we expected 3 blacklisted ips but only got %s' %(len(namelist))
                        return 1
            
                else:


                    tmpresult = ans[DNS].an.rdata

                    if tmpresult == self.querystring:

                        print '%s received for %s which is blacklisted' %(tmpresult,querydomain)

                    else:

                        print 'we expected a blacklisted ip %s but got %s' %(self.querystring,tmpresult)
                        return 1




            else:

                print 'received no answer'
                return 1

        else:

            if ans[DNS].rcode != 0L:

                print '%s is blacklisted via nx_domain' %(querydomain)

            else:

                print '%s is not blacklisted via nx_domain' %(querydomain)
        
                if self.ruletype != "app_redirect":               
                
                    for i in range(0,3):

                        print 'got %s ' %(ans[DNS].an[DNSRR][i].rdata)
                        return 1 

                else:

                    print 'got %s ' %(ans[DNS].an.rdata)

        return 0


    def blackl_domains(self,dns_server="",querystring="None",ruletype="forwarding"):

        self.dns_server = dns_server
        self.querystring = querystring
        self.expectedresultcount = 3
        self.ruletype = ruletype

        print "testing blacklists in IP mode with domain <target.ch>"
        print "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

        time.sleep(1)

        '''normal domains'''
        domain1 = "target.ch"
        server1 = [ "www1", "www2", "switch", "pop3", "ns2", "ns1", "ns", "multiple", "ftp", "cisco" ]

        
        cnt = len(server1)

        

        for i in range(0,cnt):

            q = server1[i] +"."+domain1


            multiple_entry = server1[i]


            if multiple_entry == "multiple":


                print 'checking multiple blacklisted ips for domain <multiple.target.ch>'

                time.sleep(1)

                retcode = self.__handle_multiple_entries__(q)

                if retcode != 0:

                    return 1


            else:

                sendpacket = IP(dst=self.dns_server)/UDP(sport=RandShort())/DNS(rd=1,qd=DNSQR(qname=q))

                try:

                    ans = sr1(sendpacket, retry=1)

                    
                    if self.querystring != "name_error": 

                        if ans[DNS].rcode == 0L:

                            tmpresult = ans[DNS].an.rdata

                            if tmpresult == self.querystring:

                                print '%s received for %s which is blacklisted' %(tmpresult,q)

                            else:

                                print 'we expected a blacklisted ip %s but got %s' %(self.querystring,tmpresult)
                                return 1
                        else:

                            print 'received no answer'
                            return 1


                    else:

                        if ans[DNS].rcode != 0L:

                            print 'received nx_domain for blacklisted domain %s' %(q)


                        else:

                            print '%s not blacklisted via nx_domain, received %s instead' %(q, ans[DNS].an.rdata)
                            return 1


                except:
    
                    print 'sending failed'
                    return 1



        return 0


    def blackl_subdomains(self, dns_server="",querystring="None",ruletype="forwarding"):

        self.dns_server = dns_server
        self.querystring = querystring
        self.ruletype = ruletype

    
        print "testing blacklists in IP mode with subdomains <www1..?.technet.com>"
        print "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

        time.sleep(1)

        '''subdomains'''
        domain2 = "technet.com"
        subdomain2 = [ "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "abc" ]        
        server2 = "www1"

        
        cnt = len(subdomain2)
        

        for i in range(0,cnt):

            q = server2 +"."+subdomain2[i]+"."+domain2


            non_bl_entry = subdomain2[i]

            sendpacket = IP(dst=self.dns_server)/UDP(sport=RandShort())/DNS(rd=1,qd=DNSQR(qname=q))

            if non_bl_entry == "abc":

                
                if self.querystring != "name_error":

                    try:

                        ans = sr1(sendpacket, retry=1)

                        if ans[DNS].rcode == 0L:

                            tmpresult = ans[DNS].an.rdata

                            if tmpresult == self.querystring:

                                print '%s should not be blacklisted due to regex www1.?.technet.com, but it is with A record %s' %(q,ans[DNS].an.rdata)
                                return 1
    
                            else:

                                print "%s is not blacklisted due to regex www1.?.technet.com, A record is %s" %(q,ans[DNS].an.rdata)

                        else:
                
                            print 'did not receive a valid answer for %s' %(q)
                            return 1

                    except:

                        print 'sending failed'
                        return 1

                else:


                    try:

                        ans = sr1(sendpacket, retry=1)

                        if ans[DNS].rcode != 0L:

                            print '%s is blacklisted via nx_domain, which is NOT due to regex www1.?.technet.com' %(q)
                            return 1

                        else:
                            
                             print '%s is not blacklisted due to regex www1.?.technet.com, data is %s' %(q, ans[DNS].an.rdata)             

                    except:

                        print 'sending failed'
                        return 1

            else:

                try:

                    ans = sr1(sendpacket, retry=1)

                    
                    if self.querystring != "name_error": 

                        if ans[DNS].rcode == 0L:

                            tmpresult = ans[DNS].an.rdata

                            if tmpresult == self.querystring:

                                print '%s received for %s which is blacklisted' %(tmpresult,q)

                            else:

                                print 'we expected a blacklisted ip %s but got %s' %(self.querystring,tmpresult)
                                return 1
                        else:

                            print 'received no answer'
                            return 1


                    else:

                        if ans[DNS].rcode != 0L:

                            print 'received nx_domain for blacklisted doamin %s' %(q)


                        else:

                            print '%s not blacklisted via nx_domain, received %s instead' %(q, ans[DNS].an.rdata)
                            return 1


                except:
    
                    print 'sending failed'
                    return 1

        return 0


    def blackl_cnames(self,dns_server="",querystring="None",ruletype="forwarding"):

        self.dns_server = dns_server
        self.querystring = querystring
        self.expectedresultcount = 5
        self.ruletype = ruletype

        print "testing blacklists in IP mode with cnames"
        print "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

        time.sleep(1)

        '''cname domains'''
        domains3 = [ "snap.blacklist.net", "www.google.com", "www.yahoo.com", "www.tirol.at" ]

        
        cnt = len(domains3)

        

        for i in range (0,cnt):

            q = domains3[i]


            sendpacket = IP(dst=self.dns_server)/UDP(sport=RandShort())/DNS(rd=1,qd=DNSQR(qname=q))

            try:

                ans = sr1(sendpacket, retry=1)

                
            except:
    
                print 'sending failed'
                return 1


            if self.querystring != "name_error": 

                if ans[DNS].rcode == 0L:

                    tmpresult = ans[DNS].an.rdata

                    if tmpresult == self.querystring:

                        print '%s received for %s which is blacklisted' %(tmpresult,q)

                    else:

                        print 'we expected a blacklisted ip %s but got %s' %(self.querystring,tmpresult)
                        return 1

                else:

                    print 'received no answer'
                    return 1


            else:

                if ans[DNS].rcode != 0L:

                    print 'received nx_domain for blacklisted doamin %s' %(q)


                else:

                    if q == "www.google.com":

                    
                        for i in range(0,4):
                    
                            self.namelist.append(ans[DNS].an[DNSRR][i].rdata)


                        for i in namelist:
                        
                            print '%s not blacklisted via nx_domain, received %s instead' %(q, namelist)
                            return 1

                    elif q == "snap.blacklist.net":

                            print '%s not blacklisted via nx_domain, received %s instead' %(q, ans[DNS].an[DNSRR][1].rdata)
                            return 1

                    elif q == "www.yahoo.com":

                        for i in range(4,5):           
                            print '%s not blacklisted via nx_domain, received %s instead' %(q, ans[DNS].an[DNSRR][i].rdata)
                            return 1
                            
                    elif q == "www.tirol.at":

                            print '%s not blacklisted via nx_domain, received %s instead' %(q, ans[DNS].an[DNSRR][1].rdata)
                            return 1
                    else:
                        
                            print 'not blacklisted at all'
                            return 1


        return 0

    
    def whitel_subdomains(self, dns_server="",querystring="None",ruletype="forwarding"):

        self.dns_server = dns_server
        self.querystring = querystring
        self.namelist = []
        self.ruletype = ruletype

    
        print "testing whitelists in IP mode with domain <technet.com>"
        print "+++++++++++++++++++++++++++++++++++++++++++++++++++++"

        time.sleep(1)

        '''subdomains'''
        domain2 = "technet.com"
        subdomain2 = [ "a", "b", "c" ]        
        server2 = "www1"

        
        cnt = len(subdomain2)
        

        for i in range(0,cnt):

            q = server2 +"."+subdomain2[i]+"."+domain2


            sendpacket = IP(dst=self.dns_server)/UDP(sport=RandShort())/DNS(rd=1,qd=DNSQR(qname=q))

                
            if self.querystring != "name_error":

                try:

                    ans = sr1(sendpacket, retry=1)

                    if ans[DNS].rcode == 0L:

                        tmpresult = ans[DNS].an.rdata

                        if tmpresult == self.querystring:

                            print '%s should not be blacklisted due to whitelist but it is' %(q)
                            return 1

                        else:

                            print "%s is in whitelist with A record %s" %(q,tmpresult)

                    else:
                
                            print 'did not receive a valid answer for %s' %(q)
                            return 1

                except:

                    print 'sending failed'
                    return 1


            else:

                sendpacket = IP(dst=self.dns_server)/UDP(sport=RandShort())/DNS(rd=1,qd=DNSQR(qname=q))

                
                try:

                    ans = sr1(sendpacket, retry=1)

                    if ans[DNS].rcode != 0L:

                        print 'received nx_domain for whitelisted domain %s which is not OK' %(q)
                        return 1

                    else:

                        print '%s is whitelisted with A record %s' %(q,ans[DNS].an.rdata)

                except:
                    
                    print 'sending failed'
                    return 1

        return 0
