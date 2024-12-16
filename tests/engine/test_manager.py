###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the classes in `aiida.engine.processes.calcjobs.manager`."""

import asyncio
import time

import pytest

from aiida.engine.processes.calcjobs.manager import JobManager, JobsList
from aiida.engine.transports import TransportQueue
from aiida.orm import User


class TestJobManager:
    """Test the `aiida.engine.processes.calcjobs.manager.JobManager` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.loop = asyncio.get_event_loop()
        self.transport_queue = TransportQueue(self.loop)
        self.user = User.collection.get_default()
        self.computer = aiida_localhost
        self.auth_info = self.computer.get_authinfo(self.user)
        self.manager = JobManager(self.transport_queue)

    def test_get_jobs_list(self):
        """Test the `JobManager.get_jobs_list` method."""
        jobs_list = self.manager.get_jobs_list(self.auth_info)
        assert isinstance(jobs_list, JobsList)

        # Calling the method again, should return the exact same instance of `JobsList`
        assert self.manager.get_jobs_list(self.auth_info) == jobs_list

    def test_request_job_info_update(self):
        """Test the `JobManager.request_job_info_update` method."""
        with self.manager.request_job_info_update(self.auth_info, job_id=1) as request:
            assert isinstance(request, asyncio.Future)


class TestJobsList:
    """Test the `aiida.engine.processes.calcjobs.manager.JobsList` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        self.loop = asyncio.get_event_loop()
        self.transport_queue = TransportQueue(self.loop)
        self.user = User.collection.get_default()
        self.computer = aiida_localhost
        self.auth_info = self.computer.get_authinfo(self.user)
        self.jobs_list = JobsList(self.auth_info, self.transport_queue)

    def test_get_minimum_update_interval(self):
        """Test the `JobsList.get_minimum_update_interval` method."""
        minimum_poll_interval = self.auth_info.computer.get_minimum_job_poll_interval()
        assert self.jobs_list.get_minimum_update_interval() == minimum_poll_interval

    def test_last_updated(self):
        """Test the `JobsList.last_updated` method."""
        jobs_list = JobsList(self.auth_info, self.transport_queue)
        assert jobs_list.last_updated is None

        last_updated = time.time()
        jobs_list = JobsList(self.auth_info, self.transport_queue, last_updated=last_updated)
        assert jobs_list.last_updated == last_updated
