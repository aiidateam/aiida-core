# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Testing infrastructure for easy testing of AiiDA plugins.

"""

import warnings
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.manage.tests import TestManager as FixtureManager
from aiida.manage.tests import test_manager as fixture_manager
from aiida.manage.tests import _GLOBAL_TEST_MANAGER as _GLOBAL_FIXTURE_MANAGER
from aiida.manage.tests.unittest_classes import PluginTestCase

warnings.warn('this module is deprecated, use `aiida.manage.tests` and its submodules instead', AiidaDeprecationWarning)  # pylint: disable=no-member

__all__ = ('FixtureManager', 'fixture_manager', '_GLOBAL_FIXTURE_MANAGER', 'PluginTestCase')
