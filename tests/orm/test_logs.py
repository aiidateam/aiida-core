###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""ORM Log tests"""

import json
import logging

import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.common.timezone import now
from aiida.orm import Log


class TestBackendLog:
    """Test the Log entity"""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        self.log_record = {
            'time': now(),
            'loggername': 'loggername',
            'levelname': logging.getLevelName(LOG_LEVEL_REPORT),
            'dbnode_id': None,
            'message': 'This is a template record message',
            'metadata': {'content': 'test'},
        }

    def create_log(self):
        node = orm.CalculationNode().store()
        record = self.log_record
        record['dbnode_id'] = node.pk
        return Log(**record), node

    def test_create_log_message(self):
        """Test the manual creation of a log entry"""
        entry, node = self.create_log()

        assert entry.time == self.log_record['time']
        assert entry.loggername == self.log_record['loggername']
        assert entry.levelname == self.log_record['levelname']
        assert entry.message == self.log_record['message']
        assert entry.metadata == self.log_record['metadata']
        assert entry.dbnode_id == self.log_record['dbnode_id']
        assert entry.dbnode_id == node.pk

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_create_log_unserializable_metadata(self):
        """Test that unserializable data will be removed before reaching the database causing an error."""
        import functools

        def unbound_method(argument):
            return argument

        partial = functools.partial(unbound_method, 'argument')

        node = orm.CalculationNode().store()

        # An unbound method in the `args` of the metadata
        node.logger.error('problem occurred in method %s', unbound_method)

        # A partial in the `args` of the metadata
        node.logger.error('problem occurred in partial %s', partial)

        # An exception which will include an `exc_info` object
        try:
            raise ValueError
        except ValueError:
            node.logger.exception('caught an exception')

        assert len(Log.collection.all()) == 3

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_log_delete_single(self):
        """Test that a single log entry can be deleted through the collection."""
        entry, _ = self.create_log()
        log_id = entry.pk

        assert len(Log.collection.all()) == 1

        # Deleting the entry
        Log.collection.delete(log_id)
        assert len(Log.collection.all()) == 0

        # Deleting a non-existing entry should raise
        with pytest.raises(exceptions.NotExistent):
            Log.collection.delete(log_id)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_log_collection_delete_all(self):
        """Test deleting all Log entries through collection"""
        count = 10
        for _ in range(count):
            self.create_log()
        log_id = Log.collection.find(limit=1)[0].pk

        assert len(Log.collection.all()) == count

        # Delete all
        Log.collection.delete_all()

        # Checks
        assert len(Log.collection.all()) == 0

        with pytest.raises(exceptions.NotExistent):
            Log.collection.delete(log_id)

        with pytest.raises(exceptions.NotExistent):
            Log.collection.get(id=log_id)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_log_collection_delete_many(self):
        """Test deleting many Logs through the collection."""
        log_ids = []
        count = 5
        for _ in range(count):
            log_, _ = self.create_log()
            log_ids.append(log_.pk)
        special_log, _ = self.create_log()

        # Assert the Logs exist
        assert len(Log.collection.all()) == count + 1

        # Delete new Logs using filter
        filters = {'id': {'in': log_ids}}
        Log.collection.delete_many(filters=filters)

        # Make sure only the special_log Log is left
        builder = orm.QueryBuilder().append(Log, project='id')
        assert builder.count() == 1
        assert builder.all()[0][0] == special_log.pk

        for log_id in log_ids:
            with pytest.raises(exceptions.NotExistent):
                Log.collection.delete(log_id)

            with pytest.raises(exceptions.NotExistent):
                Log.collection.get(id=log_id)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_objects_find(self):
        """Put logs in and find them"""
        node = orm.Data().store()
        for _ in range(10):
            record = self.log_record
            record['dbnode_id'] = node.pk
            Log(**record)

        entries = Log.collection.all()
        assert len(entries) == 10
        assert isinstance(entries[0], Log)

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_find_orderby(self):
        """Test the order_by option of log.find"""
        from aiida.orm.logs import ASCENDING, DESCENDING, OrderSpecifier

        node_ids = []
        for _ in range(10):
            _, node = self.create_log()
            node_ids.append(node.pk)
        node_ids.sort()

        order_by = [OrderSpecifier('dbnode_id', ASCENDING)]
        res_entries = Log.collection.find(order_by=order_by)
        assert res_entries[0].dbnode_id == node_ids[0]

        order_by = [OrderSpecifier('dbnode_id', DESCENDING)]
        res_entries = Log.collection.find(order_by=order_by)
        assert res_entries[0].dbnode_id == node_ids[-1]

    def test_find_limit(self):
        """Test the limit option of log.find"""
        node = orm.Data().store()
        limit = 2
        for _ in range(limit * 2):
            self.log_record['dbnode_id'] = node.pk
            Log(**self.log_record)
        entries = Log.collection.find(limit=limit)
        assert len(entries) == limit

    def test_find_filter(self):
        """Test the filter option of log.find"""
        from random import randint

        node_ids = []
        for _ in range(10):
            _, node = self.create_log()
            node_ids.append(node.pk)

        node_id_of_choice = node_ids.pop(randint(0, 9))

        entries = Log.collection.find(filters={'dbnode_id': node_id_of_choice})
        assert len(entries) == 1
        assert entries[0].dbnode_id == node_id_of_choice

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_db_log_handler(self):
        """Verify that the db log handler is attached correctly
        by firing a log message through the regular logging module
        attached to a calculation node
        """
        from aiida.orm.logs import ASCENDING, OrderSpecifier

        message = 'Testing logging of critical failure'
        node = orm.CalculationNode()

        # Firing a log for an unstored should not end up in the database
        node.logger.critical(message)

        logs = Log.collection.find()

        assert len(logs) == 0

        # After storing the node, logs above log level should be stored
        node.store()
        node.logger.critical(message)
        logs = Log.collection.find()

        assert len(logs) == 1
        assert logs[0].message == message

        # Launching a second log message ensuring that both messages are correctly stored
        message2 = f'{message} - Second message'
        node.logger.critical(message2)

        order_by = [OrderSpecifier('time', ASCENDING)]
        logs = Log.collection.find(order_by=order_by)

        assert len(logs) == 2
        assert logs[0].message == message
        assert logs[1].message == message2

    def test_log_querybuilder(self):
        """Test querying for logs by joining on nodes in the QueryBuilder"""
        from aiida.orm import QueryBuilder

        # Setup nodes
        log_1, calc = self.create_log()
        log_2 = Log(now(), 'loggername', logging.getLevelName(LOG_LEVEL_REPORT), calc.pk, 'log message #2')
        log_3 = Log(now(), 'loggername', logging.getLevelName(LOG_LEVEL_REPORT), calc.pk, 'log message #3')

        # Retrieve a node by joining on a specific log ('log_1')
        builder = QueryBuilder()
        builder.append(Log, tag='log', filters={'id': log_2.pk})
        builder.append(orm.CalculationNode, with_log='log', project=['uuid'])
        nodes = builder.all()

        assert len(nodes) == 1
        for node in nodes:
            assert str(node[0]) in [calc.uuid]

        # Retrieve all logs for a specific node by joining on a said node
        builder = QueryBuilder()
        builder.append(orm.CalculationNode, tag='calc', filters={'id': calc.pk})
        builder.append(Log, with_node='calc', project=['uuid'])
        logs = builder.all()

        assert len(logs) == 3
        for log in logs:
            assert str(log[0]) in [str(log_1.uuid), str(log_2.uuid), str(log_3.uuid)]

    def test_raise_wrong_metadata_type_error(self):
        """Test a TypeError exception is thrown with string metadata.
        Also test that metadata is correctly created.
        """
        # Create CalculationNode
        calc = orm.CalculationNode().store()

        # dict metadata
        correct_metadata_format = {
            'msg': 'Life is like riding a bicycle.',
            'args': '()',
            'name': 'aiida.orm.node.process.calculation.CalculationNode',
        }

        # str of dict metadata
        wrong_metadata_format = str(correct_metadata_format)

        # JSON-serialized-deserialized dict metadata
        json_metadata_format = json.loads(json.dumps(correct_metadata_format))

        # Check an error is raised when creating a Log with wrong metadata
        with pytest.raises(TypeError):
            Log(
                now(),
                'loggername',
                logging.getLevelName(LOG_LEVEL_REPORT),
                calc.pk,
                'To keep your balance, you must keep moving',
                metadata=wrong_metadata_format,
            )

        # Check no error is raised when creating a Log with dict metadata
        correct_metadata_log = Log(
            now(),
            'loggername',
            logging.getLevelName(LOG_LEVEL_REPORT),
            calc.pk,
            'To keep your balance, you must keep moving',
            metadata=correct_metadata_format,
        )

        # Check metadata is correctly created
        assert correct_metadata_log.metadata == correct_metadata_format

        # Create Log with json metadata, making sure TypeError is NOT raised
        json_metadata_log = Log(
            now(),
            'loggername',
            logging.getLevelName(LOG_LEVEL_REPORT),
            calc.pk,
            'To keep your balance, you must keep moving',
            metadata=json_metadata_format,
        )

        # Check metadata is correctly created
        assert json_metadata_log.metadata == json_metadata_format

        # Check no error is raised if no metadata is given
        no_metadata_log = Log(
            now(),
            'loggername',
            logging.getLevelName(LOG_LEVEL_REPORT),
            calc.pk,
            'To keep your balance, you must keep moving',
            metadata=None,
        )

        # Check metadata is an empty dict for no_metadata_log
        assert no_metadata_log.metadata == {}
