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
"""Test migration of `type_string` after the `Group` class became pluginnable."""

from .test_migrations_common import TestMigrations


class TestGroupTypeStringMigration(TestMigrations):
    """Test migration of `type_string` after the `Group` class became pluginnable."""

    migrate_from = '0043_default_link_label'
    migrate_to = '0044_dbgroup_type_string'

    def setUpBeforeMigration(self):
        DbGroup = self.apps.get_model('db', 'DbGroup')

        # test user group type_string: 'user' -> 'core'
        group_user = DbGroup(label='01', user_id=self.default_user.id, type_string='user')
        group_user.save()
        self.group_user_pk = group_user.pk

        # test data.upf group type_string: 'data.upf' -> 'core.upf'
        group_data_upf = DbGroup(label='02', user_id=self.default_user.id, type_string='data.upf')
        group_data_upf.save()
        self.group_data_upf_pk = group_data_upf.pk

        # test auto.import group type_string: 'auto.import' -> 'core.import'
        group_autoimport = DbGroup(label='03', user_id=self.default_user.id, type_string='auto.import')
        group_autoimport.save()
        self.group_autoimport_pk = group_autoimport.pk

        # test auto.run group type_string: 'auto.run' -> 'core.auto'
        group_autorun = DbGroup(label='04', user_id=self.default_user.id, type_string='auto.run')
        group_autorun.save()
        self.group_autorun_pk = group_autorun.pk

    def test_group_string_update(self):
        """Test that the type_string were updated correctly."""
        DbGroup = self.apps.get_model('db', 'DbGroup')

        # 'user' -> 'core'
        group_user = DbGroup.objects.get(pk=self.group_user_pk)
        self.assertEqual(group_user.type_string, 'core')

        # 'data.upf' -> 'core.upf'
        group_data_upf = DbGroup.objects.get(pk=self.group_data_upf_pk)
        self.assertEqual(group_data_upf.type_string, 'core.upf')

        # 'auto.import' -> 'core.import'
        group_autoimport = DbGroup.objects.get(pk=self.group_autoimport_pk)
        self.assertEqual(group_autoimport.type_string, 'core.import')

        # 'auto.run' -> 'core.auto'
        group_autorun = DbGroup.objects.get(pk=self.group_autorun_pk)
        self.assertEqual(group_autorun.type_string, 'core.auto')
