# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from six.moves import range

import tempfile

from django.apps import apps
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import IntegrityError
from aiida.manage.database.integrity import deduplicate_node_uuids, verify_node_uuid_uniqueness
from aiida.utils.capturing import Capturing


class TestMigrations(AiidaTestCase):

    @property
    def app(self):
        return apps.get_containing_app_config(type(self).__module__).name.split('.')[-1]

    migrate_from = None
    migrate_to = None

    def setUp(self):
        """Go to a specific schema version before running tests."""
        assert self.migrate_from and self.migrate_to, \
            "TestCase '{}' must define migrate_from and migrate_to properties".format(type(self).__name__)
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        try:
            self.setUpBeforeMigration(old_apps)
            # Run the migration to test
            executor = MigrationExecutor(connection)
            executor.loader.build_graph()
            executor.migrate(self.migrate_to)

            self.apps = executor.loader.project_state(self.migrate_to).apps
        except Exception:
            # Bring back the DB to the correct state if this setup part fails
            self._revert_database_schema()
            raise


    def tearDown(self):
        """At the end make sure we go back to the latest schema version."""
        self._revert_database_schema()

    def setUpBeforeMigration(self, apps):
        """
        Anything to do before running the migrations. 
        This is typically implemented in test subclasses.
        """
        pass

    def _revert_database_schema(self):
        """Bring back the DB to the correct state."""
        from ..migrations import LATEST_MIGRATION
        self.migrate_to = [(self.app, LATEST_MIGRATION)]
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)


class TestDuplicateNodeUuidMigration(TestMigrations):

    migrate_from = '0013_django_1_8'
    migrate_to = '0014_add_node_uuid_unique_constraint'

    def setUpBeforeMigration(self, apps):
        from aiida.orm.data.bool import Bool
        from aiida.orm.data.int import Int

        self.file_name = 'test.temp'
        self.file_content = '#!/bin/bash\n\necho test run\n'

        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(self.file_content)
            handle.flush()

            self.nodes_boolean = []
            self.nodes_integer = []
            self.n_bool_duplicates = 2
            self.n_int_duplicates = 4

            node_bool = Bool(True)
            node_bool.add_path(handle.name, self.file_name)
            node_bool.store()

            node_int = Int(1)
            node_int.add_path(handle.name, self.file_name)
            node_int.store()

            self.nodes_boolean.append(node_bool)
            self.nodes_integer.append(node_int)

            for i in range(self.n_bool_duplicates):
                node = Bool(True)
                node.dbnode.uuid = node_bool.uuid
                node.add_path(handle.name, self.file_name)
                node.store()
                self.nodes_boolean.append(node)

            for i in range(self.n_int_duplicates):
                node = Int(1)
                node.dbnode.uuid = node_int.uuid
                node.add_path(handle.name, self.file_name)
                node.store()
                self.nodes_integer.append(node)

        # Verify that there are duplicate UUIDs by checking that the following function raises
        with self.assertRaises(IntegrityError):
            verify_node_uuid_uniqueness()

        # Now run the function responsible for solving duplicate UUIDs which would also be called by the user
        # through the `verdi database integrity duplicate-node-uuid` command
        deduplicate_node_uuids(dry_run=False)

    def test_deduplicated_uuids(self):
        """Verify that after the migration, all expected nodes are still there with unique UUIDs."""
        from aiida.orm import load_node

        # If the duplicate UUIDs were successfully fixed, the following should not raise.
        verify_node_uuid_uniqueness()

        # Reload the nodes by PK and check that all UUIDs are now unique
        nodes_boolean = [load_node(node.pk) for node in self.nodes_boolean]
        uuids_boolean = [node.uuid for node in nodes_boolean]
        self.assertEqual(len(set(uuids_boolean)), len(nodes_boolean))

        nodes_integer = [load_node(node.pk) for node in self.nodes_integer]
        uuids_integer = [node.uuid for node in nodes_integer]
        self.assertEqual(len(set(uuids_integer)), len(nodes_integer))

        for node in nodes_boolean:
            with node._get_folder_pathsubfolder.open(self.file_name) as handle:
                content = handle.read()
                self.assertEqual(content, self.file_content)


class TestUuidMigration(TestMigrations):

    migrate_from = '0017_drop_dbcalcstate'
    migrate_to = '0018_django_1_11'

    def setUpBeforeMigration(self, apps):
        from aiida.orm import Data

        n = Data().store()
        self.node_uuid = n.uuid
        self.node_id = n.id

    def test_uuid_untouched(self):
        """Verify that Node uuids remain unchanged."""
        from aiida.orm import load_node

        n = load_node(self.node_id)
        self.assertEqual(self.node_uuid, n.uuid)

class TestGroupRenamingMigration(TestMigrations):

    migrate_from = '0019_dbgroup_name2label_type2type_string'
    migrate_to = '0020_dbgroup_type_string_change_content'

    def setUpBeforeMigration(self, apps):
        from aiida.orm import Node

        # Create group
        DbGroup = apps.get_model('db', 'DbGroup')
        default_user = self.backend.users.create("{}@aiida.net".format(self.id())).store()

        # test user group type_string: '' -> 'user'
        group_user = DbGroup(label='test_user_group', user_id = default_user.id, type_string='')
        group_user.save()
        self.group_user_pk = group_user.pk

        # test data.upf group type_string: 'data.upf.family' -> 'data.upf'
        group_data_upf = DbGroup(label='test_data_upf_group', user_id = default_user.id, type_string='data.upf.family')
        group_data_upf.save()
        self.group_data_upf_pk = group_data_upf.pk

        # test auto.import group type_string: 'aiida.import' -> 'auto.import'
        group_autoimport = DbGroup(label='test_import_group', user_id = default_user.id, type_string='aiida.import')
        group_autoimport.save()
        self.group_autoimport_pk = group_autoimport.pk

        # test auto.run group type_string: 'autogroup.run' -> 'auto.run'
        group_autorun = DbGroup(label='test_autorun_group', user_id = default_user.id, type_string='autogroup.run')
        group_autorun.save()
        self.group_autorun_pk = group_autorun.pk


    def test_group_string_update(self):
        from aiida.backends.djsite.db.models import DbGroup

        # test user group type_string: '' -> 'user'
        group_user = DbGroup.objects.get(pk = self.group_user_pk)
        self.assertEqual(group_user.type_string, 'user')

        # test data.upf group type_string: 'data.upf.family' -> 'data.upf'
        group_data_upf = DbGroup.objects.get(pk = self.group_data_upf_pk)
        self.assertEqual(group_data_upf.type_string, 'data.upf')

        # test auto.import group type_string: 'aiida.import' -> 'auto.import'
        group_autoimport = DbGroup.objects.get(pk = self.group_autoimport_pk)
        self.assertEqual(group_autoimport.type_string, 'auto.import')

        # test auto.run group type_string: 'autogroup.run' -> 'auto.run'
        group_autorun = DbGroup.objects.get(pk = self.group_autorun_pk)
        self.assertEqual(group_autorun.type_string, 'auto.run')

class TestNoMigrations(AiidaTestCase):

    def test_no_remaining_migrations(self):
        """Verify that no django migrations remain.

        Equivalent to python manage.py makemigrations --check"""

        from django.core.management import call_command

        # Raises SystemExit, if migrations remain
        call_command("makemigrations", "--check", verbosity=0)
