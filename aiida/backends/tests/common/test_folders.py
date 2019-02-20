# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for the folder class
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import sys
import shutil
import tempfile
import unittest

import six

from aiida.common.folders import Folder


def fs_encoding_is_utf8():
    """
    :return: True if the current filesystem encoding is set to UTF-8
    """

    return sys.getfilesystemencoding() == 'utf-8'


class FoldersTest(unittest.TestCase):
    """
    Tests for the Folder class.
    """

    @classmethod
    @unittest.skipUnless(fs_encoding_is_utf8(), ("Testing for unicode folders "
                                                 "requires UTF-8 to be set for filesystem encoding"))
    def test_unicode(cls):
        """
        Check that there are no exceptions raised when
        using unicode folders.
        """
        tmpsource = tempfile.mkdtemp()
        tmpdest = tempfile.mkdtemp()
        with io.open(os.path.join(tmpsource, "sąžininga"), 'w', encoding='utf8') as fhandle:
            fhandle.write(u"test")
        with io.open(os.path.join(tmpsource, "žąsis"), 'w', encoding='utf8') as fhandle:
            fhandle.write(u"test")
        folder = Folder(tmpdest)
        folder.insert_path(tmpsource, "destination")
        folder.insert_path(tmpsource, u"šaltinis")

        folder = Folder(os.path.join(tmpsource, u"šaltinis"))
        folder.insert_path(tmpsource, "destination")
        folder.insert_path(tmpdest, u"kitas-šaltinis")

    def test_get_abs_path_without_limit(self):
        """
        Check that the absolute path function can get an absolute path
        """
        folder = Folder('/tmp')
        # Should not raise any exception
        self.assertEqual(folder.get_abs_path('test_file.txt'), '/tmp/test_file.txt')

    @staticmethod
    @unittest.skipUnless(six.PY2, 'test is only for python2')
    def test_create_file_from_filelike_py2():
        """Test `aiida.common.folders.Folder.create_file_from_filelike` for python 2."""
        unicode_string = u'unicode_string'
        byte_string = 'byte_string'

        try:
            tempdir = tempfile.mkdtemp()
            folder = Folder(tempdir)

            # Passing a stream with matching file mode should work ofcourse
            folder.create_file_from_filelike(six.StringIO(unicode_string), 'random.dat', mode='w', encoding='utf-8')
            folder.create_file_from_filelike(six.StringIO(byte_string), 'random.dat', mode='wb', encoding=None)

            # For python 2 the `create_file_from_filelike` should be able to deal with incoherent arguments, such as
            # the examples below where a unicode string is passed with a binary mode, or a byte stream in unicode mode.
            folder.create_file_from_filelike(six.StringIO(unicode_string), 'random.dat', mode='wb', encoding=None)
            folder.create_file_from_filelike(six.StringIO(byte_string), 'random.dat', mode='w', encoding='utf-8')

        finally:
            shutil.rmtree(tempdir)

    @unittest.skipUnless(six.PY3, 'test is only for python3')
    def test_create_file_from_filelike_py3(self):
        """Test `aiida.common.folders.Folder.create_file_from_filelike` for python 3."""
        unicode_string = 'unicode_string'
        byte_string = b'byte_string'

        try:
            tempdir = tempfile.mkdtemp()
            folder = Folder(tempdir)

            folder.create_file_from_filelike(six.StringIO(unicode_string), 'random.dat', mode='w', encoding='utf-8')
            folder.create_file_from_filelike(six.BytesIO(byte_string), 'random.dat', mode='wb', encoding=None)

            # For python three we make no exceptions, if you pass a unicode stream with binary mode, one should expect
            # a TypeError. Same for the inverse case of wanting to write in unicode mode but passing a byte stream
            with self.assertRaises(TypeError):
                folder.create_file_from_filelike(six.StringIO(unicode_string), 'random.dat', mode='wb')

            with self.assertRaises(TypeError):
                folder.create_file_from_filelike(six.BytesIO(byte_string), 'random.dat', mode='w')

        finally:
            shutil.rmtree(tempdir)
