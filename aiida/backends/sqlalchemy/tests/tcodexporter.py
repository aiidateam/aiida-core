# -*- coding: utf-8 -*-
"""
Tests for the Tcod exporter
"""

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

#import the generic test class for nwchem
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.tcodexporter import TestTcodDbExporter


class TestTcodDbExporterSqla(SqlAlchemyTests, TestTcodDbExporter):
    """
    tcod database exporter tests that do need to be specified for sqlalchemy
    backend
    """
    pass

