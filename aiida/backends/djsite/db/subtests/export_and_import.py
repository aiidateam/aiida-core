# -*- coding: utf-8 -*-
"""
Tests for the export and import routines.
"""

from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.export_and_import import TestSpecificImport
from aiida.backends.tests.export_and_import import TestSimple
from aiida.backends.tests.export_and_import import TestComplex

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestSpecificImportDjango(AiidaTestCase, TestSpecificImport):
    pass


class TestSimpleDjango(AiidaTestCase, TestSimple):
    pass


class TestComplexDjango(AiidaTestCase, TestComplex):
    pass

