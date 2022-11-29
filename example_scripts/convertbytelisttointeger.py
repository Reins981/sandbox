#!/usr/bin/python

import sys
import string

def convert_byte_list_to_integer(byte_list):
    """ Convert Byte sequence to integer depend on selected byte order
        :param byte_list: list of integer bytes to be converted.
        :param byte_order: byteorder as string (big-endian, little-endian)
        @return : integer|long - Integer value
    """
    data_bytes = byte_list[:]

    i, value = 0, 0
    while i < len(data_bytes):
        value += data_bytes[i] << (i*8)
        i += 1

    return value


if __name__ == '__main__':

    
    print(convert_byte_list_to_integer([49, 136, 128, 0]))
