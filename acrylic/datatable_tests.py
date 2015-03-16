# coding: utf-8
from collections import OrderedDict
from nose.tools import (assert_equal,
                        assert_not_equal,
                        assert_raises,
                        raises)

import datatable
import ExcelRW


excel_reader = ExcelRW.UnicodeDictReader('testdata.xlsx')
data = datatable.DataTable(excel_reader)

raw_excel_data_lists = list(ExcelRW.UnicodeReader('testdata.xlsx'))
raw_excel_data_dicts = list(ExcelRW.UnicodeDictReader('testdata.xlsx'))


def test_00csvstringconstructor():
    global data

    # Note that CSV files, when data is copy-pasted from them,
    # can occasionally lose least-significant digits from long floats.

    # "\'bart\',"dfe\\"ns <- excel parsed row
    # \'bart\',dfe\\"ns <- csv string parsed row,
    #                      without r'''''' or csv.QUOTE_NONE
    # "\'bart\',"dfe\\"ns <- with r'''''' and csv.QUOTE_NONE
    # "'bart',"dfe\"ns <- row copy-pasted from excel

    csv_data = datatable.DataTable.fromcsvstring(ur"""apostle	randnum	randnum2	colors	regular numbers	comma,column
john	0.1104	0.824761	black	4	strin,"dfe\"ns
andrew	0.1836	0.568254	black	2	strin,"dfe\"ns
philip	0.2069	0.662074	red	5	strin,"dfe\"ns
judas	0.3623	0.055173	red	12	strin,"dfe\"ns
bartholomew	0.3826	0.512637	black	6	"'bart',"dfe\"ns
james	0.4481	0.746867	black	9	strin,"dfe\"ns
ペトロ	0.468	0.606110	red	1	strin,"dfe\"ns
thomas	0.5114	0.585969	yellow	7	strin,"dfe\"ns
matthew	0.5927	0.239200	red	8	strin,"dfe\"ns
simon the less	0.6132	0.762991	green	11	strin,"dfe\"ns
james	0.6682	0.660805	red	3	strin,"dfe\"ns
thaddeus	0.7175	0.075857	yellow	10	strin,"dfe\"ns
""", delimiter="\t")

    for row, csv_string_row in zip(data, csv_data):
        assert_equal(row, csv_string_row)


def test_00listconstructor():
    global data

    reader = ExcelRW.UnicodeReader('testdata.xlsx')
    csv_data = datatable.DataTable(reader)

    for row, csv_row in zip(data, csv_data):
        assert_equal(row, csv_row)


def test_01sort():
    global data

    saints = list(sorted(data['apostle']))
    data = data.sort('apostle')
    assert_equal(data['apostle'], saints)

    randnums = list(sorted(data['randnum2']))
    assert_not_equal(randnums, data['randnum2'])
    data.sort('randnum2', inplace=True)
    assert_equal(data['randnum2'], randnums)


def test_02len():
    global data

    assert_equal(len(data), 12)


def test_03row():
    global data

    row = data.row(3)
    assert_equal(row['apostle'], 'bartholomew')
    assert_equal(row['regular numbers'], 6)
    assert_equal(row['comma,column'], r'''"'bart',"dfe\"ns''')


def test_04getsetitem():
    global data

    signs = ['aries',
             'taurus',
             'gemini',
             'cancer',
             'leo',
             'virgo',
             'libra',
             'scorpio',
             'sagittarius',
             'capricorn',
             'aquarius',
             'pisces']

    data['signs'] = signs
    assert_equal(signs, data['signs'])

    for sign, inner_sign in zip(signs, data['signs']):
        assert_equal(sign, inner_sign)


def test_05distinct():
    global data

    distinct_apostles = data.distinct('apostle')
    assert_equal(len(distinct_apostles), 11)

    true_distinct = (u'judas',
                     u'thaddeus',
                     u'matthew',
                     u'bartholomew',
                     u'andrew',
                     u'thomas',
                     u'ペトロ',
                     u'james',
                     u'philip',
                     u'simon the less',
                     u'john')

    assert_equal(true_distinct, distinct_apostles)

    distinct_apostle_lens = data.distinct('apostle', key=lambda x: len(x))
    assert_equal(len(distinct_apostle_lens), 8)

    true_distinct = (u'judas',
                     u'thaddeus',
                     u'matthew',
                     u'bartholomew',
                     u'andrew',
                     u'ペトロ',
                     u'simon the less',
                     u'john')

    assert_equal(true_distinct, distinct_apostle_lens)


def test_06apply():
    global data

    apostles = data['apostle']
    apostle_lens = [len(i) for i in apostles]

    data['apostle len'] = data.apply(len, 'apostle')

    assert_equal(apostle_lens, data['apostle len'])
    assert_equal(apostle_lens, data.apply(lambda x: len(x['apostle'])))


def test_07writeexcel():
    global data

    data.writexlsx('testout.xlsx')
    reader = ExcelRW.UnicodeDictReader('testout.xlsx')
    written_data = datatable.DataTable(reader)
    for row, written_row in zip(data, written_data):
        assert_equal(row, written_row)


def test_08goodsetfields():
    global data

    numbers = ['apostle',
               'two',
               'three',
               'four',
               'five',
               'six',
               'seven',
               'eight']
    old_fields = list(data.fields)
    data.fields = numbers
    assert_equal(numbers, list(data.fields))
    data.fields = old_fields


def test_09goodrename():
    global data

    starting_fields = list(data.fields)
    data.rename('apostle', 'apostles')
    assert_equal(list(data.fields)[0], 'apostles')
    data.rename('randnum', 'randnum')
    data.rename('apostles', 'apostle')
    assert_equal(starting_fields, list(data.fields))


def test_10len():
    table = datatable.DataTable()
    assert_equal(len(table), 0)


def test_11buildwithdict():
    table = datatable.DataTable.fromdict({'a': [1, 2, 3],
                                          'b': [4, 5, 6],
                                          'c': [7, 8, 9]})
    assert_equal(table.row(1)['b'], 5)

    table = datatable.DataTable.fromdict(OrderedDict([('a', [1, 2, 3]),
                                                      ('b', [4, 5, 6]),
                                                      ('c', [7, 8, 9])]))
    assert_equal(table.row(2)['a'], 3)


def test_12maskwherered():
    global data
    assert_raises(Exception, data.mask, [True, False])

    redapostles = [u'judas',
                   u'matthew',
                   u'ペトロ',
                   u'james',
                   u'philip']

    assert_equal(data.where('colors', 'red')['apostle'], redapostles)

    redapostle_masklist = []
    for row in data:
        redapostle_masklist.append(row['colors'] == 'red')

    assert_equal(data.mask(redapostle_masklist)['apostle'], redapostles)


def test_14multiwhere():
    global data

    yg_apostles = data.where('colors', ('yellow', 'green'))['apostle']
    assert_equal(yg_apostles, ['thaddeus', 'thomas', 'simon the less'])


def test_15wherefunc():
    global data

    bigredfunc = lambda x: (x['colors'] == 'red') and x['randnum2'] > .5
    bigreds = data.wherefunc(bigredfunc)
    assert_equal(bigreds['regular numbers'], [1, 3, 5])


def test_16callablewhere():
    global data

    bignums = lambda x: x > 5
    bignumsresult = data.where('regular numbers', bignums)['regular numbers']
    assert_equal(bignumsresult, [12, 10, 8, 6, 7, 9, 11])


def test_17maskgenerator():
    global data

    mask = (i for i in [True,
                        True,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                        True,
                        False])
    weirdnamedapostles = data.mask(mask)['apostle']
    verifyweirdapostles = ['judas',
                           'thaddeus',
                           'bartholomew',
                           'simon the less']
    assert_equal(weirdnamedapostles, verifyweirdapostles)


def test_18contains():
    global data

    assert_equal(data.__contains__('colors'), True)
    assert_equal('colors' in data, True)
    assert_equal(data.__contains__('water'), False)
    assert_equal('water' in data, False)


def test_19str():
    global data

    assert_equal(str(data), unicode(data).encode('utf-8'))


# def test_190groupbylen():
#     global data
#
#     colorgroups = data.groupby('colors', agg=len, concat='apostle')
#     print colorgroups
#
#     test = datatable.DataTable()
#     test['colors'] = ['red', 'yellow', 'black', 'green']
#     test['len'] = [5, 2, 4, 1]
#     test['group_concat(apostle)'] = [u'judas,matthew,ペトロ,james,philip',
#                                      u'thaddeus,thomas',
#                                      u'bartholomew,andrew,james,john',
#                                      u'simon the less']
#
#     print test
#
#     assert_equal(test, colorgroups)


@raises(Exception)
def test_20missing_rename():
    global data
    data.rename('party', 'winkler')


@raises(Exception)
def test_21noiterable():
    datatable.DataTable(4)


@raises(TypeError)
def test_22mut():
    global data
    data.row(2)['apostle'] = 'ricky'


@raises(Exception)
def test_23badsetfields():
    global data
    data.fields = ['one', 'two']


@raises(Exception)
def test_24badrename():
    global data
    data.rename('barney', 'whitmore')


@raises(Exception)
def test_25badcsvstringconstruction():
    reader = raw_excel_data_dicts[:]
    datatable.DataTable.fromcsvstring(reader)


@raises(Exception)
def test_26badrowinexcel():
    reader = raw_excel_data_dicts[:]
    del reader[4]['apostle']
    datatable.DataTable(reader)


@raises(TypeError)
def test_27wrongrowtypeexceldict():
    reader = raw_excel_data_dicts[:]
    reader[4] = ur"""sixcha"""
    datatable.DataTable(reader)


@raises(TypeError)
def test_28wrongrowtypeexcellist():
    reader = raw_excel_data_lists[:]
    reader[4] = ur"""sixcha"""
    datatable.DataTable(reader)


@raises(Exception)
def test_29wrongrowlenthexcellist():
    reader = raw_excel_data_lists[:]
    reader[5] = reader[5][:-1]
    datatable.DataTable(reader)


@raises(Exception)
def test_30wrongrowtypeexcellist():
    reader = raw_excel_data_lists[:]
    reader[0] = lambda x: x**2
    datatable.DataTable(reader)


def test_31getcolexception():
    global data
    assert_raises(KeyError, data.__getitem__, 'notacolumn')


@raises(IndexError)
def test_32rowerror():
    global data
    data.row(4398)


@raises(Exception)
def test_33collengtherror():
    global data
    data['toolong'] = range(35)


@raises(Exception)
def test_34stringrows():
    datatable.DataTable(['row1', 'row2', 'row3', 'row4'])


def test_35wherenot():
    global data
    green = data.wherenot('colors', {'red', 'yellow', 'black'})
    assert_equal(green['apostle'], ['simon the less'])
    assert_raises(Exception, data.wherenot, 'colors', {'a': 5})
