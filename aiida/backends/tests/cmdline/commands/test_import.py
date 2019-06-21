# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi import`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner
from click.exceptions import BadParameter

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.archives import get_archive_file
from aiida.cmdline.commands import cmd_import
from aiida.orm import Group


class TestVerdiImport(AiidaTestCase):
    """Tests for `verdi import`."""

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_import_no_archives(self):
        """Test that passing no valid archives will lead to command failure."""
        options = []
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNotNone(result.exception, result.output)
        self.assertIn('Critical', result.output)
        self.assertNotEqual(result.exit_code, 0, result.output)

    def test_import_non_existing_archives(self):
        """Test that passing a non-existing archive will lead to command failure."""
        options = ['non-existing-archive.aiida']
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNotNone(result.exception, result.output)
        self.assertNotEqual(result.exit_code, 0, result.output)

    def test_import_archive(self):
        """
        Test import for archive files from disk

        NOTE: When the export format version is upped, the test export_v0.5.aiida archive will have to be
        replaced with the version of the new format
        """
        archives = [
            get_archive_file('calcjob/arithmetic.add.aiida'),
            get_archive_file('export/migrate/export_v0.5_simple.aiida')
        ]

        options = [] + archives
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNone(result.exception, result.output)
        self.assertEqual(result.exit_code, 0, result.output)

    def test_import_to_group(self):
        """
        Test import to existing Group and that Nodes are added correctly for multiple imports
        of the same, as well as separate, archives.
        """
        archives = [
            get_archive_file('calcjob/arithmetic.add.aiida'),
            get_archive_file('export/migrate/export_v0.5_simple.aiida')
        ]

        group_label = "import_madness"
        group = Group(group_label).store()

        self.assertTrue(group.is_empty, msg="The Group should be empty.")

        # Invoke `verdi import`, making sure there are no exceptions
        options = ['-G', group.label] + [archives[0]]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)
        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)

        self.assertFalse(group.is_empty, msg="The Group should no longer be empty.")

        nodes_in_group = group.count()

        # Invoke `verdi import` again, making sure Group count doesn't change
        options = ['-G', group.label] + [archives[0]]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)
        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)

        self.assertEqual(
            group.count(),
            nodes_in_group,
            msg="The Group count should not have changed from {}. Instead it is now {}".format(
                nodes_in_group, group.count()))

        # Invoke `verdi import` again with new archive, making sure Group count is upped
        options = ['-G', group.label] + [archives[1]]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)
        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)

        self.assertGreater(
            group.count(),
            nodes_in_group,
            msg="There should now be more than {} nodes in group {} , instead there are {}".format(
                nodes_in_group, group_label, group.count()))

    def test_import_make_new_group(self):
        """Make sure imported entities are saved in new Group"""
        # Initialization
        group_label = "new_group_for_verdi_import"
        archives = [get_archive_file('export/migrate/export_v0.5_simple.aiida')]

        # Check Group does not already exist
        group_search = Group.objects.find(filters={'label': group_label})
        self.assertEqual(
            len(group_search), 0, msg="A Group with label '{}' already exists, this shouldn't be.".format(group_label))

        # Invoke `verdi import`, making sure there are no exceptions
        options = ['-G', group_label] + archives
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)
        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)

        # Make sure new Group was created
        (group, new_group) = Group.objects.get_or_create(group_label)
        self.assertFalse(new_group, msg="The Group should not have been created now, but instead when it was imported.")
        self.assertFalse(group.is_empty, msg="The Group should not be empty.")

    def test_comment_mode(self):
        """
        Test comment mode flag works as intended
        """
        archives = [get_archive_file('export/migrate/export_v0.5_simple.aiida')]

        options = ['--comment-mode', 'newest'] + archives
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Comment mode: newest', result.output)
        self.assertEqual(result.exit_code, 0, result.output)

        options = ['--comment-mode', 'overwrite'] + archives
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Comment mode: overwrite', result.output)
        self.assertEqual(result.exit_code, 0, result.output)

    def test_import_old_local_archives(self):
        """ Test import of old local archives
        Expected behavior: Automatically migrate to newest version and import correctly.
        """
        archives = [('export/migrate/export_v0.1_simple.aiida', '0.1'),
                    ('export/migrate/export_v0.2_simple.aiida', '0.2'),
                    ('export/migrate/export_v0.3_simple.aiida', '0.3'),
                    ('export/migrate/export_v0.4_simple.aiida', '0.4')]

        for archive, version in archives:
            options = [get_archive_file(archive)]
            result = self.cli_runner.invoke(cmd_import.cmd_import, options)

            self.assertIsNone(result.exception, msg=result.output)
            self.assertEqual(result.exit_code, 0, msg=result.output)
            self.assertIn(version, result.output, msg=result.exception)
            self.assertIn("Success: imported archive {}".format(options[0]), result.output, msg=result.exception)

    def test_import_old_url_archives(self):
        """ Test import of old URL archives
        Expected behavior: Automatically migrate to newest version and import correctly.
        TODO: Update 'url' to point at correct commit and file.
        Now it is pointing to yakutovicha's commit, but when PR #2478 has been merged in aiidateam:develop,
        url should be updated to point to the, essentially same, commit, but in aiidateam.
        Furthermore, the filename should be changed from '_no_UPF.aiida' to '_simple.aiida'.
        """
        url = "https://raw.githubusercontent.com/yakutovicha/aiida_core/f5fff1846a62051b898f13db67f5eef18892d5f4/"
        archive_path = "aiida/backends/tests/fixtures/export/migrate/"
        archive = 'export_v0.3_no_UPF.aiida'
        version = '0.3'

        options = [url + archive_path + archive]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertIn(version, result.output, msg=result.exception)
        self.assertIn("Success: imported archive {}".format(options[0]), result.output, msg=result.exception)

    def test_import_url_and_local_archives(self):
        """Test import of both a remote and local archive
        TODO: Update 'url' to point at correct commit and file.
        Now it is pointing to yakutovicha's commit, but when PR #2478 has been merged in aiidateam:develop,
        url should be updated to point to the, essentially same, commit, but in aiidateam.
        Furthermore, the filename should be change from '_no_UPF.aiida' to '_simple.aiida'.
        """
        url = "https://raw.githubusercontent.com/yakutovicha/aiida_core/f5fff1846a62051b898f13db67f5eef18892d5f4/"
        url_archive = "aiida/backends/tests/fixtures/export/migrate/export_v0.4_no_UPF.aiida"
        local_archive = "export/migrate/export_v0.5_simple.aiida"

        options = [get_archive_file(local_archive), url + url_archive, get_archive_file(local_archive)]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNone(result.exception, result.output)
        self.assertEqual(result.exit_code, 0, result.output)

    def test_import_url_timeout(self):
        """Test a timeout to valid URL is correctly errored"""
        from aiida.cmdline.params.types import ImportPath

        timeout_url = "http://www.google.com:81"

        test_timeout_path = ImportPath(exists=True, readable=True, timeout_seconds=0)
        with self.assertRaises(BadParameter) as cmd_exc:
            test_timeout_path(timeout_url)

        error_message = 'Path "{}" could not be reached within 0 s.'.format(timeout_url)
        self.assertIn(error_message, str(cmd_exc.exception), str(cmd_exc.exception))

    def test_raise_malformed_url(self):
        """Test the correct error is raised when supplying a malformed URL"""
        malformed_url = "htp://www.aiida.net"

        result = self.cli_runner.invoke(cmd_import.cmd_import, [malformed_url])

        self.assertIsNotNone(result.exception, result.output)
        self.assertNotEqual(result.exit_code, 0, result.output)

        error_message = 'It may be neither a valid path nor a valid URL.'
        self.assertIn(error_message, result.output, result.exception)

    def test_non_interactive_and_migration(self):
        """Test options `--non-interactive` and `--migration`/`--no-migration`
        `migration` = True (default), `non_interactive` = False (default), Expected: Query user, migrate
        `migration` = True (default), `non_interactive` = True, Expected: No query, migrate
        `migration` = False, `non_interactive` = False (default), Expected: No query, no migrate
        `migration` = False, `non_interactive` = True, Expected: No query, no migrate
        """
        archive = get_archive_file('export/migrate/export_v0.4_simple.aiida')
        confirm_message = "Do you want to try and migrate {} to the newest export file version?".format(archive)
        success_message = "Success: imported archive {}".format(archive)

        # Import "normally", but explicitly specifying `--migration`, make sure confirm message is present
        # `migration` = True (default), `non_interactive` = False (default), Expected: Query user, migrate
        options = ['--migration', archive]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)

        self.assertIn(confirm_message, result.output, msg=result.exception)
        self.assertIn(success_message, result.output, msg=result.exception)

        # Import using non-interactive, make sure confirm message has gone
        # `migration` = True (default), `non_interactive` = True, Expected: No query, migrate
        options = ['--non-interactive', archive]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNone(result.exception, msg=result.output)
        self.assertEqual(result.exit_code, 0, msg=result.output)

        self.assertNotIn(confirm_message, result.output, msg=result.exception)
        self.assertIn(success_message, result.output, msg=result.exception)

        # Import using `--no-migration`, make sure confirm message has gone
        # `migration` = False, `non_interactive` = False (default), Expected: No query, no migrate
        options = ['--no-migration', archive]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNotNone(result.exception, msg=result.output)
        self.assertNotEqual(result.exit_code, 0, msg=result.output)

        self.assertNotIn(confirm_message, result.output, msg=result.exception)
        self.assertNotIn(success_message, result.output, msg=result.exception)

        # Import using `--no-migration` and `--non-interactive`, make sure confirm message has gone
        # `migration` = False, `non_interactive` = True, Expected: No query, no migrate
        options = ['--no-migration', '--non-interactive', archive]
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNotNone(result.exception, msg=result.output)
        self.assertNotEqual(result.exit_code, 0, msg=result.output)

        self.assertNotIn(confirm_message, result.output, msg=result.exception)
        self.assertNotIn(success_message, result.output, msg=result.exception)
