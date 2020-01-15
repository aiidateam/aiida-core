# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the folder class."""
import io
import os
import sys
import shutil
import tempfile
import unittest

from aiida.common.folders import Folder


def fs_encoding_is_utf8():
    """
    :return: True if the current filesystem encoding is set to UTF-8
    """

    return sys.getfilesystemencoding() == 'utf-8'


class FoldersTest(unittest.TestCase):
    """Tests for the Folder class."""

    @classmethod
    @unittest.skipUnless(
        fs_encoding_is_utf8(), ('Testing for unicode folders requires UTF-8 to be set for filesystem encoding')
    )
    def test_unicode(cls):
        """Check that there are no exceptions raised when using unicode folders."""
        tmpsource = tempfile.mkdtemp()
        tmpdest = tempfile.mkdtemp()
        with open(os.path.join(tmpsource, 'sąžininga'), 'w', encoding='utf8') as fhandle:
            fhandle.write('test')
        with open(os.path.join(tmpsource, 'žąsis'), 'w', encoding='utf8') as fhandle:
            fhandle.write('test')
        folder = Folder(tmpdest)
        folder.insert_path(tmpsource, 'destination')
        folder.insert_path(tmpsource, 'šaltinis')

        folder = Folder(os.path.join(tmpsource, 'šaltinis'))
        folder.insert_path(tmpsource, 'destination')
        folder.insert_path(tmpdest, 'kitas-šaltinis')

    def test_get_abs_path_without_limit(self):
        """
        Check that the absolute path function can get an absolute path
        """
        folder = Folder('/tmp')
        # Should not raise any exception
        self.assertEqual(folder.get_abs_path('test_file.txt'), '/tmp/test_file.txt')

    def test_create_file_from_filelike(self):
        """Test `aiida.common.folders.Folder.create_file_from_filelike`."""
        unicode_string = 'unicode_string'
        byte_string = b'byte_string'

        try:
            tempdir = tempfile.mkdtemp()
            folder = Folder(tempdir)

            folder.create_file_from_filelike(io.StringIO(unicode_string), 'random.dat', mode='w', encoding='utf-8')
            folder.create_file_from_filelike(io.BytesIO(byte_string), 'random.dat', mode='wb', encoding=None)

            with self.assertRaises(TypeError):
                folder.create_file_from_filelike(io.StringIO(unicode_string), 'random.dat', mode='wb')

            with self.assertRaises(TypeError):
                folder.create_file_from_filelike(io.BytesIO(byte_string), 'random.dat', mode='w')

        finally:
            shutil.rmtree(tempdir)
