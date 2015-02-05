# coding: utf-8
from __future__ import division, print_function
from collections import OrderedDict
from datarow import datarow_constructor
from itertools import compress, ifilterfalse, izip
from types import GeneratorType

import csv
import cStringIO
import ExcelRW
import UnicodeRW


class DataTable(object):

    def __init__(self, iterable=None):
        """
        You must pass in an iterable of:

        1. dict, where the keys will be counted as the headers ("fields"),
        2. list/tuple/generator, where the first will be assumed
           to be the fields.
        3. DataRow, from a previous DataTable.

        If your list of lists data doesn't have headers ("fields"),
        make some and append them to the beginning of your list of lists.

        If your data is CSV, TSV, or similar format, you can even copy-paste
        it the relevant script for on-the-fly DataTable construction. See
        the DataTable.fromcsvstring() method for details.
        """
        self.__data = OrderedDict()

        if iterable is None:
            return

        if not hasattr(iterable, '__iter__'):
            raise Exception("DataTable takes an iterable. "
                            "%s is not an iterable." % type(iterable))

        iterator = iterable.__iter__()
        first_row = iterator.next()

        # also identifies OrderedDict
        if isinstance(first_row, dict):
            for field in self.fields:
                self.__data[field] = [first_row[field]]
            for i, item in enumerate(iterator, 1):
                for field in self.fields:
                    try:
                        value = item[field]
                    except KeyError:
                        missing = self.__data.viewkeys()-item.viewkeys()
                        raise KeyError("Row %s is missing fields: %s" %
                                       (i, missing))
                    except TypeError:
                        raise TypeError("Although the first row of your data "
                                        "was a `dict`-like object, "
                                        "row %s was: %s" % (i, type(item)))
                    self.__data[field].append(value)
        elif isinstance(first_row, (list, tuple, GeneratorType)):
            # identifies namedtuples, and similar, including this library's
            # DataRow object. in their case, not only will the first row
            # not be headers, but we must access `._fields` to get
            # the header information. from then on, they should be the same.
            if isinstance(first_row, tuple) and hasattr(first_row, '_fields'):
                fieldnames = first_row._fields
                for fieldname, value in izip(fieldnames, first_row):
                    self.__data[fieldname] = [value]
            else:
                for fieldname in first_row:
                    self.__data[fieldname] = []
            for i, item in enumerate(iterator):
                if not isinstance(item, (list, tuple, GeneratorType)):
                    raise TypeError("Although the first row of your data "
                                    "was a `list`, `tuple`, or `generator`"
                                    "-like object, row %s was: "
                                    "%s" % (i, type(item)))
                if not hasattr(item, '__len__'):
                    item = tuple(item)
                if len(self.fields) != len(item):
                    raise Exception("Row %s's length does not match headers: "
                                    "%s vs %s" % (i,
                                                  len(self.fields),
                                                  len(item)))
                for field, value in izip(self.fields, item):
                    self.__data[field].append(value)
        else:
            raise Exception("Unrecognized row type: %s" % type(first_row))

    @property
    def fields(self):
        """
        A shallow copy of the list of fields in the DataTable.

        If you modify the DataTable, this list will not update.
        """
        return self.__data.keys()

    @property
    def __rowbuilder(self):
        return datarow_constructor(self.fields)

    @fields.setter
    def fields(self, new_fieldnames):
        """
        Overwrite all fields with new fields.
        """
        if len(new_fieldnames) != len(self.fields):
            raise Exception("Cannot replace fieldnames with list of "
                            "incorrect length: "
                            "%s vs %s" % (len(new_fieldnames),
                                          len(self.fields)))
        # We cast self.fields to a list so we don't iterate forever while
        # we mutate it.
        for old_name, new_name in izip(self.fields, new_fieldnames):
            # use pop instead of `del` in case old_name == new_name
            self.__data[new_name] = self.__data.pop(old_name)

    def rename(self, old_name, new_name):
        """
        Renames a specific field, and preserves the underlying order.
        """
        if old_name not in self:
            raise Exception("DataTable does not have field `%s`" % old_name)

        if old_name == new_name:
            return

        new_names = list(self.fields)
        location = new_names.index(old_name)
        del new_names[location]
        new_names.insert(location, new_name)
        self.fields = new_names

    @classmethod
    def fromcolumns(cls, fields, columns):
        if len(fields) != len(columns):
            raise Exception("When constructing .fromcolumns, the number "
                            "of fields must equal the number of columns: "
                            "%s vs %s" % (len(fields), len(columns)))
        new_table = cls()
        for field, column in izip(fields, columns):
            new_table[field] = column
        return new_table

    @classmethod
    def fromcsv(cls, path, delimiter=","):
        reader = UnicodeRW.UnicodeDictReader(open(path, 'r'),
                                             delimiter=delimiter)
        return cls(reader)

    @classmethod
    def fromcsvstring(cls, csvstring, delimiter=",", quotechar="\""):
        """
        Takes one string that represents the entire contents of the CSV
        file, or similar delimited file.

        If you have a list of lists, where the first list is the headers,
        then use the main constructor.

        If you see an excess of whitespace in the first column of your data,
        this is probably because you tried to format a triple-quoted string
        literal nicely. Don't add any padding to the left.

        NOTE: Please prefix your triple-quoted string literal with `u` or `ur`
        as necessary. For copy-pasting directly from Excel, use `ur`. For
        copy-pasting from something Python (or similar) printed, use `ur`.
        For something just dumped from Python via __repr__ or some other
        text source that displays escape characters used, use `u`.
        ---
        To build a DataTable from an .xls file, it's quite simple to:
        reader = ExcelReader('myfile.xls')
        reader.change_sheet('default')
        data = DataTable(reader)
        ---
        Implementation notes:

        The following solution was inspired by UnicodeRW.
        cStringIO.StringIO turns the passed string into a file-like
        (readble) object. The string must be encoded so that StringIO
        presents encoded text.

        In UnicodeRW, codecs.getreader('utf-8') reads an encoded file object
        to product a decoded file object on the fly. We don't need this.

        We read the StringIO object line by line into csv.reader,
        which is consumes encoded text and parses the CSV format out of it.
        Then we decode each cell one by one as we pass it into the data table

        csv.QUOTE_NONE (as well as the r-prefix on r'''string''') are vital
        since we're copy-pasting directly from Excel. The string should be
        treated as "literally" ("raw") as possible.
        """
        if not isinstance(csvstring, basestring):
            raise Exception("If trying to construct a DataTable with "
                            "a list of lists, just use the main "
                            "constructor. Make sure to include a header row.")

        stringio = cStringIO.StringIO(csvstring.encode('utf-8'))
        csv_data = csv.reader((line for line in stringio),
                              delimiter=delimiter,
                              dialect=csv.excel,
                              quotechar=quotechar,
                              quoting=csv.QUOTE_NONE)
        new_datatable = cls((s.decode('utf-8') for s in row)
                            for row in csv_data)
        for field in new_datatable.fields:
            new_datatable[field] = parse_column(new_datatable[field])
        return new_datatable

    @classmethod
    def fromdict(cls, datadict):
        """
        Constructs a new DataTable using a dictionary of the format:

        {field1: [a,b,c],
         field2: [d,e,f],
         field3: [g,h,i]}

        ... which most closely matches the internal representation
        of the DataTable. If it is an OrderedDict, the key order
        will be preserved.
        """
        new_datatable = cls()
        for field in datadict.keys():
            new_datatable[field] = datadict[field]
        return new_datatable

    @classmethod
    def fromxls(cls, path, sheet_name_or_num=0):
        reader = ExcelRW.UnicodeDictReader(path,
                                           sheet_name_or_num=sheet_name_or_num)
        return cls(reader)

    def __eq__(self, other):
        """
        Note that there is a bug (in my opinion) where two OrderedDicts
        are considered equal if they are identical even if one dict
        has more key-value pairs after the initial matching set.

        The line where we compare the length of the two DataTables and
        the number of keys is meant to protect against this bug.
        """
        if not isinstance(other, DataTable):
            return False
        if len(self) != len(other) or len(self.fields) != len(other.fields):
            return False
        for selfrow, otherrow in izip(self, other):
            if selfrow != otherrow:
                return False
        return True

    def __len__(self):
        if not self.__data:
            return 0
        else:
            return len(self.__data.viewvalues().__iter__().next())

    def __contains__(self, fieldname):
        return fieldname in self.__data.viewkeys()

    def __delitem__(self, key):
        del self.__data[key]

    # TODO: support passing in multiple column headers
    def __getitem__(self, item):
        """
        Pass in a fieldname to retrieve a column:
        column = dt['column_name']

        Or slice the DataTable like a list:
        sliced = dt[:30:2]
        """
        if isinstance(item, slice):
            start, stop, step = item.indices(len(self))
            sliced_table = DataTable()
            for field in self.fields:
                sliced_table[field] = self.__data[field][start:stop:step]
            return sliced_table
        elif isinstance(item, (list, tuple)):
            return [self.__getitem__(colname) for colname in item]
        elif isinstance(item, basestring):
            if item not in self:
                raise KeyError("DataTable does not have column `%s`" % item)
            return self.__data[item]
        elif isinstance(item, (int, long)):
            return self.row(item)
        else:
            raise KeyError("DataTable does not support indexing with `%s`" %
                           type(item))

    # TODO: set with slice?
    def __setitem__(self, fieldname, column):
        """
        dt['new_column'] = [1, 2, 3]
        """
        if not isinstance(column, list):
            column = list(column)
        if self.__data and len(column) != len(self):
            raise Exception("New column length must match length "
                            "of table: %s != %s" % (len(column), len(self)))
        self.__data[fieldname] = column

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        accumulator = print_tab_separated(self.fields) + u"\n"
        for line in self:
            accumulator += print_tab_separated(line.values()) + u"\n"
        return accumulator[:-1]

    def apply(self, func, *fields):
        """
        Applies the function, `func`, to every row in the DataTable.

        If no fields are supplied, the entire row is passed to `func`.
        If fieldds are supplied, the values at all of those fields
        are passed into func in that order.
        ---
        data['diff'] = data.apply(short_diff, 'old_count', 'new_count')
        """
        results = []
        for row in self:
            if not fields:
                results.append(func(row))
            else:
                results.append(func(*[row[field] for field in fields]))
        return results

    def distinct(self, fieldname, key=None):
        """
        Returns the unique values seen at `fieldname`.
        """
        return list(unique_everseen(self[fieldname], key=key))

    def groupby(self, *groupfields, **aggregators):
        """
        Groupby returns a new DataTable. The first column is the "groupkey",
        which is the unique set of fields used to identify this group. You
        may pass in as many groupfields as you'd like to group by.

        The other columns, to the right, are the results of aggregation
        functions on the lists of TableRows captured for each unique group.
        These are passed in as keyword arguments.

        There are some built-in aggregation functions, such as:

        concat : concatenates string-like values, like ",".join
        min, max, sum, mean : self explanatory effects on lists of numbers

        These are called like:

        data.groupby('colors', sum='randnum')

        Multiple groups can be called like:

        data.groupby('colors', 'apostle', min='randnum2', max='randnum2')

        Custom aggregation functions can be added easily. Below is an example
        that counts the length of the group list:

        data.groupby('colors', agg=len)

        A more complex example of a custom aggregation function might be:

        aggfunc = lambda rows: ','.join(row['apostle'] for row in rows)
        data.groupby('colors', agg=aggfunc))

        Here's a cool recipe for a generalizeable concat:

        concat = lambda field: lambda rows: ",".join(r[field] for r in rows)
        data.groupby('colors', agg=concat('apostle'))

        Consider taking into consideration this recipe taking advantage of
        closures when writing your own custom groupby code.
        """

        # Checking groupfields.
        if len(groupfields) == 1:
            keyfunc = lambda r: r[groupfields[0]]
        elif len(groupfields) == 0:
            raise Exception("Must pass at least one field to group by")
        elif len(groupfields) >= len(self.fields):
            raise Exception("Can't groupby using more groupfields than "
                            "the DataTable has fields")
        else:
            keyfunc = lambda r: tuple(r[groupfield]
                                      for groupfield in groupfields)

        builtin_aggs = {'concat': group_concat,
                        'min': min_aggregation,
                        'max': max_aggregation,
                        'sum': sum_aggregation,
                        'mean': mean_aggregation}

        aggregation_functions = []
        for argname, argvalue in aggregators.items():
            if argname in builtin_aggs:
                # We found the argname in the built-in aggregators,
                # so the value must be the fieldname we want to aggregate.
                aggregation_functions.append(builtin_aggs[argname](argvalue))
            else:
                if not callable(argvalue):
                    raise Exception("Passed in an uncallable object: "
                                    "%s, %s" % (argvalue, type(argvalue)))
                # We try to assign the argname to the argvalue, which
                # is probably a function. If it's a lambda or a regular
                # function, this works. If it's a built-in, like len(),
                # it will fail with an AttributeError - which is fine.
                try:
                    argvalue.__name__ = argname
                except AttributeError:
                    pass
                aggregation_functions.append(argvalue)

        groups = OrderedDict()
        for row in self:
            groupkey = keyfunc(row)
            if groupkey not in groups:
                groups[groupkey] = [row]
            else:
                groups[groupkey].append(row)

        new_table = DataTable()
        # TODO: fix this with a new groupby object
        new_table[','.join(groupfields)] = [unicode(i) for i in groups.keys()]

        if not aggregation_functions:
            new_table['groups'] = groups.values()
        else:
            for aggfunc in aggregation_functions:
                new_table[aggfunc.__name__] = [aggfunc(group)
                                               for group in groups.values()]
        return new_table

    def mask(self, masklist):
        """
        `masklist` is an array of Bools or equivalent.

        This returns a new DataTable using only the rows that were True
        (or equivalent) in the mask.
        """
        if not hasattr(masklist, '__len__'):
            masklist = list(masklist)

        if len(masklist) != len(self):
            raise Exception("Masklist length must match length of DataTable")

        new_datatable = DataTable()
        for field in self.fields:
            new_datatable[field] = list(compress(self[field], masklist))
        return new_datatable

    def col(self, colnum):
        """
        Returns the col at index `colnum`.
        """
        if colnum > len(self.fields):
            raise IndexError("Invalid column index `%s` for DataTable" % colnum)
        return self.__data[self.fields[colnum]]

    def row(self, rownum):
        """
        Returns the row at index `rownum`.
        ---
        Note that the TableRow object returned that represents the data row
        is constructed on the fly and is a just a shallow copy of
        the underlying data that does not update dynamically.
        """
        if rownum > len(self):
            raise IndexError("Invalid row index `%s` for DataTable" % rownum)
        return self.__rowbuilder([self[field][rownum] for field in self.fields])

    def sort(self, fieldname, key=lambda x: x, desc=False, inplace=False):
        """
        This matches Python's built-in sorting signature closely.

        By default, a new DataTable will be returned and the original will
        not be mutated. If preferred, specify `inplace=True` in order to
        mutate the original table. Either way, a reference to the relevant
        table will be returned.
        """
        field_index = list(self.fields).index(fieldname)

        data_cols = izip(*sorted(izip(*[self.__data[field]
                                        for field in self.fields]),
                                 key=lambda row: key(row[field_index]),
                                 reverse=desc))

        if inplace:
            target_table = self
        else:
            target_table = DataTable()

        for field, data_col in izip(self.fields, data_cols):
            target_table[field] = list(data_col)

        # Note that sorting in-place still returns a reference
        # to the table being sorted, for convenience.
        return target_table

    def where(self, fieldname, value, negate=False):
        """
        Takes either:

        1. A callable (like a function) that returns a bool.
        2. A container (list, tuple, or set).
        3. A primitive type (int, float, unicode, str, bool, long).

        Returns a DataTable that has been filtered such that the value
        for `fieldname` in each row:

        1. Returns True when passed into value.
        2. Is contained within value.
        3. Is comparable to value.

        ... for each of the three possible kinds of arguments, respectively.
        """
        if not negate:
            truth_func = lambda boolean: boolean
        else:
            truth_func = lambda boolean: not boolean

        if callable(value):
            return self.mask([truth_func(value(item))
                              for item in self[fieldname]])
        elif isinstance(value, (list, tuple, set)):
            return self.mask([truth_func(item in value)
                              for item in self[fieldname]])
        elif isinstance(value, (int, float, basestring, bool, long)):
            return self.mask([truth_func(item == value)
                              for item in self[fieldname]])
        else:
            raise Exception("Unsure how to filter DataTable where value is "
                            "of type: %s" % type(value))

    def wherefunc(self, func):
        """
        Applies a function to an entire row and filters the rows based on the
        boolean output of that function.
        """
        return self.mask([func(item) for item in self])

    def wherenot(self, fieldname, value):
        """
        Exact opposite of `self.where()`.
        """
        return self.where(fieldname, value, negate=True)

    def writecsv(self, path):
        writer = UnicodeRW.UnicodeDictWriter(open(path, 'wb'), self.fields)
        writer.writeheaders()
        writer.writerows(self)
        writer.close()

    def writexls(self, path, sheetname="default"):
        writer = ExcelRW.UnicodeDictWriter(path)
        writer.set_active_sheet(sheetname, self.fields)

        writer.writeheaders()
        writer.writerows(self)
        writer.save()

    def __iter__(self):
        for values in izip(*[self.__data[field] for field in self.fields]):
            yield self.__rowbuilder(values)


def aggregator_factory(fieldname, func, funcname):
    def _aggregation_function(rows):
        return func([row[fieldname] for row in rows])
    _aggregation_function.__name__ = funcname % fieldname
    return _aggregation_function


def group_concat(fieldname):
    func = lambda strings: ",".join(strings)
    return aggregator_factory(fieldname, func, 'group_concat(%s)')


def max_aggregation(fieldname):
    return aggregator_factory(fieldname, max, 'max(%s)')


def min_aggregation(fieldname):
    return aggregator_factory(fieldname, min, 'min(%s)')


def sum_aggregation(fieldname):
    return aggregator_factory(fieldname, sum, 'sum(%s)')


def mean_aggregation(fieldname):
    mean = lambda nums: sum(nums)/len(nums)
    return aggregator_factory(fieldname, mean, 'mean(%s)')


def parse_column(column):
    """
    Helper method for DataTable.fromcsvstring()

    Given a list, parse_column tries to see if it should cast
    everything in that list to a float, an int, or leave it as is.

    Always returns a list.
    """
    try:
        float_attempt = [float(i) for i in column]
    except ValueError:
        return column
    else:
        try:
            int_attempt = [int(j) for j in column]
        except ValueError:
            return float_attempt
        else:
            return int_attempt


def print_tab_separated(row):
    template = ("%s\t" * len(row))[:-1]
    return template % tuple(row)


def unique_everseen(iterable, key=None):
    """
    List unique elements, preserving order. Remember all elements ever seen.

    unique_everseen('AAAABBBCCDAABBB') --> A B C D
    unique_everseen('ABBCcAD', str.lower) --> A B C D
    """
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in ifilterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element
