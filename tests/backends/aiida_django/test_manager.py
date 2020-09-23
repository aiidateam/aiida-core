# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the django backend manager."""

from aiida.backends.djsite.manager import DjangoSettingsManager
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions


class TestDjangoSettingsManager(AiidaTestCase):
    """Test the DjangoSettingsManager class and its methods."""

    def setUp(self):
        super().setUp()
        self.settings_manager = DjangoSettingsManager()

    def test_set_get(self):
        """Test the get and set methods."""
        temp_key = 'temp_setting'
        temp_value = 'Valuable value'
        temp_description = 'Temporary value for testing'

        self.settings_manager.set(temp_key, temp_value, temp_description)
        self.assertEqual(self.settings_manager.get(temp_key).value, temp_value)
        self.assertEqual(self.settings_manager.get(temp_key).description, temp_description)

        non_existent_key = 'I_dont_exist'

        with self.assertRaises(exceptions.NotExistent):
            self.settings_manager.get(non_existent_key)

    def test_delete(self):
        """Test the delete method."""
        temp_key = 'temp_setting'
        temp_value = 'Valuable value'

        self.settings_manager.set(temp_key, temp_value)
        self.settings_manager.delete(temp_key)

        non_existent_key = 'I_dont_exist'

        with self.assertRaises(exceptions.NotExistent):
            self.settings_manager.delete(non_existent_key)
