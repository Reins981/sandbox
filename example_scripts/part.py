#!/usr/bin/python

def partition(number):
    answer = set()
    answer.add((number, ))
    print(" before for loop %s"%answer)
    for x in range(1, number):
        print(" in first for loop x = %s"%x)
        for y in partition(number -x):
            answer.add(tuple(sorted((x, ) + y)))
            print(" in second for loop %s"%answer)
    print(" before return %s"%answer)
    return answer


if __name__ == '__main__':
    print partition(4)
