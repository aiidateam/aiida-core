# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for verdi node"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import errno
import tempfile

from click.testing import CliRunner

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_node
from aiida.common.utils import Capturing


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiNode(AiidaTestCase):
    """Tests for `verdi node`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiNode, cls).setUpClass(*args, **kwargs)

        node = orm.Data()

        cls.ATTR_KEY_ONE = 'a'
        cls.ATTR_VAL_ONE = '1'
        cls.ATTR_KEY_TWO = 'b'
        cls.ATTR_VAL_TWO = 'test'

        node.set_attribute_many({cls.ATTR_KEY_ONE: cls.ATTR_VAL_ONE, cls.ATTR_KEY_TWO: cls.ATTR_VAL_TWO})

        cls.EXTRA_KEY_ONE = 'x'
        cls.EXTRA_VAL_ONE = '2'
        cls.EXTRA_KEY_TWO = 'y'
        cls.EXTRA_VAL_TWO = 'other'

        node.set_extra_many({cls.EXTRA_KEY_ONE: cls.EXTRA_VAL_ONE, cls.EXTRA_KEY_TWO: cls.EXTRA_VAL_TWO})

        node.store()

        cls.node = node

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_node_tree(self):
        """Test `verdi node tree`"""
        options = [str(self.node.pk)]
        result = self.cli_runner.invoke(cmd_node.tree, options)
        self.assertClickResultNoException(result)

    def test_node_tree_printer(self):
        """Test the `NodeTreePrinter` utility."""
        from aiida.cmdline.commands.cmd_node import NodeTreePrinter

        with Capturing():
            NodeTreePrinter.print_node_tree(self.node, max_depth=1)

        with Capturing():
            NodeTreePrinter.print_node_tree(self.node, max_depth=1, follow_links=())

    def test_node_attributes(self):
        """Test verdi node attributes"""
        options = [str(self.node.uuid)]
        result = self.cli_runner.invoke(cmd_node.attributes, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn(self.ATTR_KEY_ONE, result.output)
        self.assertIn(self.ATTR_VAL_ONE, result.output)
        self.assertIn(self.ATTR_KEY_TWO, result.output)
        self.assertIn(self.ATTR_VAL_TWO, result.output)

        for flag in ['-k', '--keys']:
            options = [flag, self.ATTR_KEY_ONE, '--', str(self.node.uuid)]
            result = self.cli_runner.invoke(cmd_node.attributes, options)
            self.assertIsNone(result.exception, result.output)
            self.assertIn(self.ATTR_KEY_ONE, result.output)
            self.assertIn(self.ATTR_VAL_ONE, result.output)
            self.assertNotIn(self.ATTR_KEY_TWO, result.output)
            self.assertNotIn(self.ATTR_VAL_TWO, result.output)

        for flag in ['-r', '--raw']:
            options = [flag, str(self.node.uuid)]
            result = self.cli_runner.invoke(cmd_node.attributes, options)
            self.assertIsNone(result.exception, result.output)

        for flag in ['-f', '--format']:
            for fmt in ['json+date', 'yaml', 'yaml_expanded']:
                options = [flag, fmt, str(self.node.uuid)]
                result = self.cli_runner.invoke(cmd_node.attributes, options)
                self.assertIsNone(result.exception, result.output)

        for flag in ['-i', '--identifier']:
            for fmt in ['pk', 'uuid']:
                options = [flag, fmt, str(self.node.uuid)]
                result = self.cli_runner.invoke(cmd_node.attributes, options)
                self.assertIsNone(result.exception, result.output)

    def test_node_extras(self):
        """Test verdi node extras"""
        options = [str(self.node.uuid)]
        result = self.cli_runner.invoke(cmd_node.extras, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn(self.EXTRA_KEY_ONE, result.output)
        self.assertIn(self.EXTRA_VAL_ONE, result.output)
        self.assertIn(self.EXTRA_KEY_TWO, result.output)
        self.assertIn(self.EXTRA_VAL_TWO, result.output)

        for flag in ['-k', '--keys']:
            options = [flag, self.EXTRA_KEY_ONE, '--', str(self.node.uuid)]
            result = self.cli_runner.invoke(cmd_node.extras, options)
            self.assertIsNone(result.exception, result.output)
            self.assertIn(self.EXTRA_KEY_ONE, result.output)
            self.assertIn(self.EXTRA_VAL_ONE, result.output)
            self.assertNotIn(self.EXTRA_KEY_TWO, result.output)
            self.assertNotIn(self.EXTRA_VAL_TWO, result.output)

        for flag in ['-r', '--raw']:
            options = [flag, str(self.node.uuid)]
            result = self.cli_runner.invoke(cmd_node.extras, options)
            self.assertIsNone(result.exception, result.output)

        for flag in ['-f', '--format']:
            for fmt in ['json+date', 'yaml', 'yaml_expanded']:
                options = [flag, fmt, str(self.node.uuid)]
                result = self.cli_runner.invoke(cmd_node.extras, options)
                self.assertIsNone(result.exception, result.output)

        for flag in ['-i', '--identifier']:
            for fmt in ['pk', 'uuid']:
                options = [flag, fmt, str(self.node.uuid)]
                result = self.cli_runner.invoke(cmd_node.extras, options)
                self.assertIsNone(result.exception, result.output)


def delete_temporary_file(filepath):
    """
    Attempt to delete a file, given an absolute path. If the deletion fails because the file does not exist
    the exception will be caught and passed. Any other exceptions will raise.

    :param filepath: the absolute file path
    """
    try:
        os.remove(filepath)
    except OSError as exception:
        if exception.errno != errno.ENOENT:
            raise
        else:
            pass


class TestVerdiGraph(AiidaTestCase):
    """Tests for the ``verdi node graph`` command."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiGraph, cls).setUpClass()
        from aiida.orm import Data

        cls.node = Data().store()

        # some of the export tests write in the current directory,
        # make sure it is writeable and we don't pollute the current one
        cls.old_cwd = os.getcwd()
        cls.cwd = tempfile.mkdtemp(__name__)
        os.chdir(cls.cwd)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        os.chdir(cls.old_cwd)
        os.rmdir(cls.cwd)

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_generate_graph(self):
        """
        Test that the default graph can be generated
        The command should run without error and should produce the .dot file
        """
        # Get a PK of a node which exists
        root_node = str(self.node.pk)
        filename = root_node + '.dot.pdf'
        options = [root_node]
        try:
            result = self.cli_runner.invoke(cmd_node.graph_generate, options)
            self.assertIsNone(result.exception, result.output)
            self.assertTrue(os.path.isfile(filename))
        finally:
            delete_temporary_file(filename)

    def test_catch_bad_pk(self):
        """
        Test that an invalid root_node pk (non-numeric, negative, or decimal),
        or non-existent pk will produce an error
        """
        from aiida.orm import load_node
        from aiida.common.exceptions import NotExistent

        # Forbidden pk
        for root_node in ['xyz', '-5', '3.14']:
            options = [root_node]
            filename = root_node + '.dot.pdf'
            try:
                result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                self.assertIsNotNone(result.exception)
                self.assertFalse(os.path.isfile(filename))
            finally:
                delete_temporary_file(filename)

        # Non-existant pk

        # Check that an arbitrary pk definately can't be loaded
        root_node = 123456789
        try:
            node = load_node(pk=root_node)
            self.assertIsNone(node)
        except NotExistent:
            pass
        #  Make sure verdi graph rejects this non-existant pk
        try:
            filename = str(root_node) + '.dot.pdf'
            options = [str(root_node)]
            result = self.cli_runner.invoke(cmd_node.graph_generate, options)
            self.assertIsNotNone(result.exception)
            self.assertFalse(os.path.isfile(filename))
        finally:
            delete_temporary_file(filename)

    def test_check_recursion_flags(self):
        """
        Test the ancestor-depth and descendent-depth options.
        Test that they don't fail and that, if specified, they only accept
        positive ints
        """
        root_node = str(self.node.pk)
        filename = root_node + '.dot.pdf'

        # Test that the options don't fail
        for opt in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            options = [opt, None, root_node]
            try:
                result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename))
            finally:
                delete_temporary_file(filename)

        # Test that the options accept zero or a positive int
        for opt in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            for value in ['0', '1']:
                options = [opt, value, root_node]
                try:
                    result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                    self.assertIsNone(result.exception, result.output)
                    self.assertTrue(os.path.isfile(filename))
                finally:
                    delete_temporary_file(filename)

        # Check the options reject any values that are not positive ints
        for flag in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            for badvalue in ['xyz', '3.14', '-5']:
                options = [flag, badvalue, root_node]
                try:
                    result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                    self.assertIsNotNone(result.exception)
                    self.assertFalse(os.path.isfile(filename))
                finally:
                    delete_temporary_file(filename)

    def test_check_io_flags(self):
        """
        Test the input and output flags work.
        """
        root_node = str(self.node.pk)
        filename = root_node + '.dot.pdf'

        for flag in ['-i', '--process-in', '-o', '--process-out']:
            options = [flag, root_node]
            try:
                result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename))
            finally:
                delete_temporary_file(filename)

    def test_output_format(self):
        """
        Test that the output file format can be specified
        """
        root_node = str(self.node.pk)

        for option in ['-f', '--output-format']:

            # Test different formats. Could exhaustively test the formats
            # supported on a given OS (printed by '$ dot -T?') but here
            # we just use the built-ins dot and canon as a minimal check that
            # the option works. After all, this test is for the cmdline.
            for fileformat in ['pdf', 'png']:
                filename = root_node + '.dot.' + fileformat
                options = [option, fileformat, root_node]
                try:
                    result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                    self.assertIsNone(result.exception, result.output)
                    self.assertTrue(os.path.isfile(filename))
                finally:
                    delete_temporary_file(filename)

    def test_node_id_label_format(self):
        """
        Test that the node id label format can be specified
        """
        root_node = str(self.node.pk)
        filename = root_node + '.dot.pdf'

        for id_label_type in ['uuid', 'pk', 'label']:
            options = ['--identifier', id_label_type, root_node]
            try:
                result = self.cli_runner.invoke(cmd_node.graph_generate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename))
            finally:
                delete_temporary_file(filename)


COMMENT = u'Well I never...'


class TestVerdiUserCommand(AiidaTestCase):
    """Tests for the ``verdi node comment`` command."""

    def setUp(self):
        self.cli_runner = CliRunner()
        self.node = orm.Data().store()

    def test_comment_show_simple(self):
        """Test simply calling the show command (without data to show)."""
        result = self.cli_runner.invoke(cmd_node.comment_show, [], catch_exceptions=False)
        self.assertEqual(result.output, '')
        self.assertEqual(result.exit_code, 0)

    def test_comment_show(self):
        """Test showing an existing comment."""
        self.node.add_comment(COMMENT)

        options = [str(self.node.pk)]
        result = self.cli_runner.invoke(cmd_node.comment_show, options, catch_exceptions=False)
        self.assertNotEqual(result.output.find(COMMENT), -1)
        self.assertEqual(result.exit_code, 0)

    def test_comment_add(self):
        """Test adding a comment."""
        options = ['-N', str(self.node.pk), '--', '{}'.format(COMMENT)]
        result = self.cli_runner.invoke(cmd_node.comment_add, options, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        comment = self.node.get_comments()
        self.assertEqual(len(comment), 1)
        self.assertEqual(comment[0].content, COMMENT)

    def test_comment_remove(self):
        """Test removing a comment."""
        comment = self.node.add_comment(COMMENT)

        self.assertEqual(len(self.node.get_comments()), 1)

        options = [str(comment.pk), '--force']
        result = self.cli_runner.invoke(cmd_node.comment_remove, options, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(len(self.node.get_comments()), 0)


class TestVerdiRehash(AiidaTestCase):
    """Tests for the ``verdi node rehash`` command."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiRehash, cls).setUpClass(*args, **kwargs)
        from aiida.orm import Data, Bool, Float, Int

        cls.node_base = Data().store()
        cls.node_bool_true = Bool(True).store()
        cls.node_bool_false = Bool(False).store()
        cls.node_float = Float(1.0).store()
        cls.node_int = Int(1).store()

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_rehash_interactive_yes(self):
        """Passing no options and answering 'Y' to the command will rehash all 5 nodes."""
        expected_node_count = 5
        options = []  # no option, will ask in the prompt
        result = self.cli_runner.invoke(cmd_node.rehash, options, input='y')
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_interactive_no(self):
        """Passing no options and answering 'N' to the command will abort the command."""
        options = []  # no option, will ask in the prompt
        result = self.cli_runner.invoke(cmd_node.rehash, options, input='n')
        self.assertIsInstance(result.exception, SystemExit)
        self.assertIn('ExitCode.CRITICAL', str(result.exception))

    def test_rehash(self):
        """Passing no options to the command will rehash all 5 nodes."""
        expected_node_count = 5
        options = ['-f']  # force, so no questions are asked
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_bool(self):
        """Limiting the queryset by defining an entry point, in this case bool, should limit nodes to 2."""
        expected_node_count = 2
        options = ['-f', '-e', 'aiida.data:bool']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_float(self):
        """Limiting the queryset by defining an entry point, in this case float, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-f', '-e', 'aiida.data:float']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_int(self):
        """Limiting the queryset by defining an entry point, in this case int, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-f', '-e', 'aiida.data:int']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_explicit_pk(self):
        """Limiting the queryset by defining explicit identifiers, should limit nodes to 2 in this example."""
        expected_node_count = 2
        options = ['-f', str(self.node_bool_true.pk), str(self.node_float.uuid)]
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_explicit_pk_and_entry_point(self):
        """Limiting the queryset by defining explicit identifiers and entry point, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-f', '-e', 'aiida.data:bool', str(self.node_bool_true.pk), str(self.node_float.uuid)]
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_entry_point_no_matches(self):
        """Limiting the queryset by defining explicit entry point, with no nodes should exit with non-zero status."""
        options = ['-f', '-e', 'aiida.data:structure']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertIsNotNone(result.exception)

    def test_rehash_invalid_entry_point(self):
        """Passing an invalid entry point should exit with non-zero status."""

        # Incorrect entry point group
        options = ['-f', '-e', 'data:structure']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertIsNotNone(result.exception)

        # Non-existent entry point name
        options = ['-f', '-e', 'aiida.data:inexistant']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertIsNotNone(result.exception)

        # Incorrect syntax, no colon to join entry point group and name
        options = ['-f', '-e', 'aiida.data.structure']
        result = self.cli_runner.invoke(cmd_node.rehash, options)
        self.assertIsNotNone(result.exception)


class TestVerdiDelete(AiidaTestCase):
    """
    Tests for the ``verdi node delete`` command.
    These test do not test the delete functionality, just that the command internal
    logic does not create any problems before the call to the function.
    For the actual functionality, see:
    * source: manage.database.delete.nodes.py
    * test: backends.tests.test_nodes.py
    """

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_basics(self):
        """
        Testing the correct translation for the `--force` and `--verbose` options.
        This just checks that the calls do not except and that in all cases with the
        force flag there is no messages.
        """
        from aiida.common.exceptions import NotExistent

        newnode = orm.Data().store()
        newnodepk = newnode.pk
        options_list = []
        options_list.append(['--create-forward'])
        options_list.append(['--call-calc-forward'])
        options_list.append(['--call-work-forward'])
        options_list.append(['--force'])
        options_list.append(['--verbose'])
        options_list.append(['--verbose', '--force'])

        for options in options_list:
            run_options = [str(newnodepk)]
            run_options.append('--dry-run')
            for an_option in options:
                run_options.append(an_option)
            result = self.cli_runner.invoke(cmd_node.node_delete, run_options)
            self.assertClickResultNoException(result)

        # To delete the created node
        run_options = [str(newnodepk)]
        run_options.append('--force')
        result = self.cli_runner.invoke(cmd_node.node_delete, run_options)
        self.assertClickResultNoException(result)

        with self.assertRaises(NotExistent):
            orm.load_node(newnodepk)
