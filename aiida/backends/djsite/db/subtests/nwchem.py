# -*- coding: utf-8 -*-
"""
Tests for the NWChem input plugins.
"""

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

#import the generic test class for nwchem
from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.nwchem import TestNwchem


class TestNwchemDjango(TestNwchem, AiidaTestCase):
    """
    These tests check the features of nwchem input file generator that differ
    from the base Nwchem test
    """
    pass

