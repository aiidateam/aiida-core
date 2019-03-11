# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for verdi graph"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import errno
import os
import tempfile

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_graph


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
    """Tests for verdi graph"""

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
        filename = root_node + '.dot'
        options = [root_node]
        try:
            result = self.cli_runner.invoke(cmd_graph.generate, options)
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
            filename = root_node + '.dot'
            try:
                result = self.cli_runner.invoke(cmd_graph.generate, options)
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
            filename = str(root_node) + '.dot'
            options = [str(root_node)]
            result = self.cli_runner.invoke(cmd_graph.generate, options)
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
        filename = root_node + '.dot'

        # Test that the options don't fail
        for opt in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            options = [opt, None, root_node]
            try:
                result = self.cli_runner.invoke(cmd_graph.generate, options)
                self.assertIsNone(result.exception, result.output)
                self.assertTrue(os.path.isfile(filename))
            finally:
                delete_temporary_file(filename)

        # Test that the options accept zero or a positive int
        for opt in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            for value in ['0', '1']:
                options = [opt, value, root_node]
                try:
                    result = self.cli_runner.invoke(cmd_graph.generate, options)
                    self.assertIsNone(result.exception, result.output)
                    self.assertTrue(os.path.isfile(filename))
                finally:
                    delete_temporary_file(filename)

        # Check the options reject any values that are not positive ints
        for flag in ['-a', '--ancestor-depth', '-d', '--descendant-depth']:
            for badvalue in ['xyz', '3.14', '-5']:
                options = [flag, badvalue, root_node]
                try:
                    result = self.cli_runner.invoke(cmd_graph.generate, options)
                    self.assertIsNotNone(result.exception)
                    self.assertFalse(os.path.isfile(filename))
                finally:
                    delete_temporary_file(filename)

    def test_check_io_flags(self):
        """
        Test the input and output flags work.
        """
        root_node = str(self.node.pk)
        filename = root_node + '.dot'

        for flag in ['-i', '--inputs', '-o', '--outputs']:
            options = [flag, root_node]
            try:
                result = self.cli_runner.invoke(cmd_graph.generate, options)
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
            for fileformat in ['dot', 'canon']:
                filename = root_node + '.' + fileformat
                options = [option, fileformat, root_node]
                try:
                    result = self.cli_runner.invoke(cmd_graph.generate, options)
                    self.assertIsNone(result.exception, result.output)
                    self.assertTrue(os.path.isfile(filename))
                finally:
                    delete_temporary_file(filename)
