#!/usr/bin/python

class Date(object):

    def __init__(self, day=0, month=0, year=0):
        self.day = day
        self.month = month
        self.year = year

    @classmethod
    def from_string(cls, date_as_string):
        day, month, year = map(int, date_as_string.split('-'))
        date1 = cls(day, month, year)
        return date1


if __name__ == '__main__':
    # Static fields; an enumeration of instance
    #inputs = map(MouseAction, ["test action", "abc"])

    date1 = Date.from_string("11-09-2012")
    print(date1.year)
