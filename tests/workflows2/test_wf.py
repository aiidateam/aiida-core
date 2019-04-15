# -*- coding: utf-8 -*-
import unittest

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.wf import wf
from aiida.workflows2.run import async
from aiida.workflows2.db_types import to_db_type


_True = to_db_type(True)


@wf
def simple_wf():
    return {'result': _True}

@wf
def return_input(inp):
    return {'result': inp}


class TestWf(unittest.TestCase):
    def test_blocking(self):
        self.assertTrue(simple_wf()['result'].value)
        self.assertTrue(return_input(_True)['result'].value)

    def test_async(self):
        self.assertTrue(async(simple_wf).result()['result'].value)
        self.assertTrue(async(return_input, _True).result()['result'].value)
