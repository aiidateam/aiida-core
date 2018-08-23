# -*- coding: utf-8 -*-
from __future__ import absolute_import
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase

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
        from aiida.orm import Node

        node = Node()
        node.store()
        node.add_comment(COMMENT)

        result = CliRunner().invoke(show, [str(node.pk)], catch_exceptions=False)
        self.assertNotEqual(result.output.find(COMMENT), -1)
        self.assertEqual(result.exit_code, 0)

    def test_comment_add(self):
        """ Test adding a comment """
        from aiida.cmdline.commands.cmd_comment import add
        from aiida.orm import Node

        node = Node()
        node.store()

        result = CliRunner().invoke(add, ['-c{}'.format(COMMENT), str(node.pk)], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        comment = node.get_comments()
        self.assertEquals(len(comment), 1)
        self.assertEqual(comment[0]['content'], COMMENT)

    def test_comment_remove(self):
        """ Test removing a comment """
        from aiida.cmdline.commands.cmd_comment import remove
        from aiida.orm import Node

        node = Node()
        node.store()
        comment_id = node.add_comment(COMMENT)

        self.assertEquals(len(node.get_comments()), 1)

        result = CliRunner().invoke(remove, [str(node.pk), str(comment_id), '--force'], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        self.assertEquals(len(node.get_comments()), 0)

    def test_comment_remove_all(self):
        """ Test removing all comments from a node """
        from aiida.cmdline.commands.cmd_comment import remove
        from aiida.orm import Node

        node = Node()
        node.store()
        for _ in range(10):
            node.add_comment(COMMENT)

        self.assertEqual(len(node.get_comments()), 10)

        result = CliRunner().invoke(remove, [str(node.pk), '--all', '--force'], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)

        self.assertEqual(len(node.get_comments()), 0)

