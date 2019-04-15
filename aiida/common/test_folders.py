# -*- coding: utf-8 -*-
import unittest

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class FoldersTest(unittest.TestCase):
    """
    Tests for the Folder class.
    """

    def test_unicode(self):
        """
        Check that there are no exceptions raised when 
        using unicode folders.
        """
        from aiida.common.folders import Folder
        import os, tempfile

        tmpsource = tempfile.mkdtemp()
        tmpdest = tempfile.mkdtemp()
        with open(os.path.join(tmpsource, "sąžininga"), 'w') as f:
            f.write("test")
        with open(os.path.join(tmpsource, "žąsis"), 'w') as f:
            f.write("test")
        fd = Folder(tmpdest)
        fd.insert_path(tmpsource, "destination")
        fd.insert_path(tmpsource, u"šaltinis")

        fd = Folder(os.path.join(tmpsource, u"šaltinis"))
        fd.insert_path(tmpsource, "destination")
        fd.insert_path(tmpdest, u"kitas-šaltinis")


    def test_get_abs_path_without_limit(self):
        from aiida.common.folders import Folder

        fd = Folder('/tmp')
        # Should not raise any exception
        self.assertEquals(fd.get_abs_path('test_file.txt'),
                          '/tmp/test_file.txt')
