# -*- coding: utf-8 -*-
"""
Tests for the NWChem input plugins.
"""

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

#import the generic test class for nwchem
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.nwchem import TestNwchem


class TestNwchemSqla(SqlAlchemyTests, TestNwchem):
    """
    nwchem tests that do need to be specified for sqlalchemy backend
    """
    pass