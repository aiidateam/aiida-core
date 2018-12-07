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
import sys
import io
import unittest


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
        from aiida.common.folders import Folder
        import os
        import tempfile

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
        from aiida.common.folders import Folder

        folder = Folder('/tmp')
        # Should not raise any exception
        self.assertEqual(folder.get_abs_path('test_file.txt'), '/tmp/test_file.txt')
