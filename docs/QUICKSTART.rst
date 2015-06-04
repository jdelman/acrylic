Acrylic Guide
=============

Constructing a DataTable
------------------------

A DataTable can be constructed from:

1. An iterable of dictionaries, where the keys are the column names. (Use an ``OrderedDict``, pass in ``headers=`` during construction, or reorder columns afterward with ``.reorder`.)
2. An iterable of ``list``-like rows. (Either pass in the headers as the first ``list``-like element, or pass them in via ``headers=``.)
3. A string representing data in CSV-form or similar.
4. A CSV file.
5. An Excel file.

DataTable fields (column names, or headers) must be strings:

.. code:: python

    data = DataTable([['name', 'zipcode', 'color'],
                      ['maria', 33134, 'purple'],
                      ['carlos', 07047, 'yellow'],
                      ['abelardo', 60153, 'red']])
                      
    # equivalent
    data = DataTable([{'name': 'maria', 'zipcode': 33134, 'color': 'purple'},
                      {'name': 'carlos', 'zipcode': 07047, 'color': 'yellow'},
                      {'name': 'abelardo', 'zipcode': 60153, 'color': 'red'}]
    data.reorder(['name', 'zipcode', 'color'])

The most performant way to create a DataTable is through the ``.fromdict``
alternative constructor, which can take an OrderedDict. This is the code:

.. code:: python

    @classmethod
    def fromdict(cls, datadict):
        new_datatable = cls()
        for field, column in datadict.items():
            new_datatable[field] = column
        return new_datatable

Reading and Writing Files
-------------------------

*********************
CSV or TSV-style Data
*********************

Read data from CSV or TSV:

.. code:: python

    csv_data = DataTable.fromcsv('myfile.csv')
    tsv_data = DataTable.fromcsv('myfile.tsv', delimiter="\t")

Construct a DataTable from a copy-pasted CSV Unicode literal:

.. code:: python

    data = DataTable.fromcsvstring(ur'''a,b,c
    d,e,f
    g,h,i''')

.. note::

    You should almost always prefix your triple-quoted string with ``ur`` (as in ``ur"""string contents"""``) if it's been copy-pasted from Excel. If you're copying something printed from Python (using the ``print`` statement), also append ``ur``. If you're copying something that was simply dumped to the screen (like just typing ``objname`` at the REPL and hitting "enter" without the ``print`` statement, which only invokes ``__repr__`` on the object), you should prefix only with ``u``.

.. note::

    Do not try to line up your copy-pasted CSV data for a visual indent - it will just add excessive whitespace to the left side of the first column.

*****
Excel
*****

Read data from Excel:

.. code:: python

    excel_data = DataTable.fromexcel('myfile.xls', sheet_name_or_number='default')

Write data to Excel:

.. code:: python

    data.writexlsx('myoutput.xlsx')

Write many DataTables to Excel:

.. code:: python

    tables = (Table_one, Table_two)
    excel('output.xls', tables, sheetnames=("one", "two"))

Sheet names will default to "datatable_01", etc. if ``sheetnames`` isn't provided.

*****************************
Iterating through a DataTable
*****************************

It is possible to iterate through the DataTable row by row, although it is 
somewhat less efficient. Each row is a ``DataRow`` instances, and 
is immutable.

Don't alter the DataTable during iteration, or you will be in a state of sin.

^^^^^^^^^^^^^^
DataRow Object
^^^^^^^^^^^^^^

Rows are a special class called a ``DataRow``, inspired by ``namedtuple``. 
It is very lightweight (for a Python object), and is essentially a ``tuple`` 
with a few additions:

    - It has a ``.items()`` method for iterating through column names and values like you would with a ``dict``.
    - You can access values like this: ``row['column_name']``, just like a ``dict``.
    - You can also default-access with ``.get('column_name', default_value)``.

Being a tuple, you can slice (e.g., ``row[0:20:2]``), unpack during iteration,
and so on.

.. code:: python

    for row in data:
        for header, value in row.items():
            # do something

If you're blessed with a small number of columns, why not unpack directly:

.. code:: python

    for name, address, phone_number in data:
        # do something

Don't try to iterate through the table and mutate each row:

.. code:: python

    for row in data:
        # TypeError because DataRows are immutable
        row['doubled_val'] = row['val']**2

Instead, you could do could construct the column separately, and 
then insert it into the table:

.. code:: python

    double_val = []
    for row in table:
        double_val.append(row['val']**2)
    data['double_val'] = double_val

Or, better in most cases, use ``apply`` or ``mutapply`` - which are 
described in the next section.

Accessing Data
--------------

*******
Columns
*******

Fetch a column:

.. code:: python

    my_column = data['column_name']

Fetch a row, and the value at a column:

.. code:: python

    # preferred
    value = data['column_name'][5]  # col, row

These ways also work for fetching a specific cell:

.. code:: python

    some_row = data[5]  # fetches row at index 5
    value = some_row['column_name']

    # equivalent, assuming ``column_name`` is the third column, zero-indexed
    value = data[5][2]  # row, col

    # equivalent
    value = data.row(5)['column_name']

    # equivalent
    value = data.col('column_name')[5]

Distinct (unique) values from a column:

.. code:: python

    brands = data.distinct('brands')

*******
Slicing
*******

Slicing a table, like ``data[4:34:3]``, gracefully handles out of bounds
slicings and produces a shallow copy - just like a normal Python ``list`` does.

Mutating a DataTable
--------------------

***************
Adding a Column
***************

Columns can be added simply by assigning any list to a column name:

.. code:: python

    data['squares'] = [i**2 for i in range(len(data))]

Columns can also be added by applying a function to a column and setting 
that result to a new column.

.. code:: python

    data['diff'] = data.apply(lambda row: row['new_count']/row['old_count'])

You may specify which columns you want passed into the function with
more arguments, as below. Otherwise, the entire ``DataRow`` is passed into the
function as the only argument.

.. code:: python

    data['diff'] = data.apply(short_diff, 'old_count', 'new_count')

If you want to set a whole column to some "scalar"-like value
(something that isn't a ``list``, ``array``, or ``tuple``), here is some sugar:

.. code:: python

    data['five'] = 5
    data['notes'] = 'Unknown'

******************
Replacing a Column
******************

As shown above, you can assign the result of an ``apply`` to a column,
overwriting it.

To mutate a column in place, use ``mutapply``:

.. code:: python

    data.mutapply(str.lower, 'name')

*************
Concatenating
*************

Call ``concat`` to concatenate two DataTables, top to bottom. Both tables must 
have the same column names (or one may be empty).

.. code:: python

    concat_table = first_table.concat(second_table)

    # equivalent
    concat_table = first_table + second_table

*********
Appending
*********

TODO

*******
Sorting
*******

For multi-priority sorting, simply chain multiple sortings in increasing 
order of importance.

.. code:: python

    data = data.sort('diff', desc=True).sort('description').sort('searchterm')

Sorting can be done in-place with the ``inplace`` argument. A reference to the 
original, now mutated DataTable is returned for convenience.

.. code:: python

    data.sort('randnum', inplace=True)

****************
Renaming Columns
****************

.. code:: python

    data.rename('diff', 'diff percentage')

Or, to rename many columns:

.. code:: python

    data.fields = [field.lower() for field in fields]

******************
Reordering Columns
******************

The fields passed in must be identical in content to the current fields.
The columns will be swapped to match their order.

.. code:: python

    data.reorder(sorted(data.fields))

Filtering
---------

A family of ``where*`` functions exist to make filtering straight-forward and readable.

- ``where``, checking for equality - ``==``.
- ``wheregreater``, checking for "greater than" - ``>``.
- ``whereless``, checking for "less than" - ``<``.
- ``wherein``, checking for membership - ``in``.
- ``wherefunc``, using a function which returns a ``bool``-like object to filter rows.

Examples:

.. code:: python

    positive_sentences = data.where('sentiment', 'positive')

    cheap_products = inventory.whereless('price', 30.0)

``wherein`` can also take a ``set`` or ``tuple`` to check multiple criteria at once - 
think of this like an ``or``.

.. code:: python

    positive_and_negative_sentences = data.wherein('sentiment', ('positive', 'negative'))

Since all ``where*`` methods return a DataTable instance, we can chain together calls
like below:

.. code:: python

    high_agreement_positives = data.where('sentiment', 'positive')
                                   .wheregreater('agreement', 0.75)
    true_positives = high_agreement_positives.where('answer', 'positive')
    positive_precision = len(true_positives)/len(high_agreement_positives)

``where`` can take a ``negate=True`` argument to negate whatever condition has been 
expressed (equivalent to ``wherenot``).

.. code:: python 

    sentiment_bearing = data.wherein('answer', ('neutral', 'not_sure'), negate=True)

    # equivalent
    sentiment_bearing = data.wherenotin('answer', ('neutral', 'not_sure'))

``wherefunc`` takes one argument: a function that returns a boolean when passed 
a row of data (an immutable ordered dict-like object).

.. code:: python

    def conditional_filter(datarow):
        if datarow['state'] == 'CA' and datarow['penalty'] > 100:
            return True
        elif datarow['penalty'] > 0:
            return True
        return False

    result = data.wherefunc(conditional_filter)

You can also create a filtered DataTable by passing an iterable of ``bool`` to 
the ``mask`` method.

Printing
--------

By default, printing a DataTable returns a tab-separated string
representation of the table. You can also print a few other common formats
using special properties of the DataTable object:

.. code:: python

    print data.jira    # Jira-style formatting, "|" separated
    print data.html    # HTML table
    print data.pretty  # a "pretty table" style table for the console

Groupby
-------

**TODO**

.. code:: python

    data.groupby

Join
----

**TODO**
