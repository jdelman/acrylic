# coding: utf-8

import datatable

from collections import OrderedDict


class GroupByTable(object):

    def __init__(self, datatable_instance, groupfields):
        if not isinstance(datatable_instance, datatable.DataTable):
            raise Exception("Must group a DataTable instance.")
        if len(groupfields) == 0:
            raise Exception("Must pass in at least one groupfield.")
        self.__key_to_group_map = OrderedDict()
        self.__grouptable = datatable.DataTable()
        self.__lambda_num = 0

        self.__initialize_groupings(datatable_instance, groupfields)

    def __initialize_groupings(self, root_data, groupfields):
        if len(groupfields) > 1:
            get_key = lambda row: tuple([row[groupfield]
                                         for groupfield in groupfields])
        else:
            get_key = lambda row: row[groupfields[0]]

        for row in root_data:
            key = get_key(row)
            if key in self.__key_to_group_map:
                self.__key_to_group_map[key].append(row)
            else:
                self.__key_to_group_map[key] = [row]
        self.__grouptable['groupkey'] = self.__key_to_group_map.keys()

    def __call__(self, func, *fields):
        if func.__name__ == '<lambda>':
            name = "lambda%04d" % self.__lambda_num
            self.__lambda_num += 1
        else:
            name = func.__name__

        aggregated_column = []

        if len(fields) > 1:
            name += "(%s)" % ','.join(fields)
            for groupkey in self.__grouptable['groupkey']:
                agg_data = [tuple([row[field] for field in fields])
                            for row in self.__key_to_group_map[groupkey]]
                aggregated_column.append(func(agg_data))
        elif len(fields) == 1:
            field = fields[0]
            name += "(%s)" % field
            for groupkey in self.__grouptable['groupkey']:
                agg_data = [row[field]
                            for row in self.__key_to_group_map[groupkey]]
                aggregated_column.append(func(agg_data))
        else:
            name += "()"
            for groupkey in self.__grouptable['groupkey']:
                agg_data = self.__key_to_group_map[groupkey]
                aggregated_column.append(func(agg_data))

        self.__grouptable[name] = aggregated_column
        return self

    def __len__(self):
        return len(self.__key_to_group_map)

    def collect(self):
        return self.__grouptable
