#!/usr/bin/python
# -*- coding: utf-8 -*

from Synchronization import *


class Observer:
    def update(observable, arg):
        print("Updating myself %s"%str(observable))
        '''Called when observed object is updated or modified
        You call the observed objects notify_observers method to notify all the objects observers
        of the change'''
        pass


class Observable(Synchronization):
    def __init__(self):
        self.obs = []
        self.changed = 0
        super().__init__()

    def add_observer(self, observer):
        if observer not in self.obs:
            self.obs.append(observer)

    def delete_observer(self, observer):
        self.obs.remove(observer)

    def notify_observers(self, arg=None):
        ''' if the object has changed, notify all of its observers
        Each observer has its upate() method called with two arguments: this observable object and the generic arg'''
        self.mutex.acquire()
        try:
            if not self.changed: return
            local_array = self.obs[:]
            self.clear_changed()
        finally:
            self.mutex.release()
        # Updating is not required to be synchronized
        for observer in local_array:
            observer.update(self, arg)

    def notify_oberver(self, n_observer, arg=None):
        '''notify a specific observer when an object has changed'''
        self.mutex.acquire()
        try:
            if not self.changed: return
            local_array = self.obs[:]
            self.clear_changed()
        finally:
            self.mutex.release()
        # Updating is not required to be synchronized
        for observer in local_array:
            if type(observer) is type(n_observer):
                observer.update(self, arg)
                break

    def delete_observers(self): 
        self.obs = []

    def set_changed(self):
        self.changed = 1

    def clear_changed(self):
        self.changed = 0

    def has_changed(self):
        return self.changed

    def count_observers(self):
        return len(self.obs)

synchronize(Observable, "add_observer delete_observer delete_observers " +
                        "set_changed clear_changed has_changed count_observers")

