# coding: utf-8

from prettytable import PrettyTable


def pretty_table(datatable):
    pt = PrettyTable(datatable.fields)
    for row in datatable:
        pt.add_row(row.values())
    return pt.get_string()
