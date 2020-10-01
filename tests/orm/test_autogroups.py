# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Autogroup functionality."""
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import AutoGroup, QueryBuilder
from aiida.orm.autogroup import Autogroup


class TestAutogroup(AiidaTestCase):
    """Tests the Autogroup logic."""

    def test_get_or_create(self):
        """Test the ``get_or_create_group`` method of ``Autogroup``."""
        label_prefix = 'test_prefix_TestAutogroup'

        # Check that there are no groups to begin with
        queryb = QueryBuilder().append(AutoGroup, filters={'label': label_prefix})
        assert not list(queryb.all())
        queryb = QueryBuilder().append(AutoGroup, filters={'label': {'like': r'{}\_%'.format(label_prefix)}})
        assert not list(queryb.all())

        # First group (no existing one)
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = label_prefix
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )

        # Second group (only one with no suffix existing)
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = f'{label_prefix}_1'
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )

        # Second group (only one suffix _1 existing)
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = f'{label_prefix}_2'
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )

        # I create a group with a large integer suffix (9)
        AutoGroup(label=f'{label_prefix}_9').store()
        # The next autogroup should become number 10
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = f'{label_prefix}_10'
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )

        # I create a group with a non-integer suffix (15a), it should be ignored
        AutoGroup(label=f'{label_prefix}_15b').store()
        # The next autogroup should become number 11
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = f'{label_prefix}_11'
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )

    def test_get_or_create_invalid_prefix(self):
        """Test the ``get_or_create_group`` method of ``Autogroup`` when there is already a group
        with the same prefix, but followed by other non-underscore characters."""
        label_prefix = 'new_test_prefix_TestAutogroup'
        # I create a group with the same prefix, but followed by non-underscore
        # characters. These should be ignored in the logic.
        AutoGroup(label=f'{label_prefix}xx').store()

        # Check that there are no groups to begin with
        queryb = QueryBuilder().append(AutoGroup, filters={'label': label_prefix})
        assert not list(queryb.all())
        queryb = QueryBuilder().append(AutoGroup, filters={'label': {'like': r'{}\_%'.format(label_prefix)}})
        assert not list(queryb.all())

        # First group (no existing one)
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = label_prefix
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )

        # Second group (only one with no suffix existing)
        autogroup = Autogroup()
        autogroup.set_group_label_prefix(label_prefix)
        group = autogroup.get_or_create_group()
        expected_label = f'{label_prefix}_1'
        self.assertEqual(
            group.label, expected_label,
            f"The auto-group should be labelled '{expected_label}', it is instead '{group.label}'"
        )
