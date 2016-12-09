# -*- coding: utf-8 -*-
"""
Tests for ``aiida.tools.codespecific.quantumespresso.pwinputparser``.

Since the AiiDa-specific methods of PwInputFile generates (unstored) Node
objects, this  has to be run with a temporary database.

The directory, ``./pwtestjobs/``, contains small QE jobs that are used to test
the parsing and units conversion. The test jobs should all contain the same
structure, input parameters, ect., but the units of the input files differ,
in order to test the unit and coordinate transformations of the PwInputTools
methods. The only thing that should vary between some of them is the type of
k-points (manual, gamma, and automatic). For this reason, the testing of
get_kpointsdata is split up into three different test methods.
"""
import os

import numpy as np

from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.pwinputparser import TestPwInputFile

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

class TestPwInputFileSqla(SqlAlchemyTests, TestPwInputFile):
    """
    """
    pass