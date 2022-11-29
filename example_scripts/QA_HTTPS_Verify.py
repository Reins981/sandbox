#! /usr/bin/env python
# vim:ts=4:sw=4:expandtab
import sys
import os
import ssl
import socket
import httplib
import pprint
from urllib2 import Request, urlopen, URLError, HTTPError, ProxyHandler, build_opener, install_opener
from subprocess import call
from modules.QA_NGFW import QA_NGFW

class bcolors:

    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    THREAD = '\033[94m'
    WAIT = '\033[95m'

    def disable(self):

        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.THREAD = ''
        self.WAIT = ''

class SecureHTTPSConnection(httplib.HTTPSConnection):

    def __init__(self, host=None, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 local_cert=None,value="",ssl_attribute="CommonName"):
        self.my_cert = cert_file
        self.value = value
        self.ssl_attribute = ssl_attribute
        self.char_count = 0
        self.local_cert_stripped = ""
        self.final_local_cert = ""
        httplib.HTTPSConnection.__init__(self,
                        host, port, key_file, cert_file, strict, timeout)
        self.local_cert = local_cert

    def __return_attribute__(self,filename=None,value=None):
        filename = filename
        value = value
        final_line = ""
        search_entry=""
        
        if value == "Subject" or value == "subject":
            search_entry="Subject:"
            value = value.lower()
        if value == "Issuer" or value == "issuer":
            search_entry="Issuer:"
            value = value.lower()
        if value == "CommonName" or value == "commonname":
            search_entry="CN="
            value = value.lower()
        if value == "ComonName":
            search_entry="CN="
            value = "commonname"
        if value == "Organization" or value == "organization":
            search_entry="Subject:"
            value = value.lower()
        if value == "OrganizationalUnit" or value == "organizationalunit":
            search_entry="Subject:"
            value = value.lower()
        if value == "emailAddress" or value == "emailaddress":
            search_entry="Subject:"
            value = value.lower()

        datafile = open(filename,'r')

        if value == "subject":
            for line in datafile:
                if search_entry in line:
                    final_line = line
                    break
        if value == "issuer":
            for line in datafile:
                if search_entry in line:
                    final_line = line
                    break
        if value == "commonname" or value == "organization" or value == "organizationalunit" or value == "emailaddress":
            for line in datafile:
                if "Subject:" in line:
                    for position,char in enumerate(line):
                        if value == "commonname":
                            if char == 'C':
                                if line[position+1] == 'N' and line[position+2] == '=':
                                    final_line = line[position+3:line.index("/")]
                                    break
                        elif value == "organization":
                            if char == 'O':
                                if line[position+1] == '=':
                                    line_tmp = line[position+2:]
                                    line_tmp = line_tmp[:line_tmp.index(',')]
                                    final_line = line_tmp
                                    break
                        elif value == "organizationalunit":
                            if char == 'O':
                                if line[position+1] == 'U' and line[position+2] == '=':
                                    line_tmp = line[position+3:]
                                    line_tmp = line_tmp[:line_tmp.index(',')]
                                    final_line = line_tmp
                                    break
                        else:
                            if char == '/':
                                final_line = line[position+14:]
                                final_line.rstrip('\n')
                                break
        datafile.close()
        return final_line



    def connect(self):
        """Connect to a host on a given (SSL) port.
        and verify certificate
        """
        try:
            httplib.HTTPSConnection.connect(self)
        except HTTPError, e:
            print bcolors.FAIL + 'Error code: ', e.code
        except URLError, e:
            print bcolors.FAIL + 'Reason: ', e.reason
        except socket.error, e:
            print bcolors.FAIL + 'socket error: ', str(e)


        # verify cert
        if self.local_cert is not None:
            cert = self.sock.getpeercert(True)
            # we need the private key , otherwise no cert verification is possible
            #self.databaselist = self.ngfw.shellEx("cat /opt/phion/preserve/cuda.vars -")
            if cert == None:
                print bcolors.FAIL + 'something went wrong in getting the cert'
            else:
                print bcolors.OKGREEN + 'retrieved cert successfully'
            with open(self.local_cert) as certfile:
                local_cert = certfile.read()
                self.final_local_cert = local_cert
            if local_cert[:10] == '-----BEGIN':  # we got a pem
                print bcolors.OKGREEN + 'we got a pem'
            else:
                print bcolors.FAIL + 'cert format not yet supported'
            cert = ssl.DER_cert_to_PEM_cert(cert)
            self.final_local_cert = self.final_local_cert.replace('-----BEGIN CERTIFICATE-----', '\n-----BEGIN CERTIFICATE-----')
            self.final_local_cert = self.final_local_cert.strip()
            cert = cert.replace('-----END CERTIFICATE-----', '\n-----END CERTIFICATE-----')
            remote_file = open('remotecert.pem','w')
            remote_file.write(cert)
            remote_file.close()
            local_file = open('localcert.pem','w')
            local_file.write(self.final_local_cert)
            local_file.close()
            with open('localcert.txt','w') as local:
                call(["openssl", "x509", "-in", "localcert.pem", "-text", "-noout"], stdout=local)
            with open('remotecert.txt','w') as remote:
                call(["openssl", "x509", "-in", "remotecert.pem", "-text", "-noout"], stdout=remote)

            attribute_remote = self.__return_attribute__(filename='remotecert.txt',value=self.ssl_attribute)
            attribute_local = self.__return_attribute__(filename='localcert.txt',value=self.ssl_attribute)
            if self.local_cert_stripped != cert:
                print bcolors.FAIL + "!!!!!!!!!!!!!!!!!"
                print "Remote cert does not match provided one!!"
                pprint.pprint(self.final_local_cert)
                print "#######################################"
                print pprint.pprint(cert)
                print bcolors.FAIL + "!!!!!!!!!!!!!!!!!"

            if attribute_local != attribute_remote:
                print bcolors.FAIL + "!!!!!!!!!!!!!!!!!"
                pprint.pprint(attribute_local)
                print bcolors.FAIL + "DIFFERS FROM"
                pprint.pprint(attribute_remote)
                print bcolors.FAIL + "!!!!!!!!!!!!!!!!!"

            if attribute_local == attribute_remote:
                print bcolors.FAIL + "!!!!!!!!!!!!!!!!!"
                pprint.pprint(attribute_local)
                print bcolors.OKGREEN + "IS EQUAL TO"
                pprint.pprint(attribute_remote)
                print bcolors.FAIL + "!!!!!!!!!!!!!!!!!"

        httplib.HTTPSConnection.request(self,"GET", "/"+self.value)
        response = httplib.HTTPSConnection.getresponse(self)
        return response

