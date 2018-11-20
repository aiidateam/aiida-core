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
        self.node = orm.Node().store()
        self.user = orm.User.objects.get_default()
        self.content = 'Sometimes when I am freestyling, I lose confidence'
        self.comment = Comment(self.node, self.user, self.content).store()

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
        comment = Comment.objects.get(comment=self.comment.pk)
        self.assertEqual(self.comment.uuid, comment.uuid)

    def test_comment_collection_delete(self):
        """Test deleting a Comment through the collection."""
        comment = Comment(self.node, self.user, 'I will perish').store()
        comment_pk = comment.pk

        Comment.objects.delete(comment=comment.pk)

        with self.assertRaises(exceptions.NotExistent):
            Comment.objects.get(comment=comment_pk)
