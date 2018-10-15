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
from __future__ import absolute_import
import os

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_import


def get_archive_file(archive):
    """
    Return the absolute path of the archive file used for testing purposes. The expected base path for these files:

        aiida.backends.tests.fixtures

    :param archive: the relative filename of the archive
    :returns: absolute filepath of the archive test file
    """
    dirpath_current = os.path.dirname(os.path.abspath(__file__))
    dirpath_archive = os.path.join(dirpath_current, os.pardir, os.pardir, 'fixtures')

    return os.path.join(dirpath_archive, archive)


class TestVerdiImport(AiidaTestCase):
    """Tests for `verdi import`."""

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_import_no_archives(self):
        """Test that passing no valid archives will lead to command failure."""
        options = []
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNotNone(result.exception)
        self.assertIn('Critical', result.output)

    def test_import_non_existing_archives(self):
        """Test that passing a non-existing archive will lead to command failure."""
        options = ['non-existing-archive.aiida']
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNotNone(result.exception)

    def test_import_archive(self):
        """
        Test import for archive files from disk

        Note that when the export format version is upped, the test export_v0.3.aiida archive will have to be
        replaced with the version of the new format
        """
        archives = [
            get_archive_file('calculation/simpleplugins.arithmetic.add.aiida'),
            get_archive_file('export/migrate/export_v0.3.aiida')
        ]

        options = [] + archives
        result = self.cli_runner.invoke(cmd_import.cmd_import, options)

        self.assertIsNone(result.exception)
