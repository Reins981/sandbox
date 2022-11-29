
from abc import abstractmethod
from string import printable

def convert_byte_in_list_to_ascii(byte_list, byte_nr):
    print(id(byte_list))
    byte = byte_list[byte_nr]
    if chr(byte) in printable and byte >= 0x20:
        byte_list[byte_nr] = chr(byte)
    else:
        byte_list[byte_nr] = "\\x%02x" % byte

def main():
    my_list = [0x24]
    print(id(my_list))
    print(my_list[0])
    convert_byte_in_list_to_ascii(my_list, 0) 
    print(my_list[0])
    
if __name__ == "__main__":
    main()
