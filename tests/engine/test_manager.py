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

    def test_prevent_racing_condition(self):
        """Test that the `JobsList` prevents racing condition when updating job info.

        This test simulates a race condition where:
        1. Job 'job1' requests an update
        2. During the scheduler query, a new job 'job2' also requests an update
        3. JobList must only update about 'job1'
        4. 'job2' future should be kept pending for the next update cycle
        """
        from unittest.mock import patch

        from aiida.schedulers.datastructures import JobInfo, JobState

        jobs_list = self.jobs_list

        mock_job_info = JobInfo()
        mock_job_info.job_id = 'job1'
        mock_job_info.job_state = JobState.RUNNING

        def mock_get_jobs(**kwargs):
            # Simulate the race: job2 is added to _job_update_requests while we're querying the scheduler
            jobs_list._job_update_requests.setdefault('job2', asyncio.Future())

            # Return only job1 (scheduler was queried with only job1)
            return {'job1': mock_job_info}

        # Request update for job1
        future1 = jobs_list._job_update_requests.setdefault('job1', asyncio.Future())

        # Patch the scheduler's get_jobs
        scheduler = self.auth_info.computer.get_scheduler()
        with patch.object(scheduler.__class__, 'get_jobs', side_effect=mock_get_jobs):
            self.loop.run_until_complete(jobs_list._update_job_info())

        # Verify job1 was resolved correctly
        assert future1.done(), 'job1 future should be resolved'
        assert future1.result() == mock_job_info, 'job1 should have the correct JobInfo'

        # Verify job2 was NOT resolved and it has remained in _job_update_requests for the next cycle
        assert 'job2' in jobs_list._job_update_requests, 'job2 should still be in update requests'
        future2 = jobs_list._job_update_requests['job2']
        assert not future2.done(), 'job2 future should NOT be resolved yet (prevented racing bug)'
        assert len(jobs_list._job_update_requests) == 1, 'Only job2 should remain in update requests'
