# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the BackendLog and BackendLogCollection classes."""

import logging
from datetime import datetime
from uuid import UUID

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.common import timezone
from aiida.common.log import LOG_LEVEL_REPORT


class TestBackendLog(AiidaTestCase):
    """Test BackendLog."""

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
        self.log_message = 'log message'

    def create_log(self, **kwargs):
        """Create BackendLog"""
        time = kwargs['time'] if 'time' in kwargs else timezone.now()
        dbnode_id = kwargs['dbnode_id'] if 'dbnode_id' in kwargs else self.node.id

        return self.backend.logs.create(
            time=time,
            loggername='loggername',
            levelname=logging.getLevelName(LOG_LEVEL_REPORT),
            dbnode_id=dbnode_id,
            message=self.log_message,
            metadata={'content': 'test'}
        )

    def test_creation(self):
        """Test creation of a BackendLog and all its properties."""
        log = self.create_log()

        # Before storing
        self.assertIsNone(log.id)
        self.assertIsNone(log.pk)
        self.assertTrue(isinstance(log.uuid, str))
        self.assertTrue(isinstance(log.time, datetime))
        self.assertEqual(log.loggername, 'loggername')
        self.assertTrue(isinstance(log.levelname, str))
        self.assertTrue(isinstance(log.dbnode_id, int))
        self.assertEqual(log.message, self.log_message)
        self.assertEqual(log.metadata, {'content': 'test'})

        log.store()

        # After storing
        self.assertTrue(isinstance(log.id, int))
        self.assertTrue(isinstance(log.pk, int))
        self.assertTrue(isinstance(log.uuid, str))
        self.assertTrue(isinstance(log.time, datetime))
        self.assertEqual(log.loggername, 'loggername')
        self.assertTrue(isinstance(log.levelname, str))
        self.assertTrue(isinstance(log.dbnode_id, int))
        self.assertEqual(log.message, self.log_message)
        self.assertEqual(log.metadata, {'content': 'test'})

        # Try to construct a UUID from the UUID value to prove that it has a valid UUID
        UUID(log.uuid)

        # Raise AttributeError when trying to change column
        with self.assertRaises(AttributeError):
            log.message = 'change message'

    def test_creation_with_static_time(self):
        """
        Test creation of a BackendLog when passing the mtime and the ctime. The passed ctime and mtime
        should be respected since it is important for the correct import of nodes at the AiiDA import/export.
        """
        from aiida.tools.importexport.dbimport.backends.utils import deserialize_attributes

        time = deserialize_attributes('2019-02-27T16:20:12.245738', 'date')

        log = self.create_log(time=time)

        # Check that the time is the given one
        self.assertEqual(log.time, time)

        # Store
        self.assertFalse(log.is_stored)
        log.store()
        self.assertTrue(log.is_stored)

        # Check that the given value remains even after storing
        self.assertEqual(log.time, time)

    def test_delete(self):
        """Test `delete` method"""
        # Create Log, making sure it exists
        log = self.create_log()
        log.store()
        log_uuid = str(log.uuid)

        builder = orm.QueryBuilder().append(orm.Log, project='uuid')
        no_of_logs = builder.count()
        found_logs_uuid = [_[0] for _ in builder.all()]
        self.assertIn(log_uuid, found_logs_uuid)

        # Delete Log, making sure it was deleted
        self.backend.logs.delete(log.id)

        builder = orm.QueryBuilder().append(orm.Log, project='uuid')
        self.assertEqual(builder.count(), no_of_logs - 1)
        found_logs_uuid = [_[0] for _ in builder.all()]
        self.assertNotIn(log_uuid, found_logs_uuid)

    def test_delete_all(self):
        """Test `delete_all` method"""
        self.create_log().store()
        self.assertGreater(len(orm.Log.objects.all()), 0, msg='There should be Logs in the database')

        self.backend.logs.delete_all()
        self.assertEqual(len(orm.Log.objects.all()), 0, msg='All Logs should have been deleted')

    def test_delete_many_no_filters(self):
        """Test `delete_many` method with empty filters"""
        self.create_log().store()
        count = len(orm.Log.objects.all())
        self.assertGreater(count, 0)

        # Pass empty filter to delete_many, making sure ValidationError is raised
        with self.assertRaises(exceptions.ValidationError):
            self.backend.logs.delete_many({})
        self.assertEqual(
            len(orm.Log.objects.all()),
            count,
            msg='No Logs should have been deleted. There should still be {} Log(s), '
            'however {} Log(s) was/were found.'.format(count, len(orm.Log.objects.all()))
        )

    def test_delete_many_ids(self):
        """Test `delete_many` method filtering on both `id` and `uuid`"""
        # Create logs
        log1 = self.create_log()
        log2 = self.create_log()
        log3 = self.create_log()
        log_uuids = []
        for log in [log1, log2, log3]:
            log.store()
            log_uuids.append(str(log.uuid))

        # Make sure they exist
        count_logs_found = orm.QueryBuilder().append(orm.Log, filters={'uuid': {'in': log_uuids}}).count()
        self.assertEqual(
            count_logs_found,
            len(log_uuids),
            msg='There should be {} Logs, instead {} Log(s) was/were found'.format(len(log_uuids), count_logs_found)
        )

        # Delete last two logs (log2, log3)
        filters = {'or': [{'id': log2.id}, {'uuid': str(log3.uuid)}]}
        self.backend.logs.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': {'in': log_uuids}}, project='uuid').all()
        found_logs_uuid = [_[0] for _ in builder]
        self.assertEqual([log_uuids[0]], found_logs_uuid)

    def test_delete_many_dbnode_id(self):
        """Test `delete_many` method filtering on `dbnode_id`"""
        # Create logs and separate node
        calc = self.backend.nodes.create(
            node_type='', user=self.user, computer=self.computer, label='label', description='description'
        ).store()
        log1 = self.create_log(dbnode_id=calc.id)
        log2 = self.create_log()
        log3 = self.create_log()
        log_uuids = []
        for log in [log1, log2, log3]:
            log.store()
            log_uuids.append(str(log.uuid))

        # Make sure they exist
        count_logs_found = orm.QueryBuilder().append(orm.Log, filters={'uuid': {'in': log_uuids}}).count()
        self.assertEqual(
            count_logs_found,
            len(log_uuids),
            msg='There should be {} Logs, instead {} Log(s) was/were found'.format(len(log_uuids), count_logs_found)
        )

        # Delete logs for self.node
        filters = {'dbnode_id': self.node.id}
        self.backend.logs.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': {'in': log_uuids}}, project='uuid').all()
        found_logs_uuid = [_[0] for _ in builder]
        self.assertEqual([log_uuids[0]], found_logs_uuid)

    def test_delete_many_time(self):
        """Test `delete_many` method filtering on `time`"""
        from datetime import timedelta

        # Initialization
        log_uuids = []
        found_logs_time = []
        found_logs_uuid = []

        now = timezone.now()
        two_days_ago = now - timedelta(days=2)
        one_day_ago = now - timedelta(days=1)
        log_times = [now, one_day_ago, two_days_ago]

        # Create logs
        log1 = self.create_log(time=now)
        log2 = self.create_log(time=one_day_ago)
        log3 = self.create_log(time=two_days_ago)
        for log in [log1, log2, log3]:
            log.store()
            log_uuids.append(str(log.uuid))

        # Make sure they exist with the correct times
        builder = orm.QueryBuilder().append(orm.Log, project=['time', 'uuid'])
        self.assertGreater(builder.count(), 0)
        for log in builder.all():
            found_logs_time.append(log[0])
            found_logs_uuid.append(log[1])
        for log_time in log_times:
            self.assertIn(log_time, found_logs_time)
        for log_uuid in log_uuids:
            self.assertIn(log_uuid, found_logs_uuid)

        # Delete logs that are older than 1 hour
        turning_point = now - timedelta(seconds=60 * 60)
        filters = {'time': {'<': turning_point}}
        self.backend.logs.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Log, project='uuid')
        self.assertGreater(builder.count(), 0)  # There should still be at least 1
        found_logs_uuid = [_[0] for _ in builder.all()]
        for log_uuid in log_uuids[1:]:
            self.assertNotIn(log_uuid, found_logs_uuid)

        # Make sure the newest log (log1) was not deleted
        self.assertIn(log_uuids[0], found_logs_uuid)

    def test_deleting_non_existent_entities(self):
        """Test deleting non-existent Logs for different cases"""
        # Create Log
        log = self.create_log()
        log.store()
        log_id = log.id
        log_uuid = log.uuid

        # Get non-existent Log
        valid_log_found = True
        id_ = 0
        while valid_log_found:
            id_ += 1
            builder = orm.QueryBuilder().append(orm.Log, filters={'id': id_})
            if builder.count() == 0:
                valid_log_found = False

        # Try to delete non-existing Log - using delete_many
        # delete_many should return an empty list
        deleted_entities = self.backend.logs.delete_many(filters={'id': id_})
        self.assertEqual(
            deleted_entities, [],
            msg='No entities should have been deleted, since Log id {} does not exist'.format(id_)
        )

        # Try to delete non-existing Log - using delete
        # NotExistent should be raised, since no entities are found
        with self.assertRaises(exceptions.NotExistent) as exc:
            self.backend.logs.delete(log_id=id_)
        self.assertIn("Log with id '{}' not found".format(id_), str(exc.exception))

        # Try to delete existing and non-existing Log - using delete_many
        # delete_many should return a list that *only* includes the existing Logs
        filters = {'id': {'in': [id_, log_id]}}
        deleted_entities = self.backend.logs.delete_many(filters=filters)
        self.assertEqual([log_id],
                         deleted_entities,
                         msg='Only Log id {} should be returned from delete_many'.format(log_id))

        # Make sure the existing Log was deleted
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': log_uuid})
        self.assertEqual(builder.count(), 0)

        # Get a non-existent Node
        valid_node_found = True
        id_ = 0
        while valid_node_found:
            id_ += 1
            builder = orm.QueryBuilder().append(orm.Node, filters={'id': id_})
            if builder.count() == 0:
                valid_node_found = False

        # Try to delete Logs filtering on non-existing dbnode_id
        # NotExistent should NOT be raised nor should any Logs be deleted
        log_count_before = orm.QueryBuilder().append(orm.Log).count()
        filters = {'dbnode_id': id_}
        self.backend.logs.delete_many(filters=filters)
        log_count_after = orm.QueryBuilder().append(orm.Log).count()
        self.assertEqual(
            log_count_after,
            log_count_before,
            msg='The number of logs changed after performing `delete_many`, '
            "while filtering for a non-existing 'dbnode_id'"
        )

    def test_delete_many_same_twice(self):
        """Test no exception is raised when entity is filtered by both `id` and `uuid`"""
        # Create log
        log = self.create_log()
        log.store()
        log_id = log.id
        log_uuid = log.uuid

        # Try to delete Log by specifying both `id` and `uuid` for it - nothing should be raised
        self.backend.logs.delete_many(filters={'id': log_id, 'uuid': log_uuid})

        # Make sure log is removed
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': log_uuid})
        self.assertEqual(builder.count(), 0)

    def test_delete_wrong_type(self):
        """Test TypeError is raised when `filters` is wrong type"""
        with self.assertRaises(TypeError):
            self.backend.logs.delete(log_id=None)

    def test_delete_many_wrong_type(self):
        """Test TypeError is raised when `filters` is wrong type"""
        with self.assertRaises(TypeError):
            self.backend.logs.delete_many(filters=None)
