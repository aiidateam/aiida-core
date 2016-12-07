# -*- coding: utf-8 -*-
"""
Tests for specific subclasses of Data
"""
from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.dataclasses import *

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

class TestCalcStatusDjango(AiidaTestCase, TestCalcStatus):
    """
    """
    pass


class TestSinglefileDataDjango(AiidaTestCase, TestSinglefileData):
    """
    """
    pass


class TestCifDataDjango(AiidaTestCase, TestCifData):
    """
    """
    pass


class TestKindValidSymbolsDjango(AiidaTestCase, TestKindValidSymbols):
    """
    """
    pass


class TestSiteValidWeightsDjango(AiidaTestCase, TestSiteValidWeights):
    """
    """
    pass


class TestKindTestGeneralDjango(AiidaTestCase, TestKindTestGeneral):
    """
    """
    pass


class TestKindTestMassesDjango(AiidaTestCase, TestKindTestMasses):
    """
    """
    pass


class TestStructureDataInitDjango(AiidaTestCase, TestStructureDataInit):
    """
    """
    pass


class TestStructureDataDjango(AiidaTestCase, TestStructureData):
    """
    """
    pass


class TestStructureDataLockDjango(AiidaTestCase, TestStructureDataLock):
    """
    """
    pass


class TestStructureDataReloadDjango(AiidaTestCase, TestStructureDataReload):
    """
    """
    pass


class TestStructureDataFromAseDjango(AiidaTestCase, TestStructureDataFromAse):
    """
    """
    pass


class TestStructureDataFromPymatgenDjango(AiidaTestCase, TestStructureDataFromPymatgen):
    """
    """
    pass


class TestPymatgenFromStructureDataDjango(AiidaTestCase, TestPymatgenFromStructureData):
    """
    """
    pass


class TestArrayDataDjango(AiidaTestCase, TestArrayData):
    """
    """
    pass


class TestTrajectoryDataDjango(AiidaTestCase, TestTrajectoryData):
    """
    """
    pass


class TestKpointsDataDjango(AiidaTestCase, TestKpointsData):
    """
    """
    pass


class TestDataDjango(AiidaTestCase, TestData):
    """
    """
    pass
