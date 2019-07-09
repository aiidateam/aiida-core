# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Archive class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common.archive import Archive, CorruptArchive
from aiida.common.exceptions import InvalidOperation
from aiida.backends.tests.utils.archives import get_archive_file


class TestCommonArchive(AiidaTestCase):
    """Tests for the :py:class:`~aiida.common.archive.Archive` class."""

    def test_context_required(self):
        """Verify that accessing a property of an Archive outside of a context manager raises."""
        with self.assertRaises(InvalidOperation):
            filepath = get_archive_file('export_v0.1_simple.aiida', filepath='export/migrate')
            archive = Archive(filepath)
            archive.version_format  # pylint: disable=pointless-statement

    def test_version_format(self):
        """Verify that `version_format` return the correct archive format version."""
        filepath = get_archive_file('export_v0.1_simple.aiida', filepath='export/migrate')
        with Archive(filepath) as archive:
            self.assertEqual(archive.version_format, '0.1')

    def test_empty_archive(self):
        """Verify that attempting to unpack an empty archive raises a `CorruptArchive` exception."""
        filepath = get_archive_file('empty.aiida', filepath='export/migrate')
        with self.assertRaises(CorruptArchive):
            with Archive(filepath) as archive:
                archive.version_format  # pylint: disable=pointless-statement
