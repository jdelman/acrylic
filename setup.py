#!/usr/bin/env python

from setuptools import setup
from os import path

import ast
import re

here = path.abspath(path.dirname(__file__))

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('click/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='acrylic',
    version=version,
    description='Simple tabular data with Python.',
    packages=['acrylic'],
    url="http://github.com/emlazzarin/acrylic/",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=['openpyxl', 'jdcal']
)