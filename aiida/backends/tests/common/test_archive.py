# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Archive class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from aiida.backends.testbase import AiidaTestCase
from aiida.common.archive import Archive
from aiida.common.exceptions import InvalidOperation


def get_archive_file(archive):
    """
    Return the absolute path of the archive file used for testing purposes. The expected path for these files:

        aiida.backends.tests.export_import_test_files.migrate

    :param archive: the relative filename of the archive
    :returns: absolute filepath of the archive test file
    """
    dirpath_current = os.path.dirname(os.path.abspath(__file__))
    dirpath_archive = os.path.join(dirpath_current, os.pardir, 'fixtures', 'export', 'migrate')

    return os.path.join(dirpath_archive, archive)


class TestCommonArchive(AiidaTestCase):
    """Tests for the :class:`aiida.common.archive.Archive` class."""

    def test_context_required(self):
        """Verify that accessing a property of an Archive outside of a context manager raises."""
        with self.assertRaises(InvalidOperation):
            filepath = get_archive_file('export_v0.1.aiida')
            archive = Archive(filepath)
            _ = archive.version_format

    def test_version_format(self):
        """Verify that `version_format` return the correct archive format version."""
        filepath = get_archive_file('export_v0.1.aiida')
        with Archive(filepath) as archive:
            self.assertEqual(archive.version_format, '0.1')
