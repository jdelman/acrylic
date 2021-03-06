# coding: utf-8

"""
This class factory exists because it's the best way that I know of to
create an object with:

1. a dict-like mapping
2. a set of keys specified at runtime
3. a memory footprint much, much smaller than a dictionary

This concept was borrowed from the Python standard library's `namedtuple`
implementation.
"""

from itertools import izip


def datarow_constructor(fields):

    class DataRow(tuple):

        __slots__ = ()

        _fields = tuple(fields)

        def __new__(cls, values):
            return tuple.__new__(cls, tuple(values))

        def __repr__(self):
            return 'DataRow(%s)' % ', '.join([unicode(item) for item in self])

        def __getitem__(self, item):
            if isinstance(item, basestring):
                try:
                    index = self._fields.index(item)  # O(n) time
                except ValueError:
                    raise ValueError("Column `%s` does not exist in DataRow." %
                                     item)
                return super(DataRow, self).__getitem__(index)
            elif isinstance(item, (int, long, slice)):
                return super(DataRow, self).__getitem__(item)
            elif isinstance(item, (list, tuple)):
                columns = []
                for subitem in item:
                    if not isinstance(subitem, basestring):
                        raise KeyError("Multi-column access must be done with "
                                       "a list or tuple of strings. A %s was "
                                       "found in the list." % type(subitem))
                    columns.append(self[subitem])
                return columns
            else:
                raise Exception("Unrecognized index type: %s" % type(item))

        def items(self):
            return izip(self._fields, self)

        def get(self, value, default=None):
            if value not in self._fields:
                return default
            else:
                return self.__getitem__(value)

    return DataRow
