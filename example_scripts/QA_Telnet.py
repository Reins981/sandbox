'''
Created on 22.02.2017

@author: uwpe9547
'''
import logging
import os
import socket
import telnetlib

class TargetConnector(object):
    '''
    opens the connection to the target and copies one file
    '''

    CFG_CONNECT_TIMEOUT = 3
    CFG_LIST_OF_FAILURE_CASES = ['Cannot execute', ': File not found']
    FINISH_FLAG = "# "
    __telnet_object = None

    def __init__(self, ip_address="127.0.0.1", timeout=10, retries=10):
        self.__address = ip_address
        self.output = None
        self.__timeout = timeout
        self.__retries = retries
        self.__ip_address = ip_address
        self.__port = 4477
        self.__telnet_user = ""
        self.__telnet_password = ""
        self.__logging_started = False
        self.__wait_time = 3

        if self.__telnet_object is None:
            if self.__connect():
                logging.debug("Successfully connected to target IP: " +
                str(self.__ip_address))

            logging.debug("created instance: " + str(self))



    def __connect(self):
        '''
        Create a telnet connection to the target
        '''
        try:
            self.__telnet_object = \
                telnetlib.Telnet(self.__ip_address, 
                                 self.__port,
                                 timeout=self.CFG_CONNECT_TIMEOUT)

            #self.__telnet_object.read_until("login: ", self.CFG_CONNECT_TIMEOUT)
            #self.__telnet_object.write(self.__telnet_user + "\n")
            #self.__telnet_object.read_until("Password:", self.CFG_CONNECT_TIMEOUT)
            #self.__telnet_object.write(self.__telnet_password + "\n")
            #self.__telnet_object.read_until(self.FINISH_FLAG, self.CFG_CONNECT_TIMEOUT)
            self.__telnet_object.read_until(">>> ", self.CFG_CONNECT_TIMEOUT)
            self.__telnet_object.write("import btn" + "\n")

            return True
        except socket.timeout as socket_timeout:
            logging.warning("Socket module raised an internal "
                            "socket.timeout Exception. " + str(socket_timeout))
        except socket.error as socket_error:
            logging.warning("Cannot connect to Telnet on target IP: " +
                            str(self.__ip_address) + ': Got a socket '
                            "Error. " + str(socket_error))
        except EOFError as eof_error:
            logging.debug(eof_error.message, exc_info=True)
            logging.warning("Encountered an EOFError while waiting on "
                            "a command prompt. "
                            "Error details:\n" + str(eof_error))

        return False

    def __disconnect(self):
        '''
        Disconnect the telnet and ftp connection
        '''
        logging.info("start disconnect")
        if self.__telnet_object is not None:
            self.__telnet_object.close()
            self.__telnet_object = None
            self.__logging_started = False
            logging.debug("disconnected")

    def reconnect(self):
        '''
        Telnet and ftp disconnect and connect
        '''
        logging.info("start reconnect")
        for i in range(self.__retries):
            self.__disconnect()
            self.__connect()
            if self.check_whether_alive():
                logging.info("Successfully reconnected to target IP: " +
                             str(self.__ip_address) + " after " +
                             str(i) +
                             ' retries.')
                return True
            else:
                logging.info("Target {0} is not online after {1} reties".format(str(self.__ip_address), str(i+1)))
                logging.info("Retrying to connect ...")
                continue
        return False

    def check_whether_alive(self):
        '''
        Check if the target can be accessed via telnet
        '''
        try:
            if self.__telnet_object.sock:
                # check if the .close() was called
                # write something to check if we get something in return
                self.__telnet_object.write("check_whether_alive\n")
                telnet_output = self.__telnet_object.read_until(self.FINISH_FLAG, self.CFG_CONNECT_TIMEOUT)
                logging.debug("telnet_output:\"%s\"", telnet_output)
                if len(telnet_output) > 0:
                    # can not check for a certain string, sometimes the telnet connection is polluted with log lines
                    logging.debug("telnet connection alive got message \"{0}\" ".format(str(telnet_output)))
                    return True
        except (EOFError, socket.error, AttributeError) as telnet_exception:
            logging.warning("telnet connection not alive - " + str(telnet_exception))

        return False

   
