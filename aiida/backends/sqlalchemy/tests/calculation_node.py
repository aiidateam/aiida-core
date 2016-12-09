# -*- coding: utf-8 -*-
"""
Tests for calculation nodes, attributes and links
"""


from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests

from aiida.backends.tests.calculation_node import TestCalcNode


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

class TestCalcNodeSQLA(SqlAlchemyTests, TestCalcNode):
    pass
