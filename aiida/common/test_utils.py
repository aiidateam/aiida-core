from aiida.common.utils import get_unique_filename
import unittest

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

