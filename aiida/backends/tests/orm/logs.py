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
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import logging

from six.moves import range

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.common.log import LOG_LEVEL_REPORT
from aiida import orm
from aiida.orm.node.process.calculation import CalculationNode
from aiida.common.timezone import now


class TestBackendLog(AiidaTestCase):
    """Test the Log entity"""

    def setUp(self):
        super(TestBackendLog, self).setUp()
        self.record = {
            'time': now(),
            'loggername': 'loggername',
            'levelname': logging.getLevelName(LOG_LEVEL_REPORT),
            'objname': 'objname',
            'objpk': 0,
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
        entry = orm.Log(**self.record)

        self.assertEqual(entry.time, self.record['time'])
        self.assertEqual(entry.loggername, self.record['loggername'])
        self.assertEqual(entry.levelname, self.record['levelname'])
        self.assertEqual(entry.objname, self.record['objname'])
        self.assertEqual(entry.objpk, self.record['objpk'])
        self.assertEqual(entry.message, self.record['message'])
        self.assertEqual(entry.metadata, self.record['metadata'])

    def test_log_delete_single(self):
        """Test that a single log entry can be deleted through the collection."""
        entry = orm.Log(**self.record)

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
        for _ in range(count):
            orm.Log(**self.record)

        self.assertEqual(len(orm.Log.objects.all()), count)
        orm.Log.objects.delete_many({})
        self.assertEqual(len(orm.Log.objects.all()), 0)

    def test_objects_find(self):
        """Put logs in and find them"""
        for pk in range(10):
            record = self.record
            record['objpk'] = pk
            orm.Log(**record)

        entries = orm.Log.objects.all()
        self.assertEqual(10, len(entries))
        self.assertIsInstance(entries[0], orm.Log)

    def test_find_orderby(self):
        """
        Test the order_by option of log.find
        """
        from aiida.orm.logs import OrderSpecifier, ASCENDING, DESCENDING

        for pk in range(10):
            record = self.record
            record['objpk'] = pk
            orm.Log(**record)

        order_by = [OrderSpecifier('objpk', ASCENDING)]
        entries = orm.Log.objects.find(order_by=order_by)

        self.assertEqual(entries[0].objpk, 0)

        order_by = [OrderSpecifier('objpk', DESCENDING)]
        entries = orm.Log.objects.find(order_by=order_by)

        self.assertEqual(entries[0].objpk, 9)

    def test_find_limit(self):
        """
        Test the limit option of log.find
        """
        limit = 2
        for _ in range(limit * 2):
            orm.Log(**self.record)

        entries = orm.Log.objects.find(limit=limit)
        self.assertEqual(len(entries), limit)

    def test_find_filter(self):
        """
        Test the filter option of log.find
        """
        target_pk = 5
        for pk in range(10):
            record = self.record
            record['objpk'] = pk
            orm.Log(**record)

        entries = orm.Log.objects.find(filters={'objpk': target_pk})
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].objpk, target_pk)

    def test_db_log_handler(self):
        """
        Verify that the db log handler is attached correctly
        by firing a log message through the regular logging module
        attached to a calculation node
        """
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
