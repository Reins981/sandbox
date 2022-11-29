class CifIPType(object):
    def __init__(self):
        self.__value = {}
        self.__mapping = {4: "CIF_ETH_TP_IPv4", 6: "CIF_ETH_TP_IPv6"}

    def __set__(self, obj, value):
        print("in set")
        self.__value[obj] = getattr(self.__mapping[value])

    def __get__(self, obj, obj_owner):
        print("in get")
        return self.__value

class A:
    m_type = CifIPType()

def main():
    a = A()
    a.m_type = 1
    print(a.m_type)

if __name__ == "__main__":
    main()

