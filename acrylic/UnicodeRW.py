# coding: utf-8

from collections import OrderedDict

import csv
import codecs
import cStringIO


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self._encoding = encoding

        # Work around accidentally including a BOM.
        first_line = f.next()
        if len(first_line) > 3 and first_line[:3] == "\xef\xbb\xbf":
            f.reader.seek(3)
        else:
            f.reader.seek(0)

        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()

        # \x85 is the alternative line-break: …
        # It confuses Python into breaking the line prematurely.
        temp_row_ending = row[-1].decode(self._encoding)
        while u"\x85" in temp_row_ending:

            # When the line has a delimiter or the quotechar,
            # it means it has been surrounded by quotechars,
            # so the \x85 won't break it.
            if (self.reader.dialect.delimiter in temp_row_ending
               or self.reader.dialect.quotechar in temp_row_ending):
                break

            # Sometimes the \x85 was at the end of the line anyway.
            next_row = self.reader.next()
            if not next_row:
                break

            # We need to reconstruct the broken row.
            temp_row_ending = temp_row_ending.replace(u"\x85", u"")
            temp_row_ending += next_row[0]
            row[-1] = temp_row_ending.encode(self._encoding)
            if len(next_row) > 1:
                row += next_row[1:]

            # We loop again because it's possible the row is broken
            # multiple times.
            temp_row_ending = row[-1].decode(self._encoding)

        return [unicode(s, self._encoding) for s in row]

    def __iter__(self):
        return self


class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self,
                 f,
                 dialect=csv.excel,
                 encoding="utf-8",
                 bom=True,
                 **kwds):

        if 'quoting' not in kwds:
            kwds['quoting'] = csv.QUOTE_ALL

        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        # Add BOM to the lead of every new file.
        if bom:
            f.write(codecs.BOM_UTF8)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") if isinstance(s,str)
                              else unicode(s).encode("utf-8")
                              for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

    def close(self):
        self.stream.close()


class UnicodeDictWriter(object):
    """
    A CSV writer that writes dicts in the order specified by fieldnames.
    """
    def __init__(self,
                 f,
                 fieldnames,
                 dialect=csv.excel,
                 encoding='utf-8',
                 **kwds):
        self._writer = UnicodeWriter(f, dialect=dialect, encoding=encoding,
                                     **kwds)
        self._fieldnames = fieldnames

    def writeheaders(self):
        self._writer.writerow(self._fieldnames)

    def writerow(self, row):
        row_builder = []
        for fieldname in self._fieldnames:
            cell = row.get(fieldname, "")
            row_builder.append(cell)
        self._writer.writerow(row_builder)

    def writerows(self, rows):
        for row_num, row in enumerate(rows):
            try:
                self.writerow(row)
            except Exception:
                print "Crashed on row %d." % row_num
                raise

    def close(self):
        self._writer.close()


class UnicodeDictReader(object):
    """
    A CSV reader that reads rows as dicts where keys are the column headers.
    Make sure that the file you're reading has headers.
    """
    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        self._reader = UnicodeReader(f,
                                     dialect=dialect,
                                     encoding=encoding,
                                     **kwds)
        headers = self._reader.next()
        self._index_to_header = {headers.index(header): header
                                 for header in headers}

    def next(self):
        row = self._reader.next()
        row_dict = OrderedDict([(self._index_to_header[i], cell)
                                for i, cell in enumerate(row)])
        return row_dict

    def __iter__(self):
        return self