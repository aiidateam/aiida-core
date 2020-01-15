# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the classes in `aiida.engine.processes.calcjobs.manager`."""

import time

import tornado

from aiida.orm import AuthInfo, User
from aiida.backends.testbase import AiidaTestCase
from aiida.engine.processes.calcjobs.manager import JobManager, JobsList
from aiida.engine.transports import TransportQueue


class TestJobManager(AiidaTestCase):
    """Test the `aiida.engine.processes.calcjobs.manager.JobManager` class."""

    def setUp(self):
        super().setUp()
        self.loop = tornado.ioloop.IOLoop()
        self.transport_queue = TransportQueue(self.loop)
        self.user = User.objects.get_default()
        self.auth_info = AuthInfo(self.computer, self.user).store()
        self.manager = JobManager(self.transport_queue)

    def tearDown(self):
        super().tearDown()
        AuthInfo.objects.delete(self.auth_info.pk)

    def test_get_jobs_list(self):
        """Test the `JobManager.get_jobs_list` method."""
        jobs_list = self.manager.get_jobs_list(self.auth_info)
        self.assertIsInstance(jobs_list, JobsList)

        # Calling the method again, should return the exact same instance of `JobsList`
        self.assertEqual(self.manager.get_jobs_list(self.auth_info), jobs_list)

    def test_request_job_info_update(self):
        """Test the `JobManager.request_job_info_update` method."""
        with self.manager.request_job_info_update(self.auth_info, job_id=1) as request:
            self.assertIsInstance(request, tornado.concurrent.Future)


class TestJobsList(AiidaTestCase):
    """Test the `aiida.engine.processes.calcjobs.manager.JobsList` class."""

    def setUp(self):
        super().setUp()
        self.loop = tornado.ioloop.IOLoop()
        self.transport_queue = TransportQueue(self.loop)
        self.user = User.objects.get_default()
        self.auth_info = AuthInfo(self.computer, self.user).store()
        self.jobs_list = JobsList(self.auth_info, self.transport_queue)

    def tearDown(self):
        super().tearDown()
        AuthInfo.objects.delete(self.auth_info.pk)

    def test_get_minimum_update_interval(self):
        """Test the `JobsList.get_minimum_update_interval` method."""
        minimum_poll_interval = self.auth_info.computer.get_minimum_job_poll_interval()
        self.assertEqual(self.jobs_list.get_minimum_update_interval(), minimum_poll_interval)

    def test_last_updated(self):
        """Test the `JobsList.last_updated` method."""
        jobs_list = JobsList(self.auth_info, self.transport_queue)
        self.assertEqual(jobs_list.last_updated, None)

        last_updated = time.time()
        jobs_list = JobsList(self.auth_info, self.transport_queue, last_updated=last_updated)
        self.assertEqual(jobs_list.last_updated, last_updated)
