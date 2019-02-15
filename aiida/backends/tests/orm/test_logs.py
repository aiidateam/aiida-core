# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""ORM Log tests"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from six.moves import range

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.common.timezone import now
from aiida.orm import Data
from aiida.orm import Log
from aiida.orm import CalculationNode


class TestBackendLog(AiidaTestCase):
    """Test the Log entity"""

    def setUp(self):
        super(TestBackendLog, self).setUp()
        self.log_record = {
            'time': now(),
            'loggername': 'loggername',
            'levelname': logging.getLevelName(LOG_LEVEL_REPORT),
            'dbnode_id': None,
            'message': 'This is a template record message',
            'metadata': {
                'content': 'test'
            },
        }

    def tearDown(self):
        """
        Delete all the created log entries
        """
        super(TestBackendLog, self).tearDown()
        Log.objects.delete_many({})

    def create_log(self):
        node = CalculationNode().store()
        record = self.log_record
        record['dbnode_id'] = node.id
        return Log(**record), node

    def test_create_log_message(self):
        """
        Test the manual creation of a log entry
        """
        entry, _ = self.create_log()

        self.assertEqual(entry.time, self.log_record['time'])
        self.assertEqual(entry.loggername, self.log_record['loggername'])
        self.assertEqual(entry.levelname, self.log_record['levelname'])
        self.assertEqual(entry.dbnode_id, self.log_record['dbnode_id'])
        self.assertEqual(entry.message, self.log_record['message'])
        self.assertEqual(entry.metadata, self.log_record['metadata'])

    def test_create_log_unserializable_metadata(self):
        """Test that unserializable data will be removed before reaching the database causing an error."""
        import functools

        def unbound_method(argument):
            return argument

        partial = functools.partial(unbound_method, 'argument')

        node = CalculationNode().store()

        # An unbound method in the `args` of the metadata
        node.logger.error('problem occurred in method %s', unbound_method)

        # A partial in the `args` of the metadata
        node.logger.error('problem occurred in partial %s', partial)

        # An exception which will include an `exc_info` object
        try:
            raise ValueError
        except ValueError:
            node.logger.exception('caught an exception')

        self.assertEqual(len(Log.objects.all()), 3)

    def test_log_delete_single(self):
        """Test that a single log entry can be deleted through the collection."""
        entry, _ = self.create_log()
        log_id = entry.id

        self.assertEqual(len(Log.objects.all()), 1)

        # Deleting the entry
        Log.objects.delete(log_id)
        self.assertEqual(len(Log.objects.all()), 0)

        # Deleting a non-existing entry should raise
        with self.assertRaises(exceptions.NotExistent):
            Log.objects.delete(log_id)

    def test_delete_many(self):
        """
        Test deleting all log entries
        Bit superfluous, given that other tests most likely would fail
        anyway if this method does not work properly
        """
        count = 10
        for _ in range(count):
            self.create_log()

        self.assertEqual(len(Log.objects.all()), count)
        Log.objects.delete_many({})
        self.assertEqual(len(Log.objects.all()), 0)

    def test_objects_find(self):
        """Put logs in and find them"""
        node = Data().store()
        for _ in range(10):
            record = self.log_record
            record['dbnode_id'] = node.id
            Log(**record)

        entries = Log.objects.all()
        self.assertEqual(10, len(entries))
        self.assertIsInstance(entries[0], Log)

    def test_find_orderby(self):
        """
        Test the order_by option of log.find
        """
        from aiida.orm.logs import OrderSpecifier, ASCENDING, DESCENDING

        node_ids = []
        for _ in range(10):
            _, node = self.create_log()
            node_ids.append(node.id)
        node_ids.sort()

        order_by = [OrderSpecifier('dbnode_id', ASCENDING)]
        res_entries = Log.objects.find(order_by=order_by)
        self.assertEqual(res_entries[0].dbnode_id, node_ids[0])

        order_by = [OrderSpecifier('dbnode_id', DESCENDING)]
        res_entries = Log.objects.find(order_by=order_by)
        self.assertEqual(res_entries[0].dbnode_id, node_ids[-1])

    def test_find_limit(self):
        """
        Test the limit option of log.find
        """
        node = Data().store()
        limit = 2
        for _ in range(limit * 2):
            self.log_record['dbnode_id'] = node.id
            Log(**self.log_record)
        entries = Log.objects.find(limit=limit)
        self.assertEqual(len(entries), limit)

    def test_find_filter(self):
        """
        Test the filter option of log.find
        """
        from random import randint

        node_ids = []
        for _ in range(10):
            _, node = self.create_log()
            node_ids.append(node.id)

        node_id_of_choice = node_ids.pop(randint(0, 9))

        entries = Log.objects.find(filters={'dbnode_id': node_id_of_choice})
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].dbnode_id, node_id_of_choice)

    def test_db_log_handler(self):
        """
        Verify that the db log handler is attached correctly
        by firing a log message through the regular logging module
        attached to a calculation node
        """
        from aiida.orm.logs import OrderSpecifier, ASCENDING

        message = 'Testing logging of critical failure'
        node = CalculationNode()

        # Firing a log for an unstored should not end up in the database
        node.logger.critical(message)

        logs = Log.objects.find()

        self.assertEqual(len(logs), 0)

        # After storing the node, logs above log level should be stored
        node.store()
        node.logger.critical(message)
        logs = Log.objects.find()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].message, message)

        # Launching a second log message ensuring that both messages are correctly stored
        message2 = message + " - Second message"
        node.logger.critical(message2)

        order_by = [OrderSpecifier('time', ASCENDING)]
        logs = Log.objects.find(order_by=order_by)

        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].message, message)
        self.assertEqual(logs[1].message, message2)

    def test_log_querybuilder(self):
        """ Test querying for logs by joining on nodes in the QueryBuilder """
        from aiida.orm import QueryBuilder

        # Setup nodes
        log_1, calc = self.create_log()
        log_2 = Log(now(), 'loggername', logging.getLevelName(LOG_LEVEL_REPORT), calc.id, 'log message #2')
        log_3 = Log(now(), 'loggername', logging.getLevelName(LOG_LEVEL_REPORT), calc.id, 'log message #3')

        # Retrieve a node by joining on a specific log ('log_1')
        builder = QueryBuilder()
        builder.append(Log, tag='log', filters={'id': log_2.id})
        builder.append(CalculationNode, with_log='log', project=['uuid'])
        nodes = builder.all()

        self.assertEqual(len(nodes), 1)
        for node in nodes:
            self.assertIn(str(node[0]), [calc.uuid])

        # Retrieve all logs for a specific node by joining on a said node
        builder = QueryBuilder()
        builder.append(CalculationNode, tag='calc', filters={'id': calc.id})
        builder.append(Log, with_node='calc', project=['uuid'])
        logs = builder.all()

        self.assertEqual(len(logs), 3)
        for log in logs:
            self.assertIn(str(log[0]), [str(log_1.uuid), str(log_2.uuid), str(log_3.uuid)])

    def test_raise_wrong_metadata_type_error(self):
        """
        Test a TypeError exception is thrown with string metadata.
        Also test that metadata is correctly created.
        """
        from aiida.common import json

        # Create CalculationNode
        calc = CalculationNode().store()

        # dict metadata
        correct_metadata_format = {
            'msg': 'Life is like riding a bicycle.',
            'args': '()',
            'name': 'aiida.orm.node.process.calculation.CalculationNode'
        }

        # str of dict metadata
        wrong_metadata_format = str(correct_metadata_format)

        # JSON-serialized-deserialized dict metadata
        json_metadata_format = json.loads(json.dumps(correct_metadata_format))

        # Check an error is raised when creating a Log with wrong metadata
        with self.assertRaises(TypeError):
            Log(now(),
                'loggername',
                logging.getLevelName(LOG_LEVEL_REPORT),
                calc.id,
                'To keep your balance, you must keep moving',
                metadata=wrong_metadata_format)

        # Check no error is raised when creating a Log with dict metadata
        correct_metadata_log = Log(
            now(),
            'loggername',
            logging.getLevelName(LOG_LEVEL_REPORT),
            calc.id,
            'To keep your balance, you must keep moving',
            metadata=correct_metadata_format)

        # Check metadata is correctly created
        self.assertEqual(correct_metadata_log.metadata, correct_metadata_format)

        # Create Log with json metadata, making sure TypeError is NOT raised
        json_metadata_log = Log(
            now(),
            'loggername',
            logging.getLevelName(LOG_LEVEL_REPORT),
            calc.id,
            'To keep your balance, you must keep moving',
            metadata=json_metadata_format)

        # Check metadata is correctly created
        self.assertEqual(json_metadata_log.metadata, json_metadata_format)

        # Check no error is raised if no metadata is given
        no_metadata_log = Log(
            now(),
            'loggername',
            logging.getLevelName(LOG_LEVEL_REPORT),
            calc.id,
            'To keep your balance, you must keep moving',
            metadata=None)

        # Check metadata is an empty dict for no_metadata_log
        self.assertEqual(no_metadata_log.metadata, {})
