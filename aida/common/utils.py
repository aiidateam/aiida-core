import os, os.path
import string

def get_suggestion(provided_string,allowed_strings):
    """
    Given a string and a list of allowed_strings, it returns a string to print
    on screen, with sensible text depending on whether no suggestion is found,
    or one or more than one suggestions are found.

    Args:
        provided_string: the string to compare
        allowed_strings: a list of valid strings
    
    Returns:
        A string to print on output, to suggest to the user a possible valid
        value.
    """
    import difflib
    
    similar_kws = difflib.get_close_matches(provided_string,
                                            allowed_strings)
    if len(similar_kws)==1:
        return "(Maybe you wanted to specify {0}?)".format(similar_kws[0])
    elif len(similar_kws)>1:
        return "(Maybe you wanted to specify one of these: {0}?)".format(
            string.join(similar_kws,', '))
    else:
        return "(No similar keywords found...)"


def get_unique_filename(filename, list_of_filenames):
    """
    Return a unique filename that can be added to the list_of_filenames.
    
    If filename is not in list_of_filenames, it simply returns the filename
    string itself. Otherwise, it appends a integer number to the filename
    (before the extension) until it finds a unique filename.

    Args:
        filename: the filename to add
        list_of_filenames: the list of filenames to which filename
            should be added, without name duplicates
    Returns:
        Either filename or its modification, with a number appended between
        the name and the extension.
    """
    if filename not in list_of_filenames:
        return filename

    basename, ext = os.path.splitext(filename)

    # Not optimized, but for the moment this should be fast enough
    append_int = 1
    while True:
        new_filename = "{:s}-{:d}{:s}".format(basename, append_int, ext)
        if new_filename not in list_of_filenames:
            break
        append_int += 1
    return new_filename

if __name__=='__main__':
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

    unittest.main()
