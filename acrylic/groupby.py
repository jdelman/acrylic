# coding: utf-8
from collections import OrderedDict
from itertools import izip

import datatable


class GroupbyTable(object):
    """
    A GroupbyTable is returned as a result of calling `.groupby` on a
    DataTable object. This table contains a mapping of the groupby keys
    to a group of rows corresponding to those keys.

    Chain calls to the `.agg` method, passing aggregation functions in as
    arguments, in order to add new columns with information derived from
    these groups.

    This returns a new DataTable with a 'department' column and a 'max(salary)'
    column:

    max_salaries_by_department = (data.groupby('department')
                                      .agg(max, 'salary')
                                      .collect())

    The `collect()` is necessary to finally cast the GroupbyTable into a
    DataTable. The resulting DataTable has no "memory" of the GroupbyTable
    from which it was made.

    Here is another example:

    def most_recent_price(price_and_timestamps):
        return max(price_and_timestamps, key=lambda row: row[1])[0]

    sales = (orders.groupby('productid')
                   .agg(sum, 'sale_price')  # col name will be "sum(sale_price)"
                   .agg(len, name='total_orders'),
                   .agg(most_recent_price, 'sale_price', 'timestamp')
                   .collect())

    """

    def __init__(self, datatable_instance, groupfields):
        if not isinstance(datatable_instance, datatable.DataTable):
            raise Exception("Must group a DataTable instance.")
        if len(groupfields) == 0:
            raise Exception("Must pass in at least one groupfield.")
        self.__key_to_group_map = OrderedDict()
        self.__groupfields = groupfields
        self.__grouptable = datatable.DataTable()
        self.__lambda_num = 0

        self.__initialize_groupings(datatable_instance, groupfields)

    def __len__(self):
        return len(self.__key_to_group_map)

    def __initialize_groupings(self, root_data, groupfields):
        if len(groupfields) > 1:
            get_key = lambda datarow: tuple([datarow[groupfield]
                                             for groupfield in groupfields])
        else:
            get_key = lambda datarow: datarow[groupfields[0]]

        for row in root_data:
            key = get_key(row)
            if key in self.__key_to_group_map:
                self.__key_to_group_map[key].append(row)
            else:
                self.__key_to_group_map[key] = [row]
        self.__grouptable['groupkey'] = self.__key_to_group_map.keys()

    def agg(self, func, *fields, **name):
        """
        Calls the aggregation function `func` on each group in the GroubyTable,
        and leaves the results in a new column with the name of the aggregation
        function.

        Call `.agg` with `name='desired_column_name' to choose a column
        name for this aggregation.
        """
        if name:
            if len(name) > 1 or 'name' not in name:
                raise TypeError("Unknown keyword args passed into `agg`: %s\n"
                                % name)
            name = name.get('name', None)

        if name is not None:
            name = name
        elif func.__name__ == '<lambda>':
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

    def aggregate(self, func, *fields):
        return self.agg(func, *fields)

    aggregate.__doc__ = agg.__doc__

    def collect(self):
        """
        After adding the desired aggregation columns, `collect`
        finalizes the groupby operation by converting the
        GroupbyTable into a DataTable.

        The first columns of the resulting table are the groupfields,
        followed by the aggregation columns specified in preceeding
        `agg` calls.
        """
        # The final order of columns is determined by the
        # group keys and the aggregation columns
        final_field_order = list(self.__groupfields) + self.__grouptable.fields

        # Tansform the group key rows into columns
        col_values = izip(*self.__grouptable['groupkey'])

        # Assign the columns to the table with the relevant name
        for groupfield, column in izip(self.__groupfields, col_values):
            self.__grouptable[groupfield] = column

        # Reorder the columns as defined above
        self.__grouptable.reorder(final_field_order)

        del self.__grouptable['groupkey']
        return self.__grouptable
