# coding: utf-8
from datatable import DataTable
from random import random, sample

@profile
def main():
    data = DataTable.fromcsv('Audience 25-34 USA Handles and IDs.csv', delimiter="\t")
    rands = (random() for _ in xrange(len(data)))
    data.fields = [unicode(field) for field in data.fields]
    data[u'rand'] = rands
    rands2 = []
    for row in data:
        item = row[u'rand']
        rands2.append(item)
    datatup = tuple([i for i in data])
    s = sample(datatup, 100)
    s = list(s)
    del s
    del data

if __name__ == '__main__':
    main()