# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi export`."""
import errno
import os
import tempfile
import tarfile
import traceback
import zipfile

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.archives import get_archive_file
from aiida.cmdline.commands import cmd_export
from aiida.tools.importexport import EXPORT_VERSION


def delete_temporary_file(filepath):
    """Attempt to delete a file, given an absolute path. If the deletion fails because the file does not exist
    the exception will be caught and passed. Any other exceptions will raise.

    :param filepath: the absolute file path"""

    try:
        os.remove(filepath)
    except OSError as exception:
        if exception.errno != errno.ENOENT:
            raise
        else:
            pass


class TestVerdiExport(AiidaTestCase):
    """Tests for `verdi export`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        from aiida import orm

        cls.computer = orm.Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida'
        ).store()

        cls.code = orm.Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.group = orm.Group(label='test_group').store()
        cls.node = orm.Data().store()

        # some of the export tests write in the current directory,
        # make sure it is writeable and we don't pollute the current one
        cls.old_cwd = os.getcwd()
        cls.cwd = tempfile.mkdtemp(__name__)
        os.chdir(cls.cwd)

        # Utility helper
        cls.fixture_archive = 'export/migrate'
        cls.newest_archive = 'export_v{}_simple.aiida'.format(EXPORT_VERSION)
        cls.penultimate_archive = 'export_v0.6_simple.aiida'

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        os.chdir(cls.old_cwd)
        os.rmdir(cls.cwd)

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_create_file_already_exists(self):
        """Test that using a file that already exists, which is the case when using NamedTemporaryFile, will raise."""
        with tempfile.NamedTemporaryFile() as handle:
            options = [handle.name]
            result = self.cli_runner.invoke(cmd_export.create, options)
            self.assertIsNotNone(result.exception)

    def test_create_force(self):
        """
        Test that using a file that already exists, which is the case when using NamedTemporaryFile, will work
        when the -f/--force parameter is used
        """
        with tempfile.NamedTemporaryFile() as handle:
            options = ['-f', handle.name]
            result = self.cli_runner.invoke(cmd_export.create, options)
            self.assertIsNone(result.exception, result.output)

            options = ['--force', handle.name]
            result = self.cli_runner.invoke(cmd_export.create, options)
            self.assertIsNone(result.exception, result.output)

    def test_create_zip(self):
        """Test that creating an archive for a set of various ORM entities works with the zip format."""
        filename = next(tempfile._get_candidate_names())  # pylint: disable=protected-access
        try:
            options = [
                '-X', self.code.pk, '-Y', self.computer.pk, '-G', self.group.pk, '-N', self.node.pk, '-F', 'zip',
                filename
            ]
            result = self.cli_runner.invoke(cmd_export.create, options)
            self.assertIsNone(result.exception, ''.join(traceback.format_exception(*result.exc_info)))
            self.assertTrue(os.path.isfile(filename))
            self.assertFalse(zipfile.ZipFile(filename).testzip(), None)
        finally:
            delete_temporary_file(filename)

    def test_create_zip_uncompressed(self):
        """Test that creating an archive for a set of various ORM entities works with the zip-uncompressed format."""
        filename = next(tempfile._get_candidate_names())  # pylint: disable=protected-access
        try:
            options = [
                '-X', self.code.pk, '-Y', self.computer.pk, '-G', self.group.pk, '-N', self.node.pk, '-F',
                'zip-uncompressed', filename
            ]
            result = self.cli_runner.invoke(cmd_export.create, options)
            self.assertIsNone(result.exception, ''.join(traceback.format_exception(*result.exc_info)))
            self.assertTrue(os.path.isfile(filename))
            self.assertFalse(zipfile.ZipFile(filename).testzip(), None)
        finally:
            delete_temporary_file(filename)

    def test_create_tar_gz(self):
        """Test that creating an archive for a set of various ORM entities works with the tar.gz format."""
        filename = next(tempfile._get_candidate_names())  # pylint: disable=protected-access
        try:
            options = [
                '-X', self.code.pk, '-Y', self.computer.pk, '-G', self.group.pk, '-N', self.node.pk, '-F', 'tar.gz',
                filename
            ]
            result = self.cli_runner.invoke(cmd_export.create, options)
            self.assertIsNone(result.exception, ''.join(traceback.format_exception(*result.exc_info)))
            self.assertTrue(os.path.isfile(filename))
            self.assertTrue(tarfile.is_tarfile(filename))
        finally:
            delete_temporary_file(filename)

    def test_migrate_versions_old(self):
        """Migrating archives with a version older than the current should work."""
        archives = []
        for version in range(1, int(EXPORT_VERSION.split('.')[-1]) - 1):
            archives.append('export_v0.{}_simple.aiida'.format(version))

        for archive in archives:

            filename_input = get_archive_file(archive, filepath=self.fixture_archive)
            filename_output = next(tempfile._get_candidate_names())  # pylint: disable=protected-access

            try:
                options = [filename_input, filename_output]
                result = self.cli_runner.invoke(cmd_export.migrate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename_output))
                self.assertEqual(zipfile.ZipFile(filename_output).testzip(), None)
            finally:
                delete_temporary_file(filename_output)

    def test_migrate_versions_recent(self):
        """Migrating an archive with the current version should exit with non-zero status."""
        filename_input = get_archive_file(self.newest_archive, filepath=self.fixture_archive)
        filename_output = next(tempfile._get_candidate_names())  # pylint: disable=protected-access

        try:
            options = [filename_input, filename_output]
            result = self.cli_runner.invoke(cmd_export.migrate, options)
            self.assertIsNotNone(result.exception)
        finally:
            delete_temporary_file(filename_output)

    def test_migrate_force(self):
        """Test that passing the -f/--force option will overwrite the output file even if it exists."""
        filename_input = get_archive_file(self.penultimate_archive, filepath=self.fixture_archive)

        # Using the context manager will create the file and so the command should fail
        with tempfile.NamedTemporaryFile() as file_output:
            options = [filename_input, file_output.name]
            result = self.cli_runner.invoke(cmd_export.migrate, options)
            self.assertIsNotNone(result.exception)

        for option in ['-f', '--force']:
            # Using the context manager will create the file, but we pass the force flag so it should work
            with tempfile.NamedTemporaryFile() as file_output:
                filename_output = file_output.name
                options = [option, filename_input, filename_output]
                result = self.cli_runner.invoke(cmd_export.migrate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename_output))
                self.assertEqual(zipfile.ZipFile(filename_output).testzip(), None)

    def test_migrate_silent(self):
        """Test that the captured output is an empty string when the -s/--silent option is passed."""
        filename_input = get_archive_file(self.penultimate_archive, filepath=self.fixture_archive)
        filename_output = next(tempfile._get_candidate_names())  # pylint: disable=protected-access

        for option in ['-s', '--silent']:
            try:
                options = [option, filename_input, filename_output]
                result = self.cli_runner.invoke(cmd_export.migrate, options)
                self.assertEqual(result.output, '')
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename_output))
                self.assertEqual(zipfile.ZipFile(filename_output).testzip(), None)
            finally:
                delete_temporary_file(filename_output)

    def test_migrate_tar_gz(self):
        """Test that -F/--archive-format option can be used to write a tar.gz instead."""
        filename_input = get_archive_file(self.penultimate_archive, filepath=self.fixture_archive)
        filename_output = next(tempfile._get_candidate_names())  # pylint: disable=protected-access

        for option in ['-F', '--archive-format']:
            try:
                options = [option, 'tar.gz', filename_input, filename_output]
                result = self.cli_runner.invoke(cmd_export.migrate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename_output))
                self.assertTrue(tarfile.is_tarfile(filename_output))
            finally:
                delete_temporary_file(filename_output)

    def test_inspect(self):
        """Test the functionality of `verdi export inspect`."""
        archives = []
        for version in range(1, int(EXPORT_VERSION.split('.')[-1])):
            archives.append(('export_v0.{}_simple.aiida'.format(version), '0.{}'.format(version)))

        for archive, version_number in archives:

            filename_input = get_archive_file(archive, filepath=self.fixture_archive)

            # Testing the options that will print the meta data and data respectively
            for option in ['-m', '-d']:
                options = [option, filename_input]
                result = self.cli_runner.invoke(cmd_export.inspect, options)
                self.assertIsNone(result.exception, result.output)

            # Test the --version option which should print the archive format version
            options = ['--version', filename_input]
            result = self.cli_runner.invoke(cmd_export.inspect, options)
            self.assertIsNone(result.exception, result.output)
            self.assertEqual(result.output.strip(), version_number)

    def test_inspect_empty_archive(self):
        """Test the functionality of `verdi export inspect` for an empty archive."""
        filename_input = get_archive_file('empty.aiida', filepath=self.fixture_archive)

        options = [filename_input]
        result = self.cli_runner.invoke(cmd_export.inspect, options)
        self.assertIsNotNone(result.exception, result.output)
        self.assertIn('corrupt archive', result.output)
