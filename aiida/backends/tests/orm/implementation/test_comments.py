# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the BackendComment and BackendCommentCollection classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime
from uuid import UUID

from aiida.backends.testbase import AiidaTestCase
from aiida.common import timezone


class TestBackendComment(AiidaTestCase):
    """Test BackendComment."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestBackendComment, cls).setUpClass(*args, **kwargs)
        cls.computer = cls.computer.backend_entity  # Unwrap the `Computer` instance to `BackendComputer`
        cls.user = cls.backend.users.create(email='tester@localhost').store()

    def setUp(self):
        super(TestBackendComment, self).setUp()
        self.node = self.backend.nodes.create(
            node_type='', user=self.user, computer=self.computer, label='label', description='description').store()
        self.comment_content = 'comment content'

    def test_creation(self):
        """Test creation of a BackendComment and all its properties."""
        comment = self.backend.comments.create(node=self.node, user=self.user, content=self.comment_content)

        # Before storing
        self.assertIsNone(comment.id)
        self.assertIsNone(comment.pk)
        self.assertTrue(isinstance(comment.uuid, str))
        self.assertTrue(isinstance(comment.ctime, datetime))
        self.assertIsNone(comment.mtime)
        self.assertEqual(comment.content, self.comment_content)

        # Store the comment.ctime before the store as a reference
        now = timezone.now()
        comment_ctime_before_store = comment.ctime
        self.assertTrue(now > comment.ctime, '{} is not smaller than now {}'.format(comment.ctime, now))

        comment.store()
        comment_ctime = comment.ctime
        comment_mtime = comment.mtime

        # The comment.ctime should have been unchanged, but the comment.mtime should have changed
        self.assertEqual(comment.ctime, comment_ctime_before_store)
        self.assertIsNotNone(comment.mtime)
        self.assertTrue(now < comment.mtime, '{} is not larger than now {}'.format(comment.mtime, now))

        # After storing
        self.assertTrue(isinstance(comment.id, int))
        self.assertTrue(isinstance(comment.pk, int))
        self.assertTrue(isinstance(comment.uuid, str))
        self.assertTrue(isinstance(comment.ctime, datetime))
        self.assertTrue(isinstance(comment.mtime, datetime))
        self.assertEqual(comment.content, self.comment_content)

        # Try to construct a UUID from the UUID value to prove that it has a valid UUID
        UUID(comment.uuid)

        # Change a column, which should trigger the save, update the mtime but leave the ctime untouched
        comment.set_content('test')
        self.assertEqual(comment.ctime, comment_ctime)
        self.assertTrue(comment.mtime > comment_mtime)

    def test_creation_with_time(self):
        """
        Test creation of a BackendComment when passing the mtime and the ctime. The passed ctime and mtime
        should be respected since it is important for the correct import of nodes at the AiiDA import/export.
        """
        from aiida.orm.importexport import deserialize_attributes

        ctime = deserialize_attributes('2019-02-27T16:20:12.245738', 'date')
        mtime = deserialize_attributes('2019-02-27T16:27:14.798838', 'date')

        comment = self.backend.comments.create(
            node=self.node, user=self.user, content=self.comment_content, mtime=mtime, ctime=ctime)

        # Check that the ctime and mtime are the given ones
        self.assertEqual(comment.ctime, ctime)
        self.assertEqual(comment.mtime, mtime)

        comment.store()

        # Check that the given values remain even after storing
        self.assertEqual(comment.ctime, ctime)
        self.assertEqual(comment.mtime, mtime)
