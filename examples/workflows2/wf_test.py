# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.orm.data.simple import Int
from aiida.workflows2.db_types import to_db_type, SimpleData

@wf
def sum(a, b):
    return to_db_type(a.value + b.value)


@wf
def prod(a, b):
    return to_db_type(a.value * b.value)


@wf
def add_multiply_wf(a, b, c):
    return prod(sum(a, b), c)


if __name__ == '__main__':
    two = Int(2)
    three = Int(3)
    four = Int(4)

    print "WORKFUNCTION:"

    simpledata = add_multiply_wf(two, three, four)
    print "output pk:", simpledata.pk
    print "output value:", simpledata.value
