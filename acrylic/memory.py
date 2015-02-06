# coding: utf-8
from datatable import DataTable
from random import random, randint, sample
#from utils import sample

import time

# @profile
def main():
    data = DataTable.fromcsv('Audience 25-34 USA Handles and IDs.csv', delimiter="\t")
    rands = (random() for _ in xrange(len(data)))
    data.fields = [unicode(field) for field in data.fields]
    data[u'rōnd'] = rands
    rands2 = []
    for row in data:
        item = row[u'rōnd']
        rands2.append(item)
    import pdb; pdb.set_trace()
    s = sample(tuple([i for i in data]), 100)
    s = list(s)
    del s
    del data

if __name__ == '__main__':
    main()