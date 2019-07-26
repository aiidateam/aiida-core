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

from click.testing import CliRunner

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_node


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiNode(AiidaTestCase):
    """Tests for `verdi node`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiNode, cls).setUpClass(*args, **kwargs)

        node = orm.Data()

        cls.ATTR_KEY_ONE = "a"
        cls.ATTR_VAL_ONE = "1"
        cls.ATTR_KEY_TWO = "b"
        cls.ATTR_VAL_TWO = "test"

        node.set_attribute_many({cls.ATTR_KEY_ONE: cls.ATTR_VAL_ONE, cls.ATTR_KEY_TWO: cls.ATTR_VAL_TWO})

        cls.EXTRA_KEY_ONE = "x"
        cls.EXTRA_VAL_ONE = "2"
        cls.EXTRA_KEY_TWO = "y"
        cls.EXTRA_VAL_TWO = "other"

        node.set_extra_many({cls.EXTRA_KEY_ONE: cls.EXTRA_VAL_ONE, cls.EXTRA_KEY_TWO: cls.EXTRA_VAL_TWO})

        node.store()

        cls.node = node

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_node_tree(self):
        """Test `verdi node tree`"""
        node = orm.Data().store()
        options = [str(node.pk)]
        result = self.cli_runner.invoke(cmd_node.tree, options)
        self.assertClickResultNoException(result)

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
