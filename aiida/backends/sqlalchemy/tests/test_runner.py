# -*- coding: utf-8 -*-

import importlib
import inspect
import sys
import unittest

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


def find_classes(module_str):
    extracted_classes = list()
    for _, obj in inspect.getmembers(sys.modules[module_str]):
        if inspect.isclass(obj) and obj.__module__ == module_str:
            extracted_classes.append(obj)
    return extracted_classes


def run_tests():
    modules_str = [
        # "aiida.backends.sqlalchemy.tests.query",
        # "aiida.backends.sqlalchemy.tests.nodes",
        # "aiida.backends.sqlalchemy.tests.backup_script",
        #  "aiida.backends.sqlalchemy.tests.export_and_import",
        #  "aiida.backends.sqlalchemy.tests.nwchem",
        #  "aiida.backends.sqlalchemy.tests.quantumespressopw",
        #  "aiida.backends.sqlalchemy.tests.quantumespressopwimmigrant",
         "aiida.backends.sqlalchemy.tests.generic"
    ]
    for module_str in modules_str:
        # Dynamically importing the module that interests us
        importlib.import_module(module_str)

        for test_class in find_classes(module_str):
            print "Running ", test_class, " of module ", module_str, "."
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            unittest.TextTestRunner(verbosity=2).run(suite)
