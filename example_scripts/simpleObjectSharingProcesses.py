#!/usr/bin/python

from multiprocessing import Process, Pool
from multiprocessing.managers import BaseManager


class MySharedClass(object):
    stored_value = 0
    def get(self):
        return self.stored_value

    def set(self, new_value):
        self.stored_value = new_value
        return self.stored_value


class MyManager(BaseManager):
    pass


MyManager.register('MySharedClass', MySharedClass)

def worker ( proxy_object, i):
    proxy_object.set( proxy_object.get() + i )
    print ("id %d, sum %d" %(i, proxy_object.get()))
    return proxy_object


if __name__ == '__main__':
    manager = MyManager()
    manager.start()
    shared = manager.MySharedClass()

    pool = Pool(5)
    for i in range(33):
        pool.apply(func=worker, args=(shared, i))
    pool.close()
    pool.join()
    print "result: %d" % shared.get()
