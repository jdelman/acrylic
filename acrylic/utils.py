# coding: utf-8

import ExcelRW


def excel(path, datatables, sheetnames=None):
    writer = ExcelRW.UnicodeDictWriter(path)
    if sheetnames is None:
        sheetnames = ["datatable_%02d" % i for i in range(1, len(datatables))]
    else:
        if len(sheetnames) != len(datatables):
            raise Exception("`sheetnames` is not the same "
                            "length as `datatables`: %s vs %s" %
                            (len(sheetnames), len(datatables)))
    for datatable, sheetname in zip(datatables, sheetnames):
        writer.set_active_sheet(sheetname, datatable.fields)
        writer.writeheaders()
        writer.writerows(datatable)
    writer.save()
