# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `FolderData` class."""

import os
import shutil
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import FolderData


class TestFolderData(AiidaTestCase):
    """Test for the `FolderData` class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.tempdir = tempfile.mkdtemp()
        cls.tree = {
            'a.txt': 'Content of file A\nWith some newlines',
            'b.txt': 'Content of file B without newline',
        }

        for filename, content in cls.tree.items():
            with open(os.path.join(cls.tempdir, filename), 'w', encoding='utf8') as handle:
                handle.write(content)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        shutil.rmtree(cls.tempdir)

    def test_constructor_tree(self):
        """Test the `tree` constructor keyword."""
        node = FolderData(tree=self.tempdir)
        self.assertEqual(sorted(node.list_object_names()), sorted(self.tree.keys()))
