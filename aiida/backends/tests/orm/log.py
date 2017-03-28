# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import logging
import unittest
from aiida.utils.timezone import now
from aiida import LOG_LEVEL_REPORT
from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING
from aiida.orm.backend import construct
from aiida.orm.calculation import Calculation
from aiida.backends.testbase import AiidaTestCase


class TestBackendLog(AiidaTestCase):
    def setUp(self):
        super(TestBackendLog, self).setUp()
        self._backend = construct()
        self._record = {
            'time': now(),
            'loggername': 'loggername',
            'levelname': logging.getLevelName(LOG_LEVEL_REPORT),
            'objname': 'objname',
            'objpk': 0,
            'message': 'This is a template record message',
            'metadata': {'content': 'test'},
        }

    def tearDown(self):
        """
        Delete all the created log entries
        """
        super(TestBackendLog, self).tearDown()
        self._backend.log.delete_many({})

    def test_create_backend(self):
        """
        Test creating the backend specific backend instance
        """
        backend = construct()

    def test_delete_many(self):
        """
        Test deleting all log entries
        Bit superfluous, given that other tests most likely would fail
        anyway if this method does not work properly
        """
        count = 10
        for _ in range(count):
            self._backend.log.create_entry(**self._record)

        self.assertEquals(len(self._backend.log.find()), count)
        self._backend.log.delete_many({})
        self.assertEquals(len(self._backend.log.find()), 0)

    def test_create_log_message(self):
        """
        Test the manual creation of a log entry 
        """
        record = self._record
        entry = self._backend.log.create_entry(
            record['time'],
            record['loggername'],
            record['levelname'],
            record['objname'],
            record['objpk'],
            record['message'],
            record['metadata']
        )

        self.assertEquals(entry.time, record['time'])
        self.assertEquals(entry.loggername, record['loggername'])
        self.assertEquals(entry.levelname, record['levelname'])
        self.assertEquals(entry.objname, record['objname'])
        self.assertEquals(entry.objpk, record['objpk'])
        self.assertEquals(entry.message, record['message'])
        self.assertEquals(entry.metadata, record['metadata'])

    def test_find_orderby(self):
        """
        Test the order_by option of log.find
        """
        for pk in range(10):
            record = self._record
            record['objpk'] = pk
            self._backend.log.create_entry(**record)

        order_by = [OrderSpecifier('objpk', ASCENDING)]
        entries = self._backend.log.find(order_by=order_by)

        self.assertEquals(entries[0].objpk, 0)

        order_by = [OrderSpecifier('objpk', DESCENDING)]
        entries = self._backend.log.find(order_by=order_by)

        self.assertEquals(entries[0].objpk, 9)

    def test_find_limit(self):
        """
        Test the limit option of log.find
        """
        limit = 2
        for _ in range(limit * 2):
            self._backend.log.create_entry(**self._record)

        entries = self._backend.log.find(limit=limit)
        self.assertEquals(len(entries), limit)

    def test_find_filter(self):
        """
        Test the filter option of log.find
        """
        target_pk = 5
        for pk in range(10):
            record = self._record
            record['objpk'] = pk
            self._backend.log.create_entry(**record)

        entries = self._backend.log.find(filter_by={'objpk': target_pk})
        self.assertEquals(len(entries), 1)
        self.assertEquals(entries[0].objpk, target_pk)

    def test_db_log_handler(self):
        """
        Verify that the db log handler is attached correctly
        by firing a log message through the regular logging module
        attached to a calculation node
        """
        message = 'Testing logging of critical failure'
        calc = Calculation()

        # Make sure that global logging is not accidentally disabled
        logging.disable(logging.NOTSET)

        # # Temporarily disable logging to the stream handler (i.e. screen)
        # # because otherwise fix_calc_states will print warnings
        # handler = next((h for h in logging.getLogger('aiida').handlers if
        #                 isinstance(h, logging.StreamHandler)), None)

        # # try:
        # if handler:
        #     original_level = handler.level
        #     handler.setLevel(logging.CRITICAL + 1)

        # Firing a log for an unstored should not end up in the database
        calc.logger.critical(message)

        logs = self._backend.log.find()

        self.assertEquals(len(logs), 0)

        # After storing the node, logs above log level should be stored
        calc.store()
        calc.logger.critical(message)
        logs = self._backend.log.find()

        self.assertEquals(len(logs), 1)
        self.assertEquals(logs[0].message, message)

        # finally:
        #     if handler:
        #         handler.setLevel(original_level)
