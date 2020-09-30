# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module,invalid-name
"""Test migration to add the `extras` JSONB column to the `DbGroup` model."""

from .test_migrations_common import TestMigrations


class TestGroupExtrasMigration(TestMigrations):
    """Test migration to add the `extras` JSONB column to the `DbGroup` model."""

    migrate_from = '0044_dbgroup_type_string'
    migrate_to = '0045_dbgroup_extras'

    def setUpBeforeMigration(self):
        DbGroup = self.apps.get_model('db', 'DbGroup')

        group = DbGroup(label='01', user_id=self.default_user.id, type_string='user')
        group.save()
        self.group_pk = group.pk

    def test_extras(self):
        """Test that the model now has an extras column with empty dictionary as default."""
        DbGroup = self.apps.get_model('db', 'DbGroup')

        group = DbGroup.objects.get(pk=self.group_pk)
        self.assertEqual(group.extras, {})
