# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module containing utilities and classes relating to job calculations running
on systems that require transport.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import contextlib
from functools import partial
import time

from six import iteritems, itervalues
from tornado import concurrent, gen

from aiida import schedulers
from aiida.common import exceptions
from ...utils import RefObjectStore

__all__ = ('JobsList', 'JobManager')


class JobsList(object):  # pylint: disable=useless-object-inheritance
    """
    A list of submitted jobs on a machine connected to by transport based on the
    authorisation information.
    """

    def __init__(self, authinfo, transport_queue):
        """
        :param authinfo: The authinfo used to check the jobs list
        :type authinfo: :class:`aiida.orm.AuthInfo`
        :param transport_queue: A transport queue
        :type: :class:`aiida.engine.transports.TransportQueue`
        """
        self._authinfo = authinfo
        self._transport_queue = transport_queue
        self._loop = transport_queue.loop()

        self._jobs_cache = {}
        self._last_updated = None  # type: float
        self._job_update_requests = {}  # Mapping: {job_id: Future}
        self._update_handle = None

    def get_minimum_update_interval(self):
        """
        Get the minimum interval that can be expected between updates of the list
        :return: The minimum interval
        :rtype: float
        """
        return self._authinfo.computer.get_minimum_job_poll_interval()

    def get_last_updated(self):
        """
        Get the timestamp of when the list was last updated as produced by `time.time()`

        :return: The last update point
        :rtype: float
        """
        return self._last_updated

    @gen.coroutine
    def _get_jobs_from_scheduler(self):
        """
        Get the current jobs list from the scheduler

        :return: A dictionary of {job_id: job info}
        :rtype: dict
        """
        with self._transport_queue.request_transport(self._authinfo) as request:
            transport = yield request

            scheduler = self._authinfo.computer.get_scheduler()
            scheduler.set_transport(transport)

            kwargs = {'as_dict': True}
            if scheduler.get_feature('can_query_by_user'):
                kwargs['user'] = "$USER"
            else:
                kwargs['jobs'] = self._get_jobs_with_scheduler()

            scheduler_response = scheduler.get_jobs(**kwargs)
            jobs_cache = {}

            for job_id, job_info in iteritems(scheduler_response):
                # If the job is done then get detailed job information
                detailed_job_info = None
                if job_info.job_state == schedulers.JobState.DONE:
                    try:
                        detailed_job_info = scheduler.get_detailed_jobinfo(job_id)
                    except exceptions.FeatureNotAvailable:
                        detailed_job_info = 'This scheduler does not implement get_detailed_jobinfo'

                job_info.detailedJobinfo = detailed_job_info
                jobs_cache[job_id] = job_info

            raise gen.Return(jobs_cache)

    @gen.coroutine
    def _update_job_info(self):
        """
        Update all of the job information objects for a given authinfo, that is to say for
        all the jobs on a particular machine for a particular user.

        This will set the futures for all pending update requests where the corresponding job
        has a new status compared to the last update.
        """
        try:
            if not self._update_requests_outstanding():
                return

            # Update our cache of the job states
            self._jobs_cache = yield self._get_jobs_from_scheduler()
        except Exception as exception:
            # Set the exception on all the update futures
            for future in itervalues(self._job_update_requests):
                if not future.done():
                    future.set_exception(exception)
            raise
        else:
            for job_id, future in iteritems(self._job_update_requests):
                if not future.done():
                    future.set_result(self._jobs_cache.get(job_id, None))
        finally:
            self._job_update_requests = {}

    @contextlib.contextmanager
    def request_job_info_update(self, job_id):
        """
        Request job info about a job when it next changes it's job state.  If the job is not
        found in the jobs list at the update the future will resolve to None.

        :param job_id: The job identifier
        :return: A future that will resolve to a JobInfo object when the job changes state
        """
        # Get or create the future
        request = self._job_update_requests.setdefault(job_id, concurrent.Future())
        assert not request.done(), "The future should be no be in the done state"

        try:
            self._ensure_updating()
            yield request
        finally:
            pass

    def _ensure_updating(self):
        """
        Ensure that we are updating the job list from the remote resource.
        This will automatically stop if there are no outstanding requests.
        """

        @gen.coroutine
        def updating():
            """ Do the actual update, stop if not requests left """
            yield self._update_job_info()
            # Any outstanding requests?
            if self._update_requests_outstanding():
                self._update_handle = self._loop.call_later(self._get_next_update_delay(), updating)
            else:
                self._update_handle = None

        # Check if we're already updating
        if self._update_handle is None:
            self._update_handle = self._loop.call_later(self._get_next_update_delay(), updating)

    @staticmethod
    def _has_job_state_changed(old, new):
        """
        :type old: :class:`aiida.schedulers.JobInfo`
        :type new: :class:`aiida.schedulers.JobInfo`
        :rtype: bool
        """
        if old is None and new is None:
            return False

        if old is None or new is None:
            # One is None and the other isn't
            return True

        return old.job_state != new.job_state or old.job_substate != new.job_substate

    def _get_next_update_delay(self):
        """
        Calculate when we are next allowed to call the scheduler get jobs command
        based on when we last called it, how long has elapsed and the minimum given
        update interval.

        :return: The delay (in seconds) for when it's safe to call the get jobs command
        :rtype: float
        """
        if self._last_updated is None:
            # Never updated, so do it straight away
            return 0.

        # Make sure to actually 'get' it here, so that if the user changed it
        # between times we use the current value
        minimum_interval = self._authinfo.computer.get_minimum_job_poll_interval()
        elapsed = time.time() - self._last_updated

        return max(minimum_interval - elapsed, 0.)

    def _update_requests_outstanding(self):
        return any(not request.done() for request in itervalues(self._job_update_requests))

    def _get_jobs_with_scheduler(self):
        """
        Get all the jobs that are currently with scheduler for this authinfo

        :return: the list of jobs with the scheduler
        :rtype: list
        """
        return [str(job_id) for job_id, _ in self._job_update_requests.items()]


class JobManager(object):  # pylint: disable=useless-object-inheritance
    """
    A manager for jobs on a (usually) remote resource such as a supercomputer
    """

    def __init__(self, transport_queue):
        self._transport_queue = transport_queue
        self._job_lists = RefObjectStore()

    @contextlib.contextmanager
    def request_job_info_update(self, authinfo, job_id):
        """
        Get a future that will resolve to information about a given job.  This is a context
        manager so that if the user leaves the context the request is automatically cancelled.

        :return: A tuple containing the JobInfo object and detailed job info.  Both can be None.
        :rtype: :class:`tornado.concurrent.Future`
        """
        # Define a way to create a JobsList if needed
        create = partial(JobsList, authinfo, self._transport_queue)

        with self._job_lists.get(authinfo.id, create) as job_list:
            with job_list.request_job_info_update(job_id) as request:
                try:
                    yield request
                finally:
                    if not request.done():
                        request.cancel()
