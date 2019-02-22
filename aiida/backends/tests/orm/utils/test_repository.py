# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Repository` utility class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import shutil
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Node


class TestRepository(AiidaTestCase):
    """Tests for the node `Repository` utility class."""

    def setUp(self):
        """Create a dummy file tree."""
        self.tempdir = tempfile.mkdtemp()
        self.tree = {
            'subdir': {
                'a.txt': u'Content of file A\nWith some newlines',
                'b.txt': u'Content of file B without newline',
            },
            'c.txt': u'Content of file C\n',
        }

        self.create_file_tree(self.tempdir, self.tree)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def create_file_tree(self, directory, tree):
        """Create a file tree in the given directory.

        :param directory: the absolute path of the directory into which to create the tree
        :param tree: a dictionary representing the tree structure
        """
        for key, value in tree.items():
            if isinstance(value, dict):
                subdir = os.path.join(directory, key)
                os.makedirs(subdir)
                self.create_file_tree(subdir, value)
            else:
                with io.open(os.path.join(directory, key), 'w', encoding='utf8') as handle:
                    handle.write(value)

    def get_file_content(self, key):
        """Get the content of a file for a given key.

        :param key: the nested key of the file to retrieve
        :return: the content of the file
        """
        parts = key.split(os.sep)
        content = self.tree
        for part in parts:
            content = content[part]

        return content

    def test_put_object_from_filelike(self):
        """Test the `put_object_from_filelike` method."""
        key = os.path.join('subdir', 'a.txt')
        filepath = os.path.join(self.tempdir, key)
        content = self.get_file_content(key)

        with io.open(filepath, 'r') as handle:
            node = Node()
            node.put_object_from_filelike(handle, key)
            self.assertEqual(node.get_object_content(key), content)

    def test_put_object_from_file(self):
        """Test the `put_object_from_file` method."""
        key = os.path.join('subdir', 'a.txt')
        filepath = os.path.join(self.tempdir, key)
        content = self.get_file_content(key)

        node = Node()
        node.put_object_from_file(filepath, key)
        self.assertEqual(node.get_object_content(key), content)

    def test_put_object_from_tree(self):
        """Test the `put_object_from_tree` method."""
        basepath = ''
        node = Node()
        node.put_object_from_tree(self.tempdir, basepath)

        key = os.path.join('subdir', 'a.txt')
        content = self.get_file_content(key)
        self.assertEqual(node.get_object_content(key), content)

        basepath = 'base'
        node = Node()
        node.put_object_from_tree(self.tempdir, basepath)

        key = os.path.join(basepath, 'subdir', 'a.txt')
        content = self.get_file_content(os.path.join('subdir', 'a.txt'))
        self.assertEqual(node.get_object_content(key), content)

        basepath = 'base/further/nested'
        node = Node()
        node.put_object_from_tree(self.tempdir, basepath)

        key = os.path.join(basepath, 'subdir', 'a.txt')
        content = self.get_file_content(os.path.join('subdir', 'a.txt'))
        self.assertEqual(node.get_object_content(key), content)
