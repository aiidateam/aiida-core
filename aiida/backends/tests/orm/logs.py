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

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.common.log import LOG_LEVEL_REPORT
from aiida.orm.node import CalculationNode
from aiida.common.timezone import now


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
        orm.Log.objects.delete_many({})

    def test_create_log_message(self):
        """
        Test the manual creation of a log entry
        """
        node = orm.Data().store()
        self.log_record['dbnode_id'] = node.id
        entry = orm.Log(**self.log_record)

        self.assertEqual(entry.time, self.log_record['time'])
        self.assertEqual(entry.loggername, self.log_record['loggername'])
        self.assertEqual(entry.levelname, self.log_record['levelname'])
        self.assertEqual(entry.dbnode_id, self.log_record['dbnode_id'])
        self.assertEqual(entry.message, self.log_record['message'])
        self.assertEqual(entry.metadata, self.log_record['metadata'])

    def test_log_delete_single(self):
        """Test that a single log entry can be deleted through the collection."""
        node = orm.Data().store()
        self.log_record['dbnode_id'] = node.id
        entry = orm.Log(**self.log_record)

        log_id = entry.id

        self.assertEqual(len(orm.Log.objects.all()), 1)

        # Deleting the entry
        orm.Log.objects.delete(log_id)
        self.assertEqual(len(orm.Log.objects.all()), 0)

        # Deleting a non-existing entry should raise
        with self.assertRaises(exceptions.NotExistent):
            orm.Log.objects.delete(log_id)

    def test_delete_many(self):
        """
        Test deleting all log entries
        Bit superfluous, given that other tests most likely would fail
        anyway if this method does not work properly
        """
        count = 10
        node = orm.Data().store()
        for _ in range(count):
            self.log_record['dbnode_id'] = node.id
            orm.Log(**self.log_record)

        self.assertEqual(len(orm.Log.objects.all()), count)
        orm.Log.objects.delete_many({})
        self.assertEqual(len(orm.Log.objects.all()), 0)

    def test_objects_find(self):
        """Put logs in and find them"""
        node = orm.Data().store()
        for _ in range(10):
            record = self.log_record
            record['dbnode_id'] = node.id
            orm.Log(**record)

        entries = orm.Log.objects.all()
        self.assertEqual(10, len(entries))
        self.assertIsInstance(entries[0], orm.Log)

    def test_find_orderby(self):
        """
        Test the order_by option of log.find
        """
        from aiida.orm.logs import OrderSpecifier, ASCENDING, DESCENDING

        min_id, max_id = None, None
        for counter in range(10):
            node = orm.Data().store()
            if counter == 0:
                min_id = node.id
            elif counter == 9:
                max_id = node.id
            record = self.log_record
            record['dbnode_id'] = node.id
            orm.Log(**record)

        order_by = [OrderSpecifier('dbnode_id', ASCENDING)]
        entries = orm.Log.objects.find(order_by=order_by)

        self.assertEqual(entries[0].dbnode_id, min_id)

        order_by = [OrderSpecifier('dbnode_id', DESCENDING)]
        entries = orm.Log.objects.find(order_by=order_by)

        self.assertEqual(entries[0].dbnode_id, max_id)

    def test_find_limit(self):
        """
        Test the limit option of log.find
        """
        node = orm.Data().store()
        limit = 2
        for _ in range(limit * 2):
            self.log_record['dbnode_id'] = node.id
            orm.Log(**self.log_record)

        entries = orm.Log.objects.find(limit=limit)
        self.assertEqual(len(entries), limit)

    def test_find_filter(self):
        """
        Test the filter option of log.find
        """
        node_id = None
        for counter in range(10):
            node = orm.Data().store()
            record = self.log_record
            record['dbnode_id'] = node.id
            orm.Log(**record)
            if counter == 5:
                node_id = node.id

        entries = orm.Log.objects.find(filters={'dbnode_id': node_id})
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].dbnode_id, node_id)

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

        logs = orm.Log.objects.find()

        self.assertEqual(len(logs), 0)

        # After storing the node, logs above log level should be stored
        node.store()
        node.logger.critical(message)
        logs = orm.Log.objects.find()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].message, message)

        # Launching a second log message ensuring that both messages are correctly stored
        message2 = message + " - Second message"
        node.logger.critical(message2)
        # logs = orm.Log.objects.find()

        order_by = [OrderSpecifier('time', ASCENDING)]
        logs = orm.Log.objects.find(order_by=order_by)

        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].message, message)
        self.assertEqual(logs[1].message, message2)
