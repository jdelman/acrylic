# coding: utf-8

from itertools import izip


def datarow_constructor(fields):

    class DataRow(tuple):

        __slots__ = ()

        _fields = tuple(fields)

        def __new__(cls, values):
            return tuple.__new__(cls, tuple(values))

        def __repr__(self):
            return 'DataRow(%s)' % ', '.join([unicode(item) for item in self])

        # TODO: should lists and slicing be supported?
        def __getitem__(self, item):
            if isinstance(item, (str, unicode)):
                index = self._fields.index(item)
                return super(DataRow, self).__getitem__(index)
            elif isinstance(item, (int, long)):
                return super(DataRow, self).__getitem__(item)
            else:
                raise Exception("Unrecognized index type: %s" % type(item))

        def items(self):
            return zip(self._fields, self)

        def iteritems(self):
            return izip(self._fields, self)

    return DataRow