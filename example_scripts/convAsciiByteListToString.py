#!/usr/bin/python

import sys
import string

def convAsciiByteListToString(byte_list):
    """ Converts a list of ASCII bytes to a printable string.
        :param byte_list: list of unsigned integers with max value 255.
            :return: printable string object
    """
    ret_val = ""
    for byte in byte_list:
        if chr(byte) in string.printable and byte >= 0x20:
            ret_val += chr(byte)
        else:
            ret_val += "\\x%02x" % byte
    return ret_val


if __name__ == '__main__':

    #m_input = (sys.argv[1])
    #m_input = map(int, m_input.strip('[]').split(','))
    
    print(convAsciiByteListToString())
