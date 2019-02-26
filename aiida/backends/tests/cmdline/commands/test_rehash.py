# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi rehash`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_rehash


class TestVerdiRehash(AiidaTestCase):
    """Tests for `verdi rehash`."""

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

    def test_rehash(self):
        """Passing no options to the command will rehash all 5 nodes."""
        expected_node_count = 5
        options = []
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_bool(self):
        """Limiting the queryset by defining an entry point, in this case bool, should limit nodes to 2."""
        expected_node_count = 2
        options = ['-e', 'aiida.data:bool']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_float(self):
        """Limiting the queryset by defining an entry point, in this case float, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-e', 'aiida.data:float']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_int(self):
        """Limiting the queryset by defining an entry point, in this case int, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-e', 'aiida.data:int']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_explicit_pk(self):
        """Limiting the queryset by defining explicit identifiers, should limit nodes to 2 in this example."""
        expected_node_count = 2
        options = [str(self.node_bool_true.pk), str(self.node_float.uuid)]
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_explicit_pk_and_entry_point(self):
        """Limiting the queryset by defining explicit identifiers and entry point, should limit nodes to 1."""
        expected_node_count = 1
        options = ['-e', 'aiida.data:bool', str(self.node_bool_true.pk), str(self.node_float.uuid)]
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertClickResultNoException(result)
        self.assertTrue('{} nodes'.format(expected_node_count) in result.output)

    def test_rehash_entry_point_no_matches(self):
        """Limiting the queryset by defining explicit entry point, with no nodes should exit with non-zero status."""
        options = ['-e', 'aiida.data:structure']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertIsNotNone(result.exception)

    def test_rehash_invalid_entry_point(self):
        """Passing an invalid entry point should exit with non-zero status."""

        # Incorrect entry point group
        options = ['-e', 'data:structure']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertIsNotNone(result.exception)

        # Non-existent entry point name
        options = ['-e', 'aiida.data:inexistant']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertIsNotNone(result.exception)

        # Incorrect syntax, no colon to join entry point group and name
        options = ['-e', 'aiida.data.structure']
        result = self.cli_runner.invoke(cmd_rehash.rehash, options)
        self.assertIsNotNone(result.exception)
