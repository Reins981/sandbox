'''
Created on 22.02.2017

@author: uwpe9547
'''
import logging
import time
import os
import socket
import telnetlib

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TargetConnector(object):
    '''
    opens the connection to the target and copies one file
    '''

    CFG_CONNECT_TIMEOUT = 3
    CFG_LIST_OF_FAILURE_CASES = ['Cannot execute', ': File not found']
    FINISH_FLAG = ">>> "
    __telnet_object = None

    def __init__(self, ip_address="127.0.0.1", conn_timeout=10, read_timeout=2, retries=100):
        self.__address = ip_address
        self.output = None
        self.__timeout = conn_timeout # in seconds
        self.__read_timeout = read_timeout # in minutes
        self.__retries = retries
        self.__ip_address = ip_address
        self.__port = 4477
        self.__telnet_user = ""
        self.__telnet_password = ""
        self.__logging_started = False
        self.__wait_time = 3
        self.success = False

        if self.__telnet_object is None:
            self.__connect()

    def is_target_connected(self):
        return self.success and self.__telnet_object is not None


    def __execute_commands(self):
        self.__telnet_object.write("import btn" + "\n")
        self.__telnet_object.read_until(">>> ", self.CFG_CONNECT_TIMEOUT)
        self.__telnet_object.write("import tst.nav2.F30X.TestRun" + "\n")
        self.__telnet_object.read_until(">>> ", self.CFG_CONNECT_TIMEOUT)
        self.__telnet_object.write("tst.nav2.F30X.doIt()" + "\n")

    def __read_from_stream_buf(self):
        print("read from stream buff until read timeout %s minute(s) is reached" %self.__read_timeout)
        current_time = time.time()
        end_time = current_time + (self.__read_timeout*60) # convert read_timeout to seconds

        while (current_time <= end_time):
            try: 
                print bcolors.OKGREEN + "sending keep alive" + bcolors.ENDC
                self.__telnet_object.write("send_keep_alive\n")
                time.sleep(1)
                # try to read anything until timeout is hit to avoid blocking indefinitely
                #self.__telnet_object.expect([".*"], 10)
                response = self.__telnet_object.read_very_eager()
                if len(response) == 0:
                    print bcolors.FAIL + "Did not receive a telnet response" + bcolors.ENDC
                    continue
                print bcolors.OKBLUE + "Got telnet response: " + str(response) + bcolors.ENDC
            except EOFError as eof_error:
                print bcolores.WARNING + "Encountered an EOFError while trying " \
                            "to read from buffer. " \
                            "Error details:\n" + str(eof_error) + bcolors.ENDC
                break
            except socket.timeout as socket_timeout:
                print bcolors.FAIL + "Could not read from buffer due to timeout -> " + str(socket_timeout) + bcolors.END
                break

            current_time = time.time()

        self.__disconnect()

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
            #self.__telnet_object.read_until(self.FINISH_FLAG, self.__telnet_object.read_until(">>> ", self.CFG_CONNECT_TIMEOUT)
            self.success = True
            print("Successfully connected to target IP: " + str(self.__ip_address))
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

    def __disconnect(self):
        '''
        Disconnect the telnet and ftp connection
        '''
        print("start disconnect")
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
            time.sleep(2)
            self.__disconnect()
            self.__connect()
            if self.send_keep_alive():
                print("Successfully reconnected to target IP: " +
                             str(self.__ip_address) + " after " +
                             str(i) +
                             ' retries.')
                return True
            else:
                print("Target {0} is not online after {1} retries".format(str(self.__ip_address), str(i+1)))
                if i < self.__retries-1:
                    print("Retrying to connect ...")
                continue

        print("Could not reconnect to target IP: " +
                    str(self.__ip_address) + " after " +
                    str(i) +
                    ' retries.')
        return False


    def send_keep_alive(self):
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
                    print("telnet connection alive got message \"{0}\" ".format(str(telnet_output)))
                    return True
        except (EOFError, socket.error, AttributeError) as telnet_exception:
            print("telnet connection not alive - " + str(telnet_exception))

        return False


    def run_test_set(self):
        self.__execute_commands()
        self.__read_from_stream_buf()

