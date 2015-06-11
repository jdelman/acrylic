# coding: utf-8

from __future__ import division, print_function
from array import array
from collections import OrderedDict
from cStringIO import StringIO
from itertools import chain, compress, izip
from random import random, randrange, shuffle
from types import GeneratorType

from .datarow import datarow_constructor
from .groupby import GroupbyTable
from .utils import unique_everseen

from . import ExcelRW
from . import UnicodeRW

import csv


class DataTable(object):

    def __init__(self, iterable=None, headers=None, value_if_missing=None):
        """
        You must pass in an iterable of:

        1. dict, where the keys will be counted as the headers ("fields"),
        2. list/tuple/generator, where the first will be assumed
           to be the fields.
        3. DataRow, from a previous DataTable.

        If your list of lists data doesn't have headers ("fields"),
        make some and pass them into the `headers` parameter.

        If your data has headers and you pass in headers anyways, headers
        acts as a filter and selects the subset of headers you want included.
        If you pass in a header that isn't in the data, there will be an error.

        ---

        If your data is CSV, TSV, or similar format, you can even copy-paste
        it the relevant script for on-the-fly DataTable construction. See
        the DataTable.fromcsvstring() method for details.
        """
        self.__data = OrderedDict()

        if iterable is None:
            # TODO: this exists so that we can create a DataTable
            # TODO: with no data, but we can make headers
            # TODO: what's the best way to address this headers issue?
            if headers is not None:
                validate_fields(headers)
                for header in headers:
                    self.__data[header] = []
            return

        if not hasattr(iterable, '__iter__'):
            raise Exception("DataTable takes an iterable and "
                            "%s is not an iterable" % type(iterable))

        iterator = iterable.__iter__()
        first_row = iterator.next()

        # also identifies OrderedDict
        if isinstance(first_row, dict):
            if not headers:
                fields = first_row.keys()
            else:
                fields = headers
            validate_fields(fields)
            for field in fields:
                self.__data[field] = [first_row[field]]
            for i, item in enumerate(iterator, 1):
                for field in self.fields:
                    try:
                        value = item[field]
                    except KeyError:
                        if value_if_missing is not None:
                            self.__data[field].append(value_if_missing)
                            continue
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
                if not headers:
                    fields = first_row._fields
                else:
                    fields = headers
                validate_fields(fields)
                for field, value in izip(fields, first_row):
                    self.__data[field] = [value]
            else:
                if not headers:
                    fields = list(first_row)
                else:
                    fields = headers
                    iterator = chain((first_row,), iterator)
                validate_fields(fields)
                for field in fields:
                    self.__data[field] = []

            for i, item in enumerate(iterator):
                if not isinstance(item, (list, tuple, GeneratorType)):
                    raise TypeError("Although the first row of your data "
                                    "was a `list`, `tuple`, or `generator`"
                                    "-like object, row %s was: "
                                    "%s" % (i, type(item)))
                if not hasattr(item, '__len__'):
                    item = tuple(item)
                if len(self.fields) != len(item):
                    raise Exception("Row %s's length (%s) does not match "
                                    "headers' length (%s)" % (i,
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

    @fields.setter
    def fields(self, new_fieldnames):
        """
        Overwrite all field names with new field names. Mass renaming.
        """
        if len(new_fieldnames) != len(self.fields):
            raise Exception("Cannot replace fieldnames (len: %s) with list of "
                            "incorrect length (len: %s)" % (len(new_fieldnames),
                                                            len(self.fields)))
        for old_name, new_name in izip(self.fields, new_fieldnames):
            # use pop instead of `del` in case old_name == new_name
            self.__data[new_name] = self.__data.pop(old_name)

    @classmethod
    def fromcolumns(cls, fields, columns):
        if len(fields) != len(columns):
            raise Exception("When constructing .fromcolumns, the number of "
                            "fields (%s) must equal the number of columns (%s)"
                            % (len(fields), len(columns)))
        new_table = cls()
        for field, column in izip(fields, columns):
            new_table[field] = column
        return new_table

    @classmethod
    def fromcsv(cls, path, delimiter=",", headers=None):
        f = open(path, 'r')
        reader = UnicodeRW.UnicodeDictReader(f,
                                             delimiter=delimiter)
        new_table = cls(reader, headers=headers)
        f.close()
        return new_table

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

        Implementation notes:

        This solution was inspired by UnicodeRW.
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
                            "constructor. Make sure to include a header row")

        stringio = StringIO(csvstring.encode('utf-8'))
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
        for field, column in datadict.items():
            new_datatable[field] = column
        return new_datatable

    @classmethod
    def fromexcel(cls, path, sheet_name_or_num=0, headers=None):
        """
        Constructs a new DataTable from an Excel file.

        Specify sheet_name_or_number to load that specific sheet.

        Headers will be inferred automatically, but if you'd prefer
        to load only a subset of all the headers, pass in a list of the
        headers you'd like as `headers`.

        ---

        Alternatively, it's quite simple to:

            reader = ExcelReader('myfile.xls')
            reader.change_sheet('default')
            data = DataTable(reader)
        """
        reader = ExcelRW.UnicodeDictReader(path, sheet_name_or_num)
        return cls(reader, headers=headers)

    def __add__(self, other_datatable):
        return self.concat(other_datatable)

    def __contains__(self, fieldname):
        return fieldname in self.__data.viewkeys()

    def __delitem__(self, key):
        del self.__data[key]

    def __eq__(self, other):
        """
        Note that there is a bug (in my opinion) where two OrderedDicts
        are considered equal even if one dict has more key-value pairs
        after the initial matching set.

        The line where we compare the length of the two DataTables and
        the number of keys is meant to protect against this bug.
        """
        if not isinstance(other, DataTable):
            raise TypeError("Cannot compare DataTables with `%s` "
                            "for equality" % type(other))
        if len(self) != len(other) or len(self.fields) != len(other.fields):
            return False
        for selfrow, otherrow in izip(self, other):
            if selfrow != otherrow:
                return False
        return True

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

    def __len__(self):
        if not self.__data:
            return 0
        else:
            return len(self.__data.viewvalues().__iter__().next())

    def __repr__(self):
        return str(self)

    def __setitem__(self, fieldname, column):
        """
        Sets a column with the specified name to the specified value:

        dt['new_column'] = [1, 2, 3]

        1. If the column name doesn't exist, it will be created.
        2. If the column value provided is a tuple, it will be cast to a list.
        3. If the column value isn't a list, tuple, or array, it will
           be assumed that you're trying to set a whole column to some scalar
           value. For example:

           dt['another_column'] = True

           ... will set the entire column, for the length of the table, equal
           to `True`.
        """
        if not isinstance(column, (list, array)):
            if isinstance(column, tuple):
                column = list(column)
            else:
                column = [column] * len(self)
        if self.__data and len(column) != len(self):
            raise Exception("New column length (%s) must match length "
                            "of table (%s)" % (len(column), len(self)))
        self.__data[fieldname] = column

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.pretty

    def __print_table(self, row_delim, header_delim=None,
                      header_pad=u"", pad=u""):
        """
        row_delim         default delimiter inserted between columns of every
                          row in the table.
        header_delim      delimiter inserted within the headers. by default
                          takes the value of `row_delim`
        header_pad        put on the sides of the row of headers.
        pad               put on the sides of every row.
        """
        if header_delim is None:
            header_delim = row_delim
        num_cols = len(self.fields)
        accumulator = ((u"%s" + header_delim) * num_cols)[:-len(header_delim)]
        accumulator = ((header_pad + accumulator + header_pad + u"\n") %
                       tuple(self.fields))
        for datarow in self:
            rowstring = ((u"%s" + row_delim) * num_cols)[:-len(row_delim)]
            rowstring = (pad + rowstring + pad + u"\n") % tuple(datarow)
            accumulator += rowstring
        return accumulator[:-1]

    @property
    def html(self):
        accumulator = u"<table>"
        accumulator += u"<tr>" + u"".join([u"<th>"+field+u"</th>"
                                           for field in self.fields]) + u"</tr>"
        for datarow in self:
            accumulator += u"<tr>" + u"".join([u"<td>"+unicode(row)+u"</td>"
                                               for row in datarow]) + u"</tr>"
        return accumulator + u"</table>"

    @property
    def jira(self):
        header, row = u"||", u"|"
        return self.__print_table(row_delim=row,
                                  header_delim=header,
                                  header_pad=header,
                                  pad=row)

    # TODO: print a "prettytable" style table
    @property
    def pretty(self):
        return self.t

    @property
    def t(self):
        return self.__print_table(u"\t")

    def append(self, row):
        """
        Takes a dict, a list/tuple/generator, or a DataRow/namedtuple,
        and appends it to the "bottom" or "end" of the DataTable.

        dicts must share the same keys as the DataTable's columns.

        lists/tuples/generators are simply trusted to be in the correct order
        and of the correct type (if relevant).

        If the table being appended to is empty, the columns are inferred
        from the row being appended.

        DataRows and namedtuples' `_fields` protected class attribute is
        checked for the field names. Those are checked against the DataTable
        and then appended to the relevant columns using those field names.
        """
        if isinstance(row, dict):
            if self.fields and not set(row.keys()) == set(self.fields):
                raise Exception("Cannot append a dict to DataTable without "
                                "all keys matching (order being irrelevant).\n"
                                "dict: %s\nDataTable: %s" % (row.keys(),
                                                             self.fields))
            if not self.fields:
                for field in row.keys():
                    self.__data[field] = [row[field]]
            else:
                for field in self.fields:
                    self.__data[field].append(row[field])
        elif isinstance(row, (list, tuple, GeneratorType)):
            if isinstance(row, tuple) and hasattr(row, '_fields'):
                fieldnames = row._fields
                if self.fields and not set(fieldnames) == set(self.fields):
                    raise Exception("Cannot append a Datarow or namedtuple to "
                                    "DataTable without all fields matching "
                                    "(order being irrelevant).\n"
                                    "DataRow/namedtuple: %s\n"
                                    "DataTable: %s" % (fieldnames, self.fields))
                if not self.fields:
                    for fieldname, value in izip(fieldnames, row):
                        self.__data[fieldname] = [value]
                else:
                    for fieldname, value in izip(fieldnames, row):
                        self.__data[fieldname].append(value)
            else:
                if isinstance(row, GeneratorType):
                    row = tuple(row)
                if self.fields and not len(row) == len(self.fields):
                    raise Exception("The row being appended does not have the "
                                    "correct length. It should have a length "
                                    "of %s, but is %s" % (len(self.fields),
                                                          len(row)))
                if not self.fields:
                    raise Exception("Can't append a list/tuple/GeneratorType "
                                    "as a row if the table doesn't have "
                                    "columns defined yet.")
                # we're just going to hope that the generator's contents are
                # provided in the right order, and of the right type.
                for (_, column), element in izip(self.__data.items(), row):
                    column.append(element)
        else:
            raise Exception("Unable to append type `%s` to DataTable" %
                            type(row))

    def apply(self, func, *fields):
        """
        Applies the function, `func`, to every row in the DataTable.

        If no fields are supplied, the entire row is passed to `func`.
        If fields are supplied, the values at all of those fields
        are passed into func in that order.
        ---
        data['diff'] = data.apply(short_diff, 'old_count', 'new_count')
        """
        results = []
        for row in self:
            if not fields:
                results.append(func(row))
            else:
                if any(field not in self for field in fields):
                    for field in fields:
                        if field not in self:
                            raise Exception("Column `%s` does not exist "
                                            "in DataTable" % field)
                results.append(func(*[row[field] for field in fields]))
        return results

    def col(self, col_name_or_num):
        """
        Returns the col at index `colnum` or name `colnum`.
        """
        if isinstance(col_name_or_num, basestring):
            return self[col_name_or_num]
        elif isinstance(col_name_or_num, (int, long)):
            if col_name_or_num > len(self.fields):
                raise IndexError("Invalid column index `%s` for DataTable" %
                                 col_name_or_num)
            return self.__data[self.fields[col_name_or_num]]

    def concat(self, other_datatable, inplace=False):
        """
        Concatenates two DataTables together, as long as column names
        are identical (ignoring order). The resulting DataTable's columns
        are in the order of the table whose `concat` method was called.
        """
        if not isinstance(other_datatable, DataTable):
            raise TypeError("`concat` requires a DataTable, not a %s" %
                            type(other_datatable))

        # if the self table is empty, we can just return the other table
        # if we need to do it in place, we just copy over the columns
        if not self.fields:
            if inplace:
                for field in other_datatable.fields:
                    self[field] = other_datatable[field]
                return self
            else:
                return other_datatable
        if not other_datatable.fields:
            return self

        if set(self.fields) != set(other_datatable.fields):
            raise Exception("Columns do not match:\nself: %s\nother: %s" %
                            (self.fields, other_datatable.fields))

        if inplace:
            for field in self.fields:
                self.__data[field] = self[field] + other_datatable[field]
            return self
        else:
            new_table = DataTable()
            for field in self.fields:
                new_table[field] = self[field] + other_datatable[field]
            return new_table

    def copy(self):
        return self.fromdict(self.__data)

    def distinct(self, fieldname, key=None):
        """
        Returns the unique values seen at `fieldname`.
        """
        return tuple(unique_everseen(self[fieldname], key=key))

    def groupby(self, *groupfields):
        """
        Groups rows in this table according to the unique combinations of
        `groupfields` combined.
        """
        return GroupbyTable(self, groupfields)

    # TODO: this is a placeholder and only does a very simple left join.
    def join(self, right_table, on):
        keymap = {}
        for row in right_table:
            if row[on] in keymap:
                keymap[row[on]].append(row)
            else:
                keymap[row[on]] = [row]
        new_table = []
        for row in self:
            if row[on] in keymap:
                left_dict = dict(row.items())
                for item in keymap[row[on]]:
                    left_dict_copy = left_dict.copy()
                    left_dict_copy.update(dict(item.items()))
                    new_table.append(left_dict_copy)
        return DataTable(new_table)

    def mask(self, masklist):
        """
        `masklist` is an array of Bools or equivalent.

        This returns a new DataTable using only the rows that were True
        (or equivalent) in the mask.
        """
        if not hasattr(masklist, '__len__'):
            masklist = tuple(masklist)

        if len(masklist) != len(self):
            raise Exception("Masklist length (%s) must match length "
                            "of DataTable (%s)" % (len(masklist), len(self)))

        new_datatable = DataTable()
        for field in self.fields:
            new_datatable[field] = list(compress(self[field], masklist))
        return new_datatable

    def mutapply(self, function, fieldname):
        """
        Applies `function` in-place to the field name specified.

        In other words, `mutapply` overwrites column `fieldname`
        ith the results of applying `function` to each element of that column.
        """
        self[fieldname] = self.apply(function, fieldname)

    def rename(self, old_fieldname, new_fieldname):
        """
        Renames a specific field, and preserves the underlying order.
        """
        if old_fieldname not in self:
            raise Exception("DataTable does not have field `%s`" %
                            old_fieldname)

        if not isinstance(new_fieldname, basestring):
            raise ValueError("DataTable fields must be strings, not `%s`" %
                             type(new_fieldname))

        if old_fieldname == new_fieldname:
            return

        new_names = self.fields
        location = new_names.index(old_fieldname)
        del new_names[location]
        new_names.insert(location, new_fieldname)
        self.fields = new_names

    def reorder(self, fields_in_new_order):
        """
        Pass in field names in the order you wish them to be swapped.
        """
        if not len(fields_in_new_order) == len(self.fields):
            raise Exception("Fields to reorder with are not the same length "
                            "(%s) as the original fields (%s)" %
                            (len(fields_in_new_order), len(self.fields)))
        if not set(fields_in_new_order) == set(self.fields):
            raise Exception("Fields to reorder with should be the same "
                            "as the original fields")
        new = OrderedDict()
        for field in fields_in_new_order:
            new[field] = self.__data[field]
        self.__data = new

    def row(self, rownum):
        """
        Returns the row at index `rownum`.
        ---
        Note that the DataRow object returned that represents the data row
        is constructed on the fly and is a just a shallow copy of
        the underlying data that does not update dynamically.
        """
        if rownum > len(self):
            raise IndexError("Invalid row index `%s` for DataTable" % rownum)
        return datarow_constructor(self.fields)([self[field][rownum]
                                                 for field in self.fields])

    def sample(self, num):
        """
        Returns a new table with rows randomly sampled.

        We create a mask with `num` True bools, and fill it with False bools
        until it is the length of the table. We shuffle it, and apply that
        mask to the table.
        """
        if num > len(self):
            return self.copy()
        elif num < 0:
            raise IndexError("Cannot sample a negative number of rows "
                             "from a DataTable")

        random_row_mask = ([True] * num) + ([False] * (len(self) - num))
        shuffle(random_row_mask)

        sampled_table = self.mask(random_row_mask)
        random_col_name = 'random_sorting_column'
        while random_col_name in sampled_table:
            random_col_name = '%030x' % randrange(16**30)
        sampled_table[random_col_name] = [random()
                                          for _ in xrange(len(sampled_table))]
        sampled_table.sort(random_col_name, inplace=True)
        del sampled_table[random_col_name]
        return sampled_table

    def sort(self, fieldname, key=lambda x: x, desc=False, inplace=False):
        """
        This matches Python's built-in sorting signature closely.

        By default, a new DataTable will be returned and the original will
        not be mutated. If preferred, specify `inplace=True` in order to
        mutate the original table. Either way, a reference to the relevant
        table will be returned.
        """
        try:
            field_index = tuple(self.fields).index(fieldname)
        except ValueError:
            raise ValueError("Sorting on a field that doesn't exist: `%s`" %
                             fieldname)

        data_cols = izip(*sorted(izip(*[self.__data[field]
                                        for field in self.fields]),
                                 key=lambda row: key(row[field_index]),
                                 reverse=desc))

        target_table = self if inplace else DataTable()

        for field, data_col in izip(self.fields, data_cols):
            target_table[field] = list(data_col)

        # Note that sorting in-place still returns a reference
        # to the table being sorted, for convenience.
        return target_table

    def where(self, fieldname, value, negate=False):
        """
        Returns a new DataTable with rows only where the value at
        `fieldname` == `value`.
        """
        if negate:
            return self.mask([elem != value
                              for elem in self[fieldname]])
        else:
            return self.mask([elem == value
                              for elem in self[fieldname]])

    def wherefunc(self, func, negate=False):
        """
        Applies a function to an entire row and filters the rows based on the
        boolean output of that function.
        """
        if negate:
            return self.mask([not func(item) for item in self])
        else:
            return self.mask([func(item) for item in self])

    def wherein(self, fieldname, collection, negate=False):
        """
        Returns a new DataTable with rows only where the value at
        `fieldname` is contained within `collection`.
        """
        if negate:
            return self.mask([elem not in collection
                              for elem in self[fieldname]])
        else:
            return self.mask([elem in collection
                              for elem in self[fieldname]])

    def wheregreater(self, fieldname, value):
        """
        Returns a new DataTable with rows only where the value at
        `fieldname` > `value`.
        """
        return self.mask([elem > value for elem in self[fieldname]])

    def whereless(self, fieldname, value):
        """
        Returns a new DataTable with rows only where the value at
        `fieldname` < `value`.
        """
        return self.mask([elem < value for elem in self[fieldname]])

    def wherenot(self, fieldname, value):
        """
        Logical opposite of `where`.
        """
        return self.where(fieldname, value, negate=True)

    def wherenotfunc(self, func):
        """
        Logical opposite of `wherefunc`.
        """
        return self.wherefunc(func, negate=True)

    def wherenotin(self, fieldname, value):
        """
        Logical opposite of `wherein`.
        """
        return self.wherein(fieldname, value, negate=True)

    def writecsv(self, path, delimiter=","):
        writer = UnicodeRW.UnicodeWriter(open(path, 'wb'),
                                         self.fields,
                                         delimiter=delimiter,
                                         lineterminator=u"\n")
        writer.writerow(self.fields)
        writer.writerows(self)
        writer.close()

    def writexlsx(self, path, sheetname="default"):
        """
        Writes this table to an .xlsx file at the specified path.

        If you'd like to specify a sheetname, you may do so.

        If you'd like to write one workbook with different DataTables
        for each sheet, import the `excel` function from acrylic. You
        can see that code in `utils.py`.

        Note that the outgoing file is an .xlsx file, so it'd make sense to
        name that way.
        """
        writer = ExcelRW.UnicodeWriter(path)
        writer.set_active_sheet(sheetname)
        writer.writerow(self.fields)
        writer.writerows(self)
        writer.save()

    def __iter__(self):
        datarow = datarow_constructor(self.fields)
        for values in izip(*[self.__data[field] for field in self.fields]):
            yield datarow(values)


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


def validate_fields(fields):
    if not all([isinstance(field, basestring) for field in fields]):
        raise Exception("Column headers/fields must be strings")
