"""Unit tests for editing pre and post bash scripts, comments, etc."""
import os
import unittest

from click.testing import CliRunner

from aiida.cmdline.utils.multi_line_input import edit_pre_post, edit_comment


class TestMultilineInput(unittest.TestCase):
    """Test functions for editing pre and post bash scripts, comments, etc."""

    def setUp(self):
        ## Sleep 1 is needed because on some filesystems (e.g. some pre 10.13 Mac) the
        ## filesystem returns the time with a precision of 1 second, and
        ## click uses the timestamp to decide if the file was re-saved or not.
        editor_cmd = 'sleep 1 ; vim -c "%s/$/Test/g" -cwq'  # appends Test to every line
        os.environ['EDITOR'] = editor_cmd
        os.environ['VISUAL'] = editor_cmd
        self.runner = CliRunner()

    def test_pre_post(self):
        result = edit_pre_post(summary={'Param 1': 'Value 1', 'Param 2': 'Value 1'})
        self.assertEqual(result[0], 'Test\nTest\nTest')
        self.assertEqual(result[1], 'Test\nTest\nTest')

    def test_edit_pre_post(self):
        result = edit_pre_post(pre='OldPre', post='OldPost')
        self.assertEqual(result[0], 'Test\nOldPreTest\nTest')
        self.assertEqual(result[1], 'Test\nOldPostTest\nTest')

    def test_new_comment(self):
        new_comment = edit_comment()
        self.assertEqual(new_comment, 'Test')

    def test_edit_comment(self):
        old_comment = 'OldComment'
        new_comment = edit_comment(old_cmt=old_comment)
        self.assertEqual(new_comment, old_comment + 'Test')
