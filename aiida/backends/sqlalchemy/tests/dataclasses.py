# -*- coding: utf-8 -*-
"""
Tests for specific subclasses of Data
"""
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.dataclasses import *

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

class TestCalcStatusSqla(SqlAlchemyTests, TestCalcStatus):
    """
    """
    pass


class TestSinglefileDataSqla(SqlAlchemyTests, TestSinglefileData):
    """
    """
    pass


class TestCifDataSqla(SqlAlchemyTests, TestCifData):
    """
    """
    pass


class TestKindValidSymbolsSqla(SqlAlchemyTests, TestKindValidSymbols):
    """
    """
    pass


class TestSiteValidWeightsSqla(SqlAlchemyTests, TestSiteValidWeights):
    """
    """
    pass


class TestKindTestGeneralSqla(SqlAlchemyTests, TestKindTestGeneral):
    """
    """
    pass


class TestKindTestMassesSqla(SqlAlchemyTests, TestKindTestMasses):
    """
    """
    pass


class TestStructureDataInitSqla(SqlAlchemyTests, TestStructureDataInit):
    """
    """
    pass


class TestStructureDataSqla(SqlAlchemyTests, TestStructureData):
    """
    """
    pass


class TestStructureDataLockSqla(SqlAlchemyTests, TestStructureDataLock):
    """
    """
    pass


class TestStructureDataReloadSqla(SqlAlchemyTests, TestStructureDataReload):
    """
    """
    pass


class TestStructureDataFromAseSqla(SqlAlchemyTests, TestStructureDataFromAse):
    """
    """
    pass


class TestStructureDataFromPymatgenSqla(SqlAlchemyTests, TestStructureDataFromPymatgen):
    """
    """
    pass


class TestPymatgenFromStructureDataSqla(SqlAlchemyTests, TestPymatgenFromStructureData):
    """
    """
    pass


class TestArrayDataSqla(SqlAlchemyTests, TestArrayData):
    """
    """
    pass


class TestTrajectoryDataSqla(SqlAlchemyTests, TestTrajectoryData):
    """
    """
    pass


class TestKpointsDataSqla(SqlAlchemyTests, TestKpointsData):
    """
    """
    pass


class TestDataSqla(SqlAlchemyTests, TestData):
    """
    """
    pass
