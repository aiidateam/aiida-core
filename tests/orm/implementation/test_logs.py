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
from uuid import UUID, uuid4

import pytest

from aiida import orm
from aiida.common import exceptions, timezone
from aiida.common.log import LOG_LEVEL_REPORT


class TestBackendLog:
    """Test BackendLog."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost, backend):
        """Initialize the profile."""
        self.backend = backend
        self.computer = aiida_localhost.backend_entity  # Unwrap the `Computer` instance to `BackendComputer`
        self.user = self.backend.users.create(email=uuid4().hex).store()
        self.node = self.backend.nodes.create(
            node_type='', user=self.user, computer=self.computer, label=uuid4().hex, description='description'
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
            metadata={'content': 'test'},
        )

    def test_creation(self):
        """Test creation of a BackendLog and all its properties."""
        log = self.create_log()

        # Before storing
        assert log.id is None
        assert log.pk is None
        assert isinstance(log.uuid, str)
        assert isinstance(log.time, datetime)
        assert log.loggername == 'loggername'
        assert isinstance(log.levelname, str)
        assert isinstance(log.dbnode_id, int)
        assert log.message == self.log_message
        assert log.metadata == {'content': 'test'}

        log.store()

        # After storing
        assert isinstance(log.id, int)
        assert isinstance(log.pk, int)
        assert isinstance(log.uuid, str)
        assert isinstance(log.time, datetime)
        assert log.loggername == 'loggername'
        assert isinstance(log.levelname, str)
        assert isinstance(log.dbnode_id, int)
        assert log.message == self.log_message
        assert log.metadata == {'content': 'test'}

        # Try to construct a UUID from the UUID value to prove that it has a valid UUID
        UUID(log.uuid)

        # Raise AttributeError when trying to change column
        with pytest.raises(AttributeError):
            log.message = 'change message'

    def test_creation_with_static_time(self):
        """Test creation of a BackendLog when passing the mtime and the ctime. The passed ctime and mtime
        should be respected since it is important for the correct import of nodes at the AiiDA import/export.
        """
        time = datetime(2019, 2, 27, 16, 20, 12, 245738, timezone.utc)

        log = self.create_log(time=time)

        # Check that the time is the given one
        assert log.time == time

        # Store
        assert not log.is_stored
        log.store()
        assert log.is_stored

        # Check that the given value remains even after storing
        assert log.time == time

    def test_delete(self):
        """Test `delete` method"""
        # Create Log, making sure it exists
        log = self.create_log()
        log.store()
        log_uuid = str(log.uuid)

        builder = orm.QueryBuilder().append(orm.Log, project='uuid')
        no_of_logs = builder.count()
        found_logs_uuid = [_[0] for _ in builder.all()]
        assert log_uuid in found_logs_uuid

        # Delete Log, making sure it was deleted
        self.backend.logs.delete(log.id)

        builder = orm.QueryBuilder().append(orm.Log, project='uuid')
        assert builder.count() == no_of_logs - 1
        found_logs_uuid = [_[0] for _ in builder.all()]
        assert log_uuid not in found_logs_uuid

    def test_delete_all(self):
        """Test `delete_all` method"""
        self.create_log().store()
        assert len(orm.Log.collection.all()) > 0, 'There should be Logs in the database'

        self.backend.logs.delete_all()
        assert len(orm.Log.collection.all()) == 0, 'All Logs should have been deleted'

    def test_delete_many_no_filters(self):
        """Test `delete_many` method with empty filters"""
        self.create_log().store()
        count = len(orm.Log.collection.all())
        assert count > 0

        # Pass empty filter to delete_many, making sure ValidationError is raised
        with pytest.raises(exceptions.ValidationError):
            self.backend.logs.delete_many({})
        assert len(orm.Log.collection.all()) == count, (
            'No Logs should have been deleted. There should still be {} Log(s), '
            'however {} Log(s) was/were found.'.format(count, len(orm.Log.collection.all()))
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
        assert count_logs_found == len(
            log_uuids
        ), f'There should be {len(log_uuids)} Logs, instead {count_logs_found} Log(s) was/were found'

        # Delete last two logs (log2, log3)
        filters = {'or': [{'id': log2.id}, {'uuid': str(log3.uuid)}]}
        self.backend.logs.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': {'in': log_uuids}}, project='uuid').all()
        found_logs_uuid = [_[0] for _ in builder]
        assert [log_uuids[0]] == found_logs_uuid

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
        assert count_logs_found == len(
            log_uuids
        ), f'There should be {len(log_uuids)} Logs, instead {count_logs_found} Log(s) was/were found'

        # Delete logs for self.node
        filters = {'dbnode_id': self.node.id}
        self.backend.logs.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': {'in': log_uuids}}, project='uuid').all()
        found_logs_uuid = [_[0] for _ in builder]
        assert [log_uuids[0]] == found_logs_uuid

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
        assert builder.count() > 0
        for log in builder.all():
            found_logs_time.append(log[0])
            found_logs_uuid.append(log[1])
        for log_time in log_times:
            assert log_time in found_logs_time
        for log_uuid in log_uuids:
            assert log_uuid in found_logs_uuid

        # Delete logs that are older than 1 hour
        turning_point = now - timedelta(seconds=60 * 60)
        filters = {'time': {'<': turning_point}}
        self.backend.logs.delete_many(filters=filters)

        # Check they were deleted
        builder = orm.QueryBuilder().append(orm.Log, project='uuid')
        assert builder.count() > 0  # There should still be at least 1
        found_logs_uuid = [_[0] for _ in builder.all()]
        for log_uuid in log_uuids[1:]:
            assert log_uuid not in found_logs_uuid

        # Make sure the newest log (log1) was not deleted
        assert log_uuids[0] in found_logs_uuid

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
        assert deleted_entities == [], f'No entities should have been deleted, since Log id {id_} does not exist'

        # Try to delete non-existing Log - using delete
        # NotExistent should be raised, since no entities are found
        with pytest.raises(exceptions.NotExistent) as exc:
            self.backend.logs.delete(log_id=id_)
        assert f"Log with id '{id_}' not found" in str(exc)

        # Try to delete existing and non-existing Log - using delete_many
        # delete_many should return a list that *only* includes the existing Logs
        filters = {'id': {'in': [id_, log_id]}}
        deleted_entities = self.backend.logs.delete_many(filters=filters)
        assert [log_id] == deleted_entities, f'Only Log id {log_id} should be returned from delete_many'

        # Make sure the existing Log was deleted
        builder = orm.QueryBuilder().append(orm.Log, filters={'uuid': log_uuid})
        assert builder.count() == 0

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
        assert log_count_after == log_count_before, (
            'The number of logs changed after performing `delete_many`, '
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
        assert builder.count() == 0

    def test_delete_wrong_type(self):
        """Test TypeError is raised when `filters` is wrong type"""
        with pytest.raises(TypeError):
            self.backend.logs.delete(log_id=None)

    def test_delete_many_wrong_type(self):
        """Test TypeError is raised when `filters` is wrong type"""
        with pytest.raises(TypeError):
            self.backend.logs.delete_many(filters=None)
