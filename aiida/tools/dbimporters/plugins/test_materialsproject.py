# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that contains the class definitions necessary to offer support for queries to Materials Project."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import pytest

from aiida.backends.testbase import AiidaTestCase
from aiida.plugins import DbImporterFactory


def run_materialsproject_api_tests():
    from aiida.settings import PROFILE_CONF
    return PROFILE_CONF.get('run_materialsproject_api_tests', False)


class TestMaterialsProject(AiidaTestCase):
    """
    Contains the tests to verify the functionality of the Materials Project importer
    functions.
    """

    import unittest

    @unittest.skipIf(not run_materialsproject_api_tests(), "MaterialsProject API tests not enabled")
    def test_invalid_api_key(self):  # pylint: disable=no-self-use
        """
        Test if Materials Project rejects an invalid API key and that we catch the error.
        Please enable the test in the profile configurator.
        """
        importer_class = DbImporterFactory('materialsproject')
        importer_parameters = {'api_key': 'thisisawrongkey'}

        with pytest.raises(Exception):
            importer_class(**importer_parameters)
