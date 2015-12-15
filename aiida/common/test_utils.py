# -*- coding: utf-8 -*-
from aiida.common.utils import get_unique_filename
import unittest

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Eric Hontz, Giovanni Pizzi, Martin Uhrin"


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

