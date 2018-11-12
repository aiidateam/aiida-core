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

from six.moves import range
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida import orm

COMMENT = u'Well I never...'


class TestVerdiUserCommand(AiidaTestCase):

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_comment_show_simple(self):
        """ test simply calling the show command (without data to show) """
        from aiida.cmdline.commands.cmd_comment import show

        result = CliRunner().invoke(show, [], catch_exceptions=False)
        self.assertEqual(result.output, "")
        self.assertEqual(result.exit_code, 0)

    def test_comment_show(self):
        """ Test showing an existing comment """
        from aiida.cmdline.commands.cmd_comment import show

        node = orm.Node()
        node.store()
        node.add_comment(COMMENT)

        result = CliRunner().invoke(show, [str(node.pk)], catch_exceptions=False)
        self.assertNotEqual(result.output.find(COMMENT), -1)
        self.assertEqual(result.exit_code, 0)

    def test_comment_add(self):
        """ Test adding a comment """
        from aiida.cmdline.commands.cmd_comment import add

        node = orm.Node()
        node.store()

        result = CliRunner().invoke(add, ['-c{}'.format(COMMENT), str(node.pk)], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        comment = node.get_comments()
        self.assertEquals(len(comment), 1)
        self.assertEqual(comment[0]['content'], COMMENT)

    def test_comment_remove(self):
        """ Test removing a comment """
        from aiida.cmdline.commands.cmd_comment import remove

        node = orm.Node()
        node.store()
        comment_id = node.add_comment(COMMENT)

        self.assertEquals(len(node.get_comments()), 1)

        result = CliRunner().invoke(remove, [str(node.pk), str(comment_id), '--force'], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        self.assertEquals(len(node.get_comments()), 0)

    def test_comment_remove_all(self):
        """ Test removing all comments from a node """
        from aiida.cmdline.commands.cmd_comment import remove

        node = orm.Node()
        node.store()
        for _ in range(10):
            node.add_comment(COMMENT)

        self.assertEqual(len(node.get_comments()), 10)

        result = CliRunner().invoke(remove, [str(node.pk), '--all', '--force'], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        self.assertEqual(len(node.get_comments()), 0)
