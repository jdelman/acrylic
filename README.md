# Acrylic 0.1.1

## Construction

A DataTable can always be constructed from a list of dictionaries,
where the keys are the column names, or a list of lists,
where the first list contains the column names.

If the first list doesn't contain the column names, you can pass in a
`headers=` argument to the constructor.

If you use `OrderedDict` instead of a standard dictionary,
column order will be preserved (and based off of the first row).
Otherwise, the order will be lost - but you can always reorder columns later.

DataTable fields (also known as column names, or headers) must be strings.

```python
data = DataTable([['name', 'zipcode', 'favcolor'],
                  ['maria', 33134, 'purple'],
                  ['carlos', 07047, 'yellow'],
                  ['abelardo', 60153, 'red']])
                  
# equivalent
data = DataTable([{'name': 'maria', 'zipcode': 33134, 'favcolor': 'purple'},
                  {'name': 'carlos', 'zipcode': 07047, 'favcolor': 'yellow'},
                  {'name': 'abelardo', 'zipcode': 60153, 'favcolor': 'red'}]
data.reorder(['name', 'zipcode', 'favcolor'])
```

The most performant way to create a DataTable is through the `.fromdict`
alternative constructor, which can take an OrderedDict. This is the code: 

```python
@classmethod
def fromdict(cls, datadict):
    new_datatable = cls()
    for field, column in datadict.items():
        new_datatable[field] = column
    return new_datatable
```

## Reading and Writing

### Read data from Excel:

```python
data = DataTable.fromexcel('myfile.xls', sheet_name_or_number='default')
```

### Read data from CSV:

```python
data = DataTable.fromcsv('myfile.xls')
```

### Read data from a copy-pasted CSV Unicode literal:

Note that you should almost always prefix your triple-quoted string with `ur` 
(as in `ur"""string contents"""`) if it's been copy-pasted from Excel. 
If you're copying something printed from Python (using the `print` statement), 
also append `ur`. If you're copying something that was simply dumped to the 
screen (like just typing `objname` at the REPL and hitting "enter" without the 
`print` statement, which only invokes `__repr__` on the object), you should 
prefix only with `u`.

Also, do not try to line up your copy-pasted CSV data for a visual indent. 
That will just add tons of whitespace to the left side of the first column.

```python
data = DataTable.fromcsv(ur'''a,b,c
d,e,f
g,h,i''')
```

### Write data to Excel:

```python
data.writexlsx('myoutput.xlsx')
```
### Write many DataTables to Excel:

`sheetnames` is optional. Sheet names will default to "datatable_01", etc. if 
it isn't provided.

```python
tables = [Table_one, Table_two]
excel('output.xls', tables, sheetnames=("one", "two"))
```

## Accessing Data

Fetch a column:

```python
my_column = data['column_name']
```

Fetch a row, and the value at a column:

```python
# preferred
value = data['column_name'][5]  # col, row
```

These ways also work for fetching a specific cell:

```python
some_row = data[5]  # fetches row at index 5
value = some_row['column_name']

# equivalent, assuming `column_name` is the third column, zero-indexed
value = data[5][2]  # row, col

# equivalent
value = data.row(5)['column_name']

# equivalent
value = data.col('column_name')[5]
```

Distinct (unique) values from a column:

```python
brands = data.distinct('brands')
```

## DataRow Object

Rows are a special class called a `DataRow`, inspired by `namedtuple`. It is
very lightweight (for a Python object), and is essentially a `tuple` with
two additions:

- It has a `.items()` method for iterating through column names and 
values like you would with a `dict`.
- You can access values like this: `row['column_name']`, just like
a `dict`.

Being a tuple, you can slice (e.g., `row[0:20:2]`), unpack during iteration,
and so on. 

## Manipulating a DataTable

### Iterating

It is possible to iterate through the DataTable row by row, although it is 
not especially efficient, and the rows are immutable.
 
Column order is preserved. Don't alter the DataTable during iteration, or you 
will be in a state of sin.

```python
for row in data:
    for header, value in row.items():
        # do something
```

If you're blessed with a small number of columns, why not:

```python
for name, address, phone_number in data:
    # do something
```

**Don't** do this:

```python
for row in data:
    # TypeError because DataRows are immutable
    row['doubled_val'] = row['val']**2
```

Instead, you could do this:

```python
double_val = []
for row in table:
    double_val.append(row['val']**2)
data['double_val'] = double_val
```

Or, better, use `apply`. The first argument is a function (or callable).
You may specify which columns you want passed into the function with
more arguments, as below. Otherwise, the entire `DataRow` is passed into the
function as the only argument.

```python
data['double_val'] = data.apply(lambda x: x**2, 'val')
# or, equivalently
data['double_val'] = data.apply(lambda row: row['val']**2)
```

### Adding columns

Columns can be added simply by assigning any list value to a column name:

```python
data['squares'] = [i**2 for i in range(len(data))]
```

Columns can also be added by applying a function to a column and setting 
that result to a new column:

```python
data['diff'] = data.apply(lambda row: row['new_count']/row['old_count'])
# or
data['diff'] = data.apply(short_diff, 'old_count', 'new_count')
```

If you want to set a whole column to some "scalar"-like value, here is some
sugar:

```python
data['five'] = 5
data['notes'] = 'Unknown'
```

### Slicing

Slicing a table, like `data[4:34:3]`, gracefully handling of out of bounds 
slicings, like a normal Python `list` does. The slice is also shallow copy,
just like a Python `list` slice.

### Concatenating

The `concat` method 

```python

```

### Appending

TODO

### Sorting

For multi-priority sorting, simply chain multiple sortings in increasing 
order of importance.

```python
data = data.sort('diff', desc=True).sort('description').sort('searchterm')
```

Sorting can be done in-place with the `inplace` argument. A reference to the 
(original, now mutated) DataTable is returned just in case, but the original 
DataTable is mutated.

```python
data.sort('randnum', inplace=True)
```

### Renaming columns

```python
data.rename('diff', 'diff percentage')
```

Or, to rename many columns:

```python
data.fields = [field.lower() for field in fields]
```

### Reordering columns

The fields passed in must be identical in content to the current fields.
The columns will be swapped to match their order.

```python
data.reorder(sorted(data.fields))
```

## Filtering

Create a new DataTable in every case where a column equals certain value.

```python
positive_sentences = data.where('sentiment', 'positive')
```

`where` can also take a `set` or `tuple` to check multiple criteria at once - 
think of this like an `or`.

```python
sentiment_sentences = data.where('sentiment', ('positive', 'negative'))
```

`where` can also take a callable. The value at that column for each row gets 
passed into the callable. Since `where` returns a DataTable instance, you can 
chain calls of `where`.

```python
high_agreement_positives = data.where('sentiment', 'positive')
                               .where('agreement', lambda ag: ag >= 0.75)
true_positives = high_agreement_positives.where('answer', 'positive')
positive_precision = len(true_positives)/len(high_agreement_positives)
```

`where` can take a `negate=True` argument to negate whatever condition has been 
expressed. `wherenot` is equivalent to this.

```python
sentiment_bearing = data.where('answer', ('neutral', 'not_sure'), negate=True)
# equivalent
sentiment_bearing = data.wherenot('answer', ('neutral', 'not_sure'))
```

`wherefunc` takes one argument: a function that returns a boolean when passed 
a row of data (an immutable ordered dict-like object).

```python
def conditional_filter(datarow):
    if datarow['state'] == 'CA' and datarow['penalty'] > 100:
        return True
    elif datarow['penalty'] > 0:
        return True
    return False

result = data.wherefunc(conditional_filter)
```

You can also create a filtered DataTable by passing an iterable of `bool` to 
the `mask` method.

## Groupby TODO

```python
data.groupby
```

## Display

By default, `print`ing a DataTable returns a tab-separated string 
representation of the table. You can also print a few other common formats
using special properties of the DataTable object:

```python
print data.jira  # Jira-style formatting, "|" separated
print data.html  # HTML table
print data.pretty  # a "pretty table" style table for the console (TODO)
```

## Join

TODO

## Future

TODO