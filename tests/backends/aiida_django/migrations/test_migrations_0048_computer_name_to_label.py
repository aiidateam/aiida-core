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
"""Test migration that renames the ``name`` column of the ``Computer`` entity to ``label``."""
from .test_migrations_common import TestMigrations


class TestMigration(TestMigrations):
    """Test migration that renames the ``name`` column of the ``Computer`` entity to ``label``."""

    migrate_from = '0047_migrate_repository'
    migrate_to = '0048_computer_name_to_label'

    def setUpBeforeMigration(self):
        DbComputer = self.apps.get_model('db', 'DbComputer')

        computer = DbComputer(name='testing')
        computer.save()
        self.computer_pk = computer.pk

    def test_migration(self):
        """Test that the migration was performed correctly."""
        DbComputer = self.apps.get_model('db', 'DbComputer')

        computer = DbComputer.objects.get(pk=self.computer_pk)
        assert computer.label == 'testing'
