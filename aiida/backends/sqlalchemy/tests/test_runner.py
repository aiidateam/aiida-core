# -*- coding: utf-8 -*-

import unittest
import sys, inspect

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


def print_classes():
    print ">>>>>>>>>>>>> ", __name__
    for name, obj in inspect.getmembers(sys.modules["aiida.backends.sqlalchemy.tests.nodes"]):
        extracted_classes = list()
        if inspect.isclass(obj):
            print "-------> ", obj
            extracted_classes.append(obj)

        inspect.getclasstree(extracted_classes)


def run_tests():
    from aiida.backends.sqlalchemy.tests.nodes import TestDataNodeSQLA
    print_classes()
    exit(0)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataNodeSQLA)
    unittest.TextTestRunner(verbosity=2).run(suite)
