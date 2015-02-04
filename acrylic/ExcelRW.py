# coding: utf-8
from collections import OrderedDict

import xlrd
import xlwt


class UnicodeReader(object):

    def __init__(self, f, sheet_name_or_num=0):
        self.__wb = xlrd.open_workbook(filename=f)
        self._sheet, self.__row_num = None, 0
        self.change_sheet(sheet_name_or_num)

    def change_sheet(self, sheet_name_or_num):
        if isinstance(sheet_name_or_num, int):
            self._sheet = self.__wb.sheet_by_index(sheet_name_or_num)
        elif (isinstance(sheet_name_or_num, str)
              or isinstance(sheet_name_or_num, unicode)):
            self._sheet = self.__wb.sheet_by_name(sheet_name_or_num)
        else:
            reason = "Must enter either sheet name or sheet number."
            raise Exception(reason)
        self.__row_num = 0

    def get_row(self, num):
        row = [item.value for item in self._sheet.row(num)]
        return row

    def get_col(self, num):
        col = [item.value for item in self._sheet.col(num)]
        return col

    def nsheets(self):
        return self.__wb.nsheets

    def _next(self):
        try:
            row = []
            for item in self._sheet.row(self.__row_num):
                row.append(item)
        except IndexError:
            raise StopIteration

        self.__row_num += 1
        return [cell.value if hasattr(cell, 'value') else cell for cell in row]

    def next(self):
        return self._next()

    def __iter__(self):
        return self


class UnicodeWriter(object):

    def __init__(self, filename):
        if not (isinstance(filename, str) or isinstance(filename, unicode)):
            reason = ("UnicodeWriter requires a filename string"
                      " and not an open file.")
            raise Exception(reason)

        self.__wb = xlwt.Workbook()
        self.__active_sheet = None
        self.__active_sheet_name = None
        self.__row_num = 0
        self.__sheets = {}

        self.filename = filename

    def set_active_sheet(self, name):
        # Save the current sheet again.
        self.__sheets[self.__active_sheet_name] = (self.__active_sheet,
                                                   self.__row_num)

        if name not in self.__sheets:
            self.__sheets[name] = (self.__wb.add_sheet(name), 0)

        self.__active_sheet_name = name
        self.__active_sheet, self.__row_num = self.__sheets[name]

    def writerow(self, row):
        if not self.__active_sheet:
            self.set_active_sheet("default")

        for col, cell in enumerate(row):
            self.__active_sheet.write(self.__row_num, col, cell)

        self.__row_num += 1

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def save(self):
        self.__wb.save(self.filename)


class UnicodeDictReader(UnicodeReader):

    def __init__(self, filename, sheet_name_or_num=0):
        super(UnicodeDictReader, self).__init__(filename, sheet_name_or_num)
 
    def __set_headers(self):
        self.__row_num = 0
        headers = self._next()
 
        self._index_to_header = OrderedDict()
        for header in headers:
            self._index_to_header[headers.index(header)] = header
 
        self._header_indexes = sorted(self._index_to_header.keys())
 
        if range(len(headers)) != self._header_indexes:
            raise Exception("There appear to be hidden or 'extra'"
                            "columns in your *.xls file. This is "
                            "what ExcelRW sees:\n%s" % unicode(headers))
 
    def change_sheet(self, sheet_name_or_num):
        super(UnicodeDictReader, self).change_sheet(sheet_name_or_num)
        self.__set_headers()

    def next(self):
        """
        Currently, this code breaks when it encounters a file with hidden
        headers, so the code below is never fully taken advantage of.
        If you'd prefer to read *.xls files ignoring hidden columns,
        then merely remove the exception built into the constructor.
        """
        row = self._next()
        row_dict = OrderedDict([(self._index_to_header[i], cell)
                                for i, cell in zip(self._header_indexes, row)])
        return row_dict

    def __iter__(self):
        return self


class UnicodeDictWriter(object):
    """
    A Excel writer that writes dicts in the order specified by fieldnames.

    Don't forget to call .save()!
    """
    def __init__(self, filename):
        self._writer = UnicodeWriter(filename)
        self._cache = {}
        self._fieldnames = None

    def set_active_sheet(self, name, fieldnames):
        if name not in self._cache:
            self._writer.set_active_sheet(name)
            self._fieldnames = fieldnames
            self._cache[name] = fieldnames
        else:
            if self._cache[name] != fieldnames:
                values = (name, self._cache[name], fieldnames)
                raise Exception("Already begun writing to %s "
                                "with fieldnames %s. Cannot resume writing "
                                "with fieldnames %s." % values)
            # in the case that the sheet name is in the cache
            # and the fieldnames are the same as they were
            # we change the active sheet and change the fieldnames
            else:
                self._writer.set_active_sheet(name)
                self._fieldnames = fieldnames

    def writeheaders(self):
        self._writer.writerow(self._fieldnames)

    def writerow(self, row):
        if not self._fieldnames:
            raise Exception("Fieldnames (headers) not defined.")

        row_builder = []
        for fieldname in self._fieldnames:
            try:
                cell = row[fieldname]
            except KeyError:
                row_builder.append('')
                # raise Exception("Fieldname '{}' does not exist.".format(
                #     fieldname))
            else:
                row_builder.append(cell)
        self._writer.writerow(row_builder)

    def writerows(self, rows):
        for row_num, row in enumerate(rows):
            try:
                self.writerow(row)
            except Exception as e:
                print "Crashed on row %d." % row_num
                print "Here is the row:"
                print row
                raise e

    def save(self):
        self._writer.save()
