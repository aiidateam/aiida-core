# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_comment
from aiida import orm

COMMENT = u'Well I never...'


class TestVerdiUserCommand(AiidaTestCase):

    def setUp(self):
        self.cli_runner = CliRunner()
        self.node = orm.Data().store()

    def test_comment_show_simple(self):
        """Test simply calling the show command (without data to show)."""
        result = self.cli_runner.invoke(cmd_comment.show, [], catch_exceptions=False)
        self.assertEqual(result.output, '')
        self.assertEqual(result.exit_code, 0)

    def test_comment_show(self):
        """Test showing an existing comment."""
        self.node.add_comment(COMMENT)

        options = [str(self.node.pk)]
        result = self.cli_runner.invoke(cmd_comment.show, options, catch_exceptions=False)
        self.assertNotEqual(result.output.find(COMMENT), -1)
        self.assertEqual(result.exit_code, 0)

    def test_comment_add(self):
        """Test adding a comment."""
        options = ['-N', str(self.node.pk), '--', '{}'.format(COMMENT)]
        result = self.cli_runner.invoke(cmd_comment.add, options, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        comment = self.node.get_comments()
        self.assertEqual(len(comment), 1)
        self.assertEqual(comment[0].content, COMMENT)

    def test_comment_remove(self):
        """Test removing a comment."""
        comment = self.node.add_comment(COMMENT)

        self.assertEqual(len(self.node.get_comments()), 1)

        options = [str(comment.pk), '--force']
        result = self.cli_runner.invoke(cmd_comment.remove, options, catch_exceptions=False)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(len(self.node.get_comments()), 0)
