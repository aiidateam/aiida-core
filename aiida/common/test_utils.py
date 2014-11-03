# -*- coding: utf-8 -*-
from aiida.common.utils import get_unique_filename
import unittest

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class UniqueTest(unittest.TestCase):
    """
    Tests for the get_unique_filename function.
    """

    def test_unique_1(self):
        filename = "different.txt"
        filename_list = ["file1.txt", "file2.txt"]
        
        self.assertEqual(filename,
                         get_unique_filename(filename, filename_list))

    def test_unique_2(self):
        filename = "file1.txt"
        filename_list = ["file1.txt", "file2.txt"]
        
        self.assertEqual("file1-1.txt",
                         get_unique_filename(filename, filename_list))


    def test_unique_3(self):
        filename = "file1.txt"
        filename_list = ["file1.txt", "file1-1.txt"]
        
        self.assertEqual("file1-2.txt",
                         get_unique_filename(filename, filename_list))

    def test_unique_4(self):
        filename = "file1.txt"
        filename_list = ["file1.txt", "file1-2.txt"]
        
        self.assertEqual("file1-1.txt",
                         get_unique_filename(filename, filename_list))

