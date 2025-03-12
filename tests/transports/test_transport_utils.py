import os
import tempfile
import unittest
import zipfile

from aiida.transports.util import compress, extract


class TestTransportUtils(unittest.TestCase):
    """Test compression and extraction utilities for Transport classes."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = os.path.join(self.temp_dir.name, 'source')
        self.dest_dir = os.path.join(self.temp_dir.name, 'dest')
        os.makedirs(self.source_dir, exist_ok=True)
        os.makedirs(self.dest_dir, exist_ok=True)

    def tearDown(self):
        """Clean up the temporary directory after testing."""
        self.temp_dir.cleanup()

    def test_compress_and_extract_zip(self):
        """Test compressing and extracting a directory using ZIP format."""
        # Create test files and directories
        file_path = os.path.join(self.source_dir, 'test_file.txt')
        with open(file_path, 'w') as f:
            f.write('Hello, AiiDA!')

        empty_dir_path = os.path.join(self.source_dir, 'empty_dir')
        os.makedirs(empty_dir_path, exist_ok=True)

        # Compress the source directory into a ZIP archive
        zip_path = os.path.join(self.temp_dir.name, 'archive.zip')
        compress(None, self.source_dir, zip_path, format='zip')

        # Verify the ZIP archive was created
        self.assertTrue(os.path.exists(zip_path))

        # Extract the ZIP archive to the destination directory
        extract(None, zip_path, self.dest_dir, format='zip')

        # Verify the extracted contents
        extracted_file_path = os.path.join(self.dest_dir, 'test_file.txt')
        self.assertTrue(os.path.exists(extracted_file_path))
        with open(extracted_file_path, 'r') as f:
            self.assertEqual(f.read(), 'Hello, AiiDA!')

        extracted_empty_dir_path = os.path.join(self.dest_dir, 'empty_dir')
        self.assertTrue(os.path.exists(extracted_empty_dir_path))
        self.assertTrue(os.path.isdir(extracted_empty_dir_path))

    def test_compress_zip_with_empty_directory(self):
        """Test compressing a directory with only an empty directory using ZIP format."""
        empty_dir_path = os.path.join(self.source_dir, 'empty_dir')
        os.makedirs(empty_dir_path, exist_ok=True)

        # Compress the source directory into a ZIP archive
        zip_path = os.path.join(self.temp_dir.name, 'archive.zip')
        compress(None, self.source_dir, zip_path, format='zip')

        # Verify the ZIP archive was created
        self.assertTrue(os.path.exists(zip_path))

        # Open the ZIP archive and verify it contains the empty directory
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zip_contents = zipf.namelist()
            self.assertIn('empty_dir/', zip_contents)

    def test_extract_nonexistent_zip(self):
        """Test extracting a non-existent ZIP archive."""
        nonexistent_zip_path = os.path.join(self.temp_dir.name, 'nonexistent.zip')
        with self.assertRaises(FileNotFoundError):
            extract(None, nonexistent_zip_path, self.dest_dir, format='zip')

    def test_compress_unsupported_format(self):
        """Test compressing with an unsupported format."""
        with self.assertRaises(ValueError):
            compress(None, self.source_dir, 'archive.rar', format='rar')

    def test_extract_unsupported_format(self):
        """Test extracting with an unsupported format."""
        with self.assertRaises(ValueError):
            extract(None, 'archive.rar', self.dest_dir, format='rar')


if __name__ == '__main__':
    unittest.main()
