# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common.datastructures import _sorted_datastates, calc_states, is_progressive_state_change


class TestCommonDataStructures(AiidaTestCase):

    def test_is_progressive_state_change(self):
        """Test the `is_progressive_state_change` utility function by testing all possible state change permutations."""
        for i, state_one in enumerate(_sorted_datastates):

            for j, state_two in enumerate(_sorted_datastates):

                # States will be equal and should not count as progressive state change
                if i == j:
                    self.assertFalse(is_progressive_state_change(state_one, state_two))
                elif i > j:
                    self.assertFalse(is_progressive_state_change(state_one, state_two))
                elif i < j:
                    self.assertTrue(is_progressive_state_change(state_one, state_two))
                else:
                    assert True, 'we broke math'

    def test_is_progressive_state_change_invalid_states(self):
        """Test `is_progressive_state_change` function should raise ValueError for invalid states."""
        with self.assertRaises(ValueError):
            is_progressive_state_change('NOTEXISTENT', calc_states.NEW)

        with self.assertRaises(ValueError):
            is_progressive_state_change(calc_states.NEW, 'NOTEXISTENT')
