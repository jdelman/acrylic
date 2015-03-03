# coding: utf-8

from itertools import chain
from pyexcelerate import Workbook


def excel(path, datatables, sheetnames=None):
    wb = Workbook()
    if sheetnames is None:
        sheetnames = ["datatable_%02d" % i for i in range(1, len(datatables))]
    else:
        if len(sheetnames) != len(datatables):
            raise Exception("`sheetnames` is not the same "
                            "length as `datatables`: %s vs %s" %
                            (len(sheetnames), len(datatables)))
    for datatable, sheetname in zip(datatables, sheetnames):
        wb.new_sheet(sheetname, data=chain([datatable.fields], datatable))
    wb.save(path)
