# -*- coding: utf-8 -*-
"""
Tests for specific subclasses of Data
"""

from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.parsers import TestParsers

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestParsersSqla(SqlAlchemyTests, TestParsers):
    """
    """
    def read_test(self, outfolder):
    
        import os
        import importlib
        import json

        from aiida.common.exceptions import NotExistent
        from aiida.orm import JobCalculation
        from aiida.orm.utils import load_node
        from aiida.orm.importexport import import_data_sqla

        imported = import_data_sqla(outfolder,
                               ignore_unknown_nodes=True, silent=True)

        calc = None
        for _, pk in imported['aiida.backends.djsite.db.models.DbNode']['new']:
            c = load_node(pk)
            if issubclass(c.__class__, JobCalculation):
                calc = c
                break

        retrieved = calc.out.retrieved

        try:
            with open(os.path.join(outfolder, '_aiida_checks.json')) as f:
                tests = json.load(f)
        except IOError:
            raise ValueError("This test does not provide a check file!")
        except ValueError:
            raise ValueError("This test does provide a check file, but it cannot "
                             "be JSON-decoded!")

        mod_path = 'aiida.backends.tests.parser_tests.{}'.format(
            os.path.split(outfolder)[1])

        skip_test = False
        try:
            m = importlib.import_module(mod_path)
            skip_test = m.skip_condition()
        except Exception:
            pass

        if skip_test:
            raise SkipTestException

        return calc, {'retrieved': retrieved}, tests

class SkipTestException(Exception):
    pass
