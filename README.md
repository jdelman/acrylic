# Acrylic 0.1.0

## Loading Data

A DataTable can always be constructed from a list of dictionaries, where the keys are the column names, or a list of lists, where the first list contains the column names. If you use `OrderedDict` instead of a standard dictionary, column order will be preserved (and based off of the first row). Otherwise, the order will be lost - but you can always reorder columns later.

### Read data from Excel:

```python
data = DataTable.fromxls('myfile.xls', sheet_name_or_number='default')
```

### Read data from CSV:

```python
data = DataTable.fromcsv('myfile.xls')
```

### Read data from a copy-pasted CSV Unicode literal:

Note that you should almost always prefix your triple-quoted string with `ur` (as in `ur"""string contents"""`) if it's been copy-pasted from Excel. If you're copying something printed from Python (using the `print` statement), also append `ur`. If you're copying something that was simply dumped to the screen (like just typing `objname` at the REPL and hitting "enter" without the `print` statement, which only invokes `__repr__` on the object), you should prefix only with `u`.

Also, do not try to line up your copy-pasted CSV data for a visual indent. That will just add tons of whitespace to the left side of the first column.

```python
data = DataTable.fromcsv(ur'''a,b,c
d,e,f
g,h,i''')
```

### Write data to Excel:

```python
data.writexls('myoutput.xls')
```
### Write many Tables to Excel:

`sheetnames` is optional. Sheet names will default to "Table_01", etc. if it isn't provided.

```python
Tables = [Table_one, Table_two]
excel('output.xls', Tables, sheetnames=("one", "two"))
```

## Manipulating a DataTable

### Adding columns

```python
data['diff'] = data.apply(lambda row: row['new_count']/row['old_count'])
# or
data['diff'] = data.apply(short_diff, 'old_count', 'new_count')
```

### Iterating

It is possible to iterate through the DataTable row by row, although it is 
not especially efficient, and you cannot modify rows. 
Column order is preserved. Don't alter the DataTable during iteration.

```python
for row in data:
    for header, value in row:
        # do something
```

*Don't* do this:

```python
for row in data:
    doubled_value = row['val']**2
    # TypeError because rows are immutable
    row['double_val'] = double_value
```

Instead, you could do this:

```python
double_val = []
for row in table:
    double_val.append(row['val']**2)
data['double_val'] = double_val
```

Or, preferably, use `apply`. The first argument is a function (or callable) 
you wish to be called. If no subsequent arguments are passed in, the entire 
`DataRow` is passed in as the function. However, you may specify which columns 
you want passed into the function with subsequent arguments, like below:

```python
data['double_val'] = data.apply(lambda x: x**2, 'val')
```

### Slicing

Slicing a table, like `data[4:34:3]`, gracefully handling of out of bounds 
slicings, like a normal Python list. The slice is a shallow copy, like a 
Python list slice.

### Sorting

For multi-priority sorting, simply chain multiple sortings in increasing 
order of importance.

```python
data = data.sort('diff', desc=True).sort('description').sort('searchterm')
```

Sorting can be done in-place with the `inplace` argument. A reference to the 
DataTable is returned just in case, but the original DataTable is mutated.
```python
data.sort('randnum', inplace=True)
```

### Renaming columns

```python
data.rename('diff', 'diff percentage')
```

### Reordering columns

```python
data.fields = sorted(data.fields)
```

## Filtering

Create a new DataTable in every case where a column equals certain value.

```python
positive_sentences = data.where('sentiment', 'positive')
```

`where` can also take a `set` or `tuple` to check multiple criteria at once - or think of this like `or`.

```python
sentiment_sentences = data.where('sentiment', ('positive', 'negative'))
```

`where` can also take a callable. The value at that column for each row gets passed into the callable. Since `where` returns a DataTable instance, you can chain calls of `where`.

```python
high_agreement_positives = data.where('sentiment', 'positive').where('agreement', lambda agg: agg >= 0.75)
true_positives = high_agreement_positives.where('answer', 'positive')
positive_precision = len(true_positives)/len(high_agreement_positives)
```

`where` can take a `negate=True` argument to negate whatever condition has been expressed. `wherenot` is equivalent to this.

`wherefunc` takes one argument: a function that returns a boolean when passed a row of data (an immutable ordered dict-like object).

```python
def conditional_filter(datarow):
    if datarow['state'] == 'CA' and datarow['penalty'] > 100:
        return True
    elif datarow['penalty'] > 0:
        return True
    return False

result = data.wherefunc(conditional_filter)
```

You can also create a filtered DataTable by passing an iterable of `bool` to the `mask` method.

## Groupby

TODO

## Join

TODO

## Display

TODO
