#!/usr/bin/python
import sys, time
from telnet import *
import subprocess
from os import getcwd, listdir
from os.path import isfile, join

class FileParser(object):
    def __init__(self, filename):
        self.filename = filename

    def add_option_after_line(self, option, line):
        buf = None
        line_found = False

        with open(self.filename, "r") as in_file:
            buf = in_file.readlines()

        with open(self.filename, "w") as out_file:
            for line_buf in buf:
                if line_found and "4477" in line_buf:
                    print("already found %s" %line_buf)
                    continue
                if line in line_buf:
                    line_found = True
                    line_buf = line_buf + option + " ^\n"
                out_file.write(line_buf)


def file_exists_in_current_dir(filename):
    return isfile(("/".join((getcwd(),filename))))

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-f", "--simulator", dest="batfilename",
                      help="select a simulator bat file")
    parser.add_option("-t", "--timeout", dest="timeout", default=60, type="int",
                      help="terminate telnet connection + program when the given timeout in minute(s) exceeds")
    
    (options, args) = parser.parse_args()
    if options.batfilename is None:
        parser.error("Incorrect number of arguments!")
        sys.exit(1)

    parser = FileParser(options.batfilename)
    parser.add_option_after_line("-DPyTerminalPort=4477", "JRE\\bin\java")

    p = None
    if file_exists_in_current_dir(options.batfilename):
        p = subprocess.Popen(["./"+options.batfilename])
    else:
        p = subprocess.Popen([options.batfilename])

    print("Simulator started successfully")

    # terminate when read_timeout is reached
    timeout = options.timeout
    connector = TargetConnector(read_timeout=timeout)
    if not connector.is_target_connected() and not connector.reconnect():
        sys.exit(0)

    print("Run test set....")
    connector.run_test_set()
    print("Ran into read_timeout = %s, terminating now.." %timeout)
    subprocess.Popen("taskkill /F /T /PID %i"%p.pid , shell=True)
    sys.exit(0)
