#!/usr/bin/env python
"""
@package tresosita.timetools
@brief Time functions for all tresosita drivers.

@copyright Copyright by Elektrobit Automotive GmbH
All rights exclusively reserved for Elektrobit Automotive GmbH,
unless expressly agreed to otherwise.

@version EB tresos ITA 3.12.0
"""


import time
from enum import Enum

class EnumMessageStatus(Enum):
    """
        Common status definition for the messages on bus interfaces
    """
    UNINIT = 'NOT_INITIALIZED'
    TX_ERROR = 'TX_ERROR'
    PENDING = 'PENDING'
    TIMEOUT = 'TIMEOUT'
    OK = 'OK'
    UNKNOWN = 'UNKNOWN'



class Time(object):
    """
    class used for describing time information from different sources

    Internally time is stored in ns as an integer value and always rounded to the next smaller integer.
    All other attributes (s,ms,us) are calculated from that value and returned as float.

    """

    def __init__(self, timevalue=None, source=None, ns=None, us=None, ms=None, s=None):
        """
        initialize time values
        @param timevalue: Time value in milliseconds (integer or Time object)
        tbd: document other parameters
        """
        if timevalue is not None:
            if isinstance(timevalue, self.__class__):
                self._ns = timevalue.ns
            else:
                if timevalue != 0:
                    warnings.warn("Time value used without a unit, please use tresosita.time.s or tresosita.time.ms "
                                  "to specify time values. Using ms as default", DeprecationWarning)
                    self._ns = timevalue * 1000 * 1000
                else:
                    self._ns = 0
        elif ns is not None:
            self._ns = int(ns)
        elif us is not None:
            self._ns = int(us * 1000)
        elif ms is not None:
            self._ns = int(ms * 1000 * 1000)
            print(self._ns)
        elif s is not None:
            self._ns = int(s * 1000 * 1000 * 1000)
        else:
            raise RuntimeError("no time value specified")

        self.source = source

    def __str__(self):
        if self.source is None:
            return "%s" % self.pretty_format()
        else:
            return "%s (%s)" % (self.pretty_format(), self.source)

    def __repr__(self):
        return "<time %s from %s>" % (self.pretty_format(), self.source)

    def pretty_format(self):
        if abs(self.s) >= 1.0:
            return "%f s" % self.s
        elif abs(self.ms) >= 1.0:
            return "%f ms" % self.ms
        elif abs(self.us) >= 1.0:
            return "%f us" % self.us
        else:
            return "%d ns" % self.ns

    def _enforce_type(self, other):
        """
        enforce other to be of the same class as self
        """
        if not isinstance(other, self.__class__):
            return self.__class__(other)
        else:
            return other

    def _check_source(self, other):
        """
        compare the source field of other with ours and warn if there is a mismatch
        """
        if other.source != self.source:
            warnings.warn("Comparing time values from different sources (%s and %s). Results are probably inaccurate." % (self.source, other.source), UserWarning)
            return None
        else:
            return self.source

    def __add__(self, other):
        other = self._enforce_type(other)
        common_source = self._check_source(other)
        return self.__class__(ns=self.ns + other.ns, source=common_source)

    def __sub__(self, other):
        other = self._enforce_type(other)
        self._check_source(other)
        return self.__class__(ns=self.ns - other.ns, source=None)

    def __mul__(self, other):
        return self.__class__(ns=self.ns * other, source=self.source)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self.__class__(ns=self.ns / other, source=self.source)

    def __rdiv__(self, other):
        """
        division by a time value is not supported
        """
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            self._check_source(other)
            return other.ns == self.ns
        else:
            return self == self.__class__(other)

    def __lt__(self, other):
        other = self._enforce_type(other)
        self._check_source(other)
        return self.ns < other.ns

    @property
    def ns(self):
        return self._ns

    @property
    def us(self):
        return self.ns / 1000.0

    @property
    def ms(self):
        return self.ns / (1000.0 * 1000.0)

    @property
    def s(self):
        return self.ns / (1000.0 * 1000.0 * 1000.0)



'''def pollingLoop(timeout=1 * s, delay=100 * ms):
    """
    Default implementation of a polling loop
    (implementation from http://code.activestate.com/recipes/578163-retry-loop)

    @b Syntax
    @code{.py}
    for retry in pollingLoop(timeout, delay):
        res = getSomeResult()
        if res != expected_value:
            retry()
    @endcode


    @param timeout specified as Time object or as int/float representing milliseconds
    @param delay per loop run, specified as Time object or as int/float representing milliseconds
    """
    if isinstance(timeout, Time):
        timeout = timeout.ms
    if isinstance(delay, Time):
        delay = delay.ms

    delay = delay / 1000.0
    timeout = timeout / 1000.0
    starttime = time.time()
    success = set()
    backoff = 1
    duration = 0.0
    i = 0
    while True:
        i += 1
        success.add(True)
        yield success.clear
        if success:
            return
        duration = time.time() - starttime
        if timeout is not None and duration > timeout:
            break
        if delay:
            time.sleep(delay)
            delay = delay * backoff

    raise TimeoutError("Timeout on attempt {0} after {1:.3f} seconds".format(i, duration))'''


if __name__ == '__main__':


    ns = Time(ns=1)
    us = Time(us=1)
    ms = Time(ms=1)
    s = Time(s=1)

    #print(ns)
    #print(us)
    #print(ms)
    #print(s)

