# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the Comment ORM class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.orm.comments import Comment
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions


class TestComment(AiidaTestCase):
    """Unit tests for the Comment ORM class."""

    def setUp(self):
        super(TestComment, self).setUp()
        self.node = orm.Data().store()
        self.user = orm.User.objects.get_default()
        self.content = 'Sometimes when I am freestyling, I lose confidence'
        self.comment = Comment(self.node, self.user, self.content).store()

    def tearDown(self):
        super(TestComment, self).tearDown()
        comments = Comment.objects.all()
        for comment in comments:
            Comment.objects.delete(comment.id)

    def test_comment_content(self):
        """Test getting and setting content of a Comment."""
        content = 'Be more constructive with your feedback'
        self.comment.set_content(content)
        self.assertEqual(self.comment.content, content)

    def test_comment_mtime(self):
        """Test getting and setting mtime of a Comment."""
        mtime = self.comment.mtime
        self.comment.set_content('Changing an attribute should automatically change the mtime')
        self.assertEqual(self.comment.content, 'Changing an attribute should automatically change the mtime')
        self.assertNotEqual(self.comment.mtime, mtime)

    def test_comment_node(self):
        """Test getting the node of a Comment."""
        self.assertEqual(self.comment.node.uuid, self.node.uuid)

    def test_comment_user(self):
        """Test getting the user of a Comment."""
        self.assertEqual(self.comment.user.uuid, self.user.uuid)

    def test_comment_collection_get(self):
        """Test retrieving a Comment through the collection."""
        comment = Comment.objects.get(id=self.comment.pk)
        self.assertEqual(self.comment.uuid, comment.uuid)

    def test_comment_collection_delete(self):
        """Test deleting a Comment through the collection."""
        comment = Comment(self.node, self.user, 'I will perish').store()
        comment_pk = comment.pk

        Comment.objects.delete(comment.pk)

        with self.assertRaises(exceptions.NotExistent):
            Comment.objects.delete(comment_pk)

        with self.assertRaises(exceptions.NotExistent):
            Comment.objects.get(id=comment_pk)

    def test_comment_querybuilder(self):
        """Test querying for comments by joining on nodes in the QueryBuilder."""
        node_one = orm.Data().store()
        comment_one = Comment(node_one, self.user, 'comment_one').store()

        node_two = orm.Data().store()
        comment_three = Comment(node_two, self.user, 'comment_three').store()
        comment_four = Comment(node_two, self.user, 'comment_four').store()

        # Retrieve a node by joining on a specific comment
        nodes = orm.QueryBuilder().append(
            Comment, tag='comment', filters={
                'id': comment_one.id
            }).append(
                orm.Node, with_comment='comment', project=['uuid']).all()

        self.assertEqual(len(nodes), 1)
        for node in nodes:
            self.assertIn(str(node[0]), [node_one.uuid])

        # Retrieve a comment by joining on a specific node
        comments = orm.QueryBuilder().append(
            orm.Node, tag='node', filters={
                'id': node_two.id
            }).append(
                Comment, with_node='node', project=['uuid']).all()

        self.assertEqual(len(comments), 2)
        for comment in comments:
            self.assertIn(str(comment[0]), [comment_three.uuid, comment_four.uuid])

    def test_objects_get(self):
        """Test getting a comment from the collection"""
        node = orm.Data().store()
        comment = node.add_comment('Check out the comment on _this_ one')
        gotten_comment = Comment.objects.get(id=comment.id)
        self.assertIsInstance(gotten_comment, Comment)
