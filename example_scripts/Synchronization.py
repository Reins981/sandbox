#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading

def synchronized(method):
    def f(*args):
        self = args[0]
        self.mutex.acquire()
        try:
            return method(*args)
        finally:
            self.mutex.release()
    return f


def synchronize(m_class, names=None):
    """Synchronize methods in the given class
    Only synchronize the methods whose names are given, or all methods if names=None."""
    if type(names) == type(''): names = names.split()
    for (name,val) in m_class.__dict__.items():
        if callable(val) and name != '__init__' and \
                (names is None or name in names):
                    setattr(m_class, name, synchronized(val))


# create your own self.mutex or inherit from this class
class Synchronization:
    def __init__(self):
        self.mutex = threading.RLock()
