# -*- coding: utf-8 -*-

import unittest

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


def run_tests():
    from aiida.backends.sqlalchemy.tests.nodes import TestDataNodeSQLA
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataNodeSQLA)
    unittest.TextTestRunner(verbosity=2).run(suite)
