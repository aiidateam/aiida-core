# -*- coding: utf-8 -*-

import unittest
import sys, inspect
import aiida.backends.sqlalchemy.tests.nodes

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
    module_str = "aiida.backends.sqlalchemy.tests.nodes"
    for test_class in find_classes(module_str):
        print "Running ", test_class, " of module ", module_str, "."
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(suite)
