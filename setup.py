#!/usr/bin/env python

from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='acrylic',
    version='0.1.0',
    description='Simple tabular data in Python.',
    url="http://github.com/emlazzarin/acrylic",

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2.7',
    ],
    install_requires=['openpyxl']
)