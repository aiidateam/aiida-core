# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the BackendComment and BackendCommentCollection classes."""

from datetime import datetime
from uuid import UUID

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import timezone
from aiida.common import exceptions


class TestBackendComment(AiidaTestCase):
    """Test BackendComment."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.computer = cls.computer.backend_entity  # Unwrap the `Computer` instance to `BackendComputer`
        cls.user = cls.backend.users.create(email='tester@localhost').store()

    def setUp(self):
        super().setUp()
        self.node = self.backend.nodes.create(
            node_type='', user=self.user, computer=self.computer, label='label', description='description'
        ).store()
        self.comment_content = 'comment content'

    def create_comment(self, **kwargs):
        """Create BackendComment"""
        node = kwargs['node'] if 'node' in kwargs else self.node
        user = kwargs['user'] if 'user' in kwargs else self.user
        ctime = kwargs['ctime'] if 'ctime' in kwargs else None
        mtime = kwargs['mtime'] if 'mtime' in kwargs else None

        return self.backend.comments.create(
            node=node, user=user, content=self.comment_content, ctime=ctime, mtime=mtime
        )

    def test_creation(self):
        """Test creation of a BackendComment and all its properties."""
        comment = self.backend.comments.create(node=self.node, user=self.user, content=self.comment_content)

        # Before storing
        self.assertIsNone(comment.id)
        self.assertIsNone(comment.pk)
        self.assertTrue(isinstance(comment.uuid, str))
        self.assertTrue(comment.node, self.node)
        self.assertTrue(isinstance(comment.ctime, datetime))
        self.assertIsNone(comment.mtime)
        self.assertTrue(comment.user, self.user)
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
        self.assertTrue(comment.node, self.node)
        self.assertTrue(isinstance(comment.ctime, datetime))
        self.assertTrue(isinstance(comment.mtime, datetime))
        self.assertTrue(comment.user, self.user)
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
        from aiida.tools.importexport.dbimport.backends.utils import deserialize_attributes

        ctime = deserialize_attributes('2019-02-27T16:20:12.245738', 'date')
        mtime = deserialize_attributes('2019-02-27T16:27:14.798838', 'date')

        comment = self.backend.comments.create(
            node=self.node, user=self.user, content=self.comment_content, mtime=mtime, ctime=ctime
        )

        # Check that the ctime and mtime are the given ones
        self.assertEqual(comment.ctime, ctime)
        self.assertEqual(comment.mtime, mtime)

        comment.store()

        # Check that the given values remain even after storing
        self.assertEqual(comment.ctime, ctime)
        self.assertEqual(comment.mtime, mtime)

    def test_delete(self):
        """Test `delete` method"""
        # Create Comment, making sure it exists
        comment = self.create_comment()
        comment.store()
        comment_uuid = str(comment.uuid)

        builder = orm.QueryBuilder().append(orm.Comment, project='uuid')
        no_of_comments = builder.count()
        found_comments_uuid = [_[0] for _ in builder.all()]
        self.assertIn(comment_uuid, found_comments_uuid)

        # Delete Comment, making sure it was deleted
        self.backend.comments.delete(comment.id)

        builder = orm.QueryBuilder().append(orm.Comment, project='uuid')
        self.assertEqual(builder.count(), no_of_comments - 1)
        found_comments_uuid = [_[0] for _ in builder.all()]
        self.assertNotIn(comment_uuid, found_comments_uuid)

    def test_delete_all(self):
        """Test `delete_all` method"""
        self.create_comment().store()
        self.assertGreater(len(orm.Comment.objects.all()), 0, msg='There should be Comments in the database')

        self.backend.comments.delete_all()
        self.assertEqual(len(orm.Comment.objects.all()), 0, msg='All Comments should have been deleted')

    def test_delete_many_no_filters(self):
        """Test `delete_many` method with empty filters"""
        self.create_comment().store()
        count = len(orm.Comment.objects.all())
        self.assertGreater(count, 0)

        # Pass empty filter to delete_many, making sure ValidationError is raised
        with self.assertRaises(exceptions.ValidationError):
            self.backend.comments.delete_many({})
        self.assertEqual(
            len(orm.Comment.objects.all()),
            count,
            msg='No Comments should have been deleted. There should still be {} Comment(s), '
            'however {} Comment(s) was/were found.'.format(count, len(orm.Comment.objects.all()))
        )

    def test_delete_many_ids(self):
        """Test `delete_many` method filtering on both `id` and `uuid`"""
        comment1 = self.create_comment()
        comment2 = self.create_comment()
        comment3 = self.create_comment()
        comment_uuids = []
        for comment in [comment1, comment2, comment3]:
            comment.store()
            comment_uuids.append(str(comment.uuid))

        # Make sure they exist
        count_comments_found = orm.QueryBuilder().append(orm.Comment, filters={'uuid': {'in': comment_uuids}}).count()
        self.assertEqual(
            count_comments_found,
            len(comment_uuids),
            msg='There should be {} Comments, instead {} Comment(s) was/were found'.format(
                len(comment_uuids), count_comments_found
            )
        )

        # Delete last two comments (comment2, comment3)
        filters = {'or': [{'id': comment2.id}, {'uuid': str(comment3.uuid)}]}
        self.backend.comments.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Comment, filters={'uuid': {'in': comment_uuids}}, project='uuid').all()
        found_comments_uuid = [_[0] for _ in builder]
        self.assertEqual([comment_uuids[0]], found_comments_uuid)

    def test_delete_many_dbnode_id(self):
        """Test `delete_many` method filtering on `dbnode_id`"""
        # Create comments and separate node
        calc = self.backend.nodes.create(
            node_type='', user=self.user, computer=self.computer, label='label', description='description'
        ).store()
        comment1 = self.create_comment(node=calc)
        comment2 = self.create_comment()
        comment3 = self.create_comment()
        comment_uuids = []
        for comment in [comment1, comment2, comment3]:
            comment.store()
            comment_uuids.append(str(comment.uuid))

        # Make sure they exist
        count_comments_found = orm.QueryBuilder().append(orm.Comment, filters={'uuid': {'in': comment_uuids}}).count()
        self.assertEqual(
            count_comments_found,
            len(comment_uuids),
            msg='There should be {} Comments, instead {} Comment(s) was/were found'.format(
                len(comment_uuids), count_comments_found
            )
        )

        # Delete comments for self.node
        filters = {'dbnode_id': self.node.id}
        self.backend.comments.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Comment, filters={'uuid': {'in': comment_uuids}}, project='uuid').all()
        found_comments_uuid = [_[0] for _ in builder]
        self.assertEqual([comment_uuids[0]], found_comments_uuid)

    # pylint: disable=too-many-locals
    def test_delete_many_ctime_mtime(self):
        """Test `delete_many` method filtering on `ctime` and `mtime`"""
        from datetime import timedelta

        # Initialization
        comment_uuids = []
        found_comments_ctime = []
        found_comments_mtime = []
        found_comments_uuid = []

        now = timezone.now()
        two_days_ago = now - timedelta(days=2)
        one_day_ago = now - timedelta(days=1)
        comment_times = [now, one_day_ago, two_days_ago]

        # Create comments
        comment1 = self.create_comment(ctime=now, mtime=now)
        comment2 = self.create_comment(ctime=one_day_ago, mtime=now)
        comment3 = self.create_comment(ctime=two_days_ago, mtime=one_day_ago)
        for comment in [comment1, comment2, comment3]:
            comment.store()
            comment_uuids.append(str(comment.uuid))

        # Make sure they exist with the correct times
        builder = orm.QueryBuilder().append(orm.Comment, project=['ctime', 'mtime', 'uuid'])
        self.assertGreater(builder.count(), 0)
        for comment in builder.all():
            found_comments_ctime.append(comment[0])
            found_comments_mtime.append(comment[1])
            found_comments_uuid.append(comment[2])
        for time, uuid in zip(comment_times, comment_uuids):
            self.assertIn(time, found_comments_ctime)
            self.assertIn(uuid, found_comments_uuid)
            if time != two_days_ago:
                self.assertIn(time, found_comments_mtime)

        # Delete comments that are created more than 1 hour ago,
        # unless they have been modified within 5 hours
        ctime_turning_point = now - timedelta(seconds=60 * 60)
        mtime_turning_point = now - timedelta(seconds=60 * 60 * 5)
        filters = {'and': [{'ctime': {'<': ctime_turning_point}}, {'mtime': {'<': mtime_turning_point}}]}
        self.backend.comments.delete_many(filters=filters)

        # Check only the most stale comment (comment3) was deleted
        builder = orm.QueryBuilder().append(orm.Comment, project='uuid')
        self.assertGreater(builder.count(), 1)  # There should still be at least 2
        found_comments_uuid = [_[0] for _ in builder.all()]
        self.assertNotIn(comment_uuids[2], found_comments_uuid)

        # Make sure the other comments were not deleted
        for comment_uuid in comment_uuids[:-1]:
            self.assertIn(comment_uuid, found_comments_uuid)

    def test_delete_many_user_id(self):
        """Test `delete_many` method filtering on `user_id`"""
        # Create comments and separate user
        user_two = self.backend.users.create(email='tester_two@localhost').store()
        comment1 = self.create_comment(user=user_two)
        comment2 = self.create_comment()
        comment3 = self.create_comment()
        comment_uuids = []
        for comment in [comment1, comment2, comment3]:
            comment.store()
            comment_uuids.append(str(comment.uuid))

        # Make sure they exist
        builder = orm.QueryBuilder().append(orm.Comment, project='uuid')
        self.assertGreater(builder.count(), 0)
        found_comments_uuid = [_[0] for _ in builder.all()]
        for comment_uuid in comment_uuids:
            self.assertIn(comment_uuid, found_comments_uuid)

        # Delete last comments for `self.user`
        filters = {'user_id': self.user.id}
        self.backend.comments.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Comment, project='uuid')
        found_comments_uuid = [_[0] for _ in builder.all()]
        self.assertGreater(builder.count(), 0)
        for comment_uuid in comment_uuids[1:]:
            self.assertNotIn(comment_uuid, found_comments_uuid)

        # Make sure the first comment (comment1) was not deleted
        self.assertIn(comment_uuids[0], found_comments_uuid)

    def test_deleting_non_existent_entities(self):
        """Test deleting non-existent Comments for different cases"""
        comment = self.create_comment()
        comment.store()
        comment_id = comment.id
        comment_uuid = comment.uuid

        # Get a non-existent Comment
        valid_comment_found = True
        id_ = 0
        while valid_comment_found:
            id_ += 1
            builder = orm.QueryBuilder().append(orm.Comment, filters={'id': id_})
            if builder.count() == 0:
                valid_comment_found = False

        # Try to delete non-existing Comment - using delete_many
        # delete_many should return an empty list
        deleted_entities = self.backend.comments.delete_many(filters={'id': id_})
        self.assertEqual(
            deleted_entities, [],
            msg='No entities should have been deleted, since Comment id {} does not exist'.format(id_)
        )

        # Try to delete non-existing Comment - using delete
        # NotExistent should be raised, since no entities are found
        with self.assertRaises(exceptions.NotExistent) as exc:
            self.backend.comments.delete(comment_id=id_)
        self.assertIn("Comment with id '{}' not found".format(id_), str(exc.exception))

        # Try to delete existing and non-existing Comment - using delete_many
        # delete_many should return a list that *only* includes the existing Comment
        filters = {'id': {'in': [id_, comment_id]}}
        deleted_entities = self.backend.comments.delete_many(filters=filters)
        self.assertEqual([comment_id],
                         deleted_entities,
                         msg='Only Comment id {} should be returned from delete_many'.format(comment_id))

        # Make sure the existing Comment was deleted
        builder = orm.QueryBuilder().append(orm.Comment, filters={'uuid': comment_uuid})
        self.assertEqual(builder.count(), 0)

        # Get a non-existent Node
        valid_node_found = True
        id_ = 0
        while valid_node_found:
            id_ += 1
            builder = orm.QueryBuilder().append(orm.Node, filters={'id': id_})
            if builder.count() == 0:
                valid_node_found = False

        # Try to delete Comments filtering on non-existing dbnode_id
        # NotExistent should NOT be raised nor should any Comments be deleted
        comment_count_before = orm.QueryBuilder().append(orm.Comment).count()
        filters = {'dbnode_id': id_}
        self.backend.comments.delete_many(filters=filters)
        comment_count_after = orm.QueryBuilder().append(orm.Comment).count()
        self.assertEqual(
            comment_count_after,
            comment_count_before,
            msg='The number of comments changed after performing `delete_many`, '
            "while filtering for a non-existing 'dbnode_id'"
        )

    def test_delete_many_same_twice(self):
        """Test no exception is raised when entity is filtered by both `id` and `uuid`"""
        # Create comment
        comment = self.create_comment()
        comment.store()
        comment_id = comment.id
        comment_uuid = comment.uuid

        # Try to delete Comment by specifying both `id` and `uuid` for it - nothing should be raised
        self.backend.comments.delete_many(filters={'id': comment_id, 'uuid': comment_uuid})

        # Make sure comment is removed
        builder = orm.QueryBuilder().append(orm.Comment, filters={'uuid': comment_uuid})
        self.assertEqual(builder.count(), 0)

    def test_delete_wrong_type(self):
        """Test TypeError is raised when `filters` is wrong type"""
        with self.assertRaises(TypeError):
            self.backend.comments.delete(comment_id=None)

    def test_delete_many_wrong_type(self):
        """Test TypeError is raised when `filters` is wrong type"""
        with self.assertRaises(TypeError):
            self.backend.comments.delete_many(filters=None)
