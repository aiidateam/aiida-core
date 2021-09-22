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
"""Test migration that updates node types after `core.` prefix was added to entry point names."""
from .test_migrations_common import TestMigrations


class TestMigration(TestMigrations):
    """Test migration that updates node types after `core.` prefix was added to entry point names."""

    migrate_from = '0048_computer_name_to_label'
    migrate_to = '0049_entry_point_core_prefix'

    def setUpBeforeMigration(self):
        DbComputer = self.apps.get_model('db', 'DbComputer')
        DbNode = self.apps.get_model('db', 'DbNode')

        computer = DbComputer(label='testing', scheduler_type='direct', transport_type='local')
        computer.save()
        self.computer_pk = computer.pk

        calcjob = DbNode(
            user_id=self.default_user.id,
            process_type='aiida.calculations:core.arithmetic.add',
            attributes={'parser_name': 'core.arithmetic.add'}
        )
        calcjob.save()
        self.calcjob_pk = calcjob.pk

        workflow = DbNode(user_id=self.default_user.id, process_type='aiida.workflows:arithmetic.add_multiply')
        workflow.save()
        self.workflow_pk = workflow.pk

    def test_migration(self):
        """Test that the migration was performed correctly."""
        DbComputer = self.apps.get_model('db', 'DbComputer')
        DbNode = self.apps.get_model('db', 'DbNode')

        computer = DbComputer.objects.get(pk=self.computer_pk)
        assert computer.scheduler_type == 'core.direct'
        assert computer.transport_type == 'core.local'

        calcjob = DbNode.objects.get(pk=self.calcjob_pk)
        assert calcjob.process_type == 'aiida.calculations:core.arithmetic.add'
        assert calcjob.attributes['parser_name'] == 'core.arithmetic.add'

        workflow = DbNode.objects.get(pk=self.workflow_pk)
        assert workflow.process_type == 'aiida.workflows:core.arithmetic.add_multiply'
