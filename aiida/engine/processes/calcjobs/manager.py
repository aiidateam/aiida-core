# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module containing utilities and classes relating to job calculations running on systems that require transport."""
import contextlib
import logging
import time

from tornado import concurrent, gen

from aiida.common import lang

__all__ = ('JobsList', 'JobManager')


class JobsList:
    """Manager of calculation jobs submitted with a specific ``AuthInfo``, i.e. computer configured for a specific user.

    This container of active calculation jobs is used to update their status periodically in batches, ensuring that
    even when a lot of jobs are running, the scheduler update command is not triggered for each job individually.

    In addition, the :py:class:`~aiida.orm.computers.Computer` for which the :py:class:`~aiida.orm.authinfos.AuthInfo`
    is configured, can define a minimum polling interval. This class will guarantee that the time between update calls
    to the scheduler is larger or equal to that minimum interval.

    Note that since each instance operates on a specific authinfo, the guarantees of batching scheduler update calls
    and the limiting of number of calls per unit time, through the minimum polling interval, is only applicable for jobs
    launched with that particular authinfo. If multiple authinfo instances with the same computer, have active jobs
    these limitations are not respected between them, since there is no communication between ``JobsList`` instances.
    See the :py:class:`~aiida.engine.processes.calcjobs.manager.JobManager` for example usage.
    """

    def __init__(self, authinfo, transport_queue, last_updated=None):
        """Construct an instance for the given authinfo and transport queue.

        :param authinfo: The authinfo used to check the jobs list
        :type authinfo: :class:`aiida.orm.AuthInfo`
        :param transport_queue: A transport queue
        :type: :class:`aiida.engine.transports.TransportQueue`
        :param last_updated: initialize the last updated timestamp
        :type: float
        """
        lang.type_check(last_updated, float, allow_none=True)

        self._authinfo = authinfo
        self._transport_queue = transport_queue
        self._loop = transport_queue.loop()
        self._logger = logging.getLogger(__name__)

        self._jobs_cache = {}
        self._job_update_requests = {}  # Mapping: {job_id: Future}
        self._last_updated = last_updated
        self._update_handle = None

    @property
    def logger(self):
        """Return the logger configured for this instance.

        :return: the logger
        """
        return self._logger

    def get_minimum_update_interval(self):
        """Get the minimum interval that should be respected between updates of the list.

        :return: the minimum interval
        :rtype: float
        """
        return self._authinfo.computer.get_minimum_job_poll_interval()

    @property
    def last_updated(self):
        """Get the timestamp of when the list was last updated as produced by `time.time()`

        :return: The last update point
        :rtype: float
        """
        return self._last_updated

    @gen.coroutine
    def _get_jobs_from_scheduler(self):
        """Get the current jobs list from the scheduler.

        :return: a mapping of job ids to :py:class:`~aiida.schedulers.datastructures.JobInfo` instances
        :rtype: dict
        """
        with self._transport_queue.request_transport(self._authinfo) as request:
            self.logger.info('waiting for transport')
            transport = yield request

            scheduler = self._authinfo.computer.get_scheduler()
            scheduler.set_transport(transport)

            kwargs = {'as_dict': True}
            if scheduler.get_feature('can_query_by_user'):
                kwargs['user'] = '$USER'
            else:
                kwargs['jobs'] = self._get_jobs_with_scheduler()

            scheduler_response = scheduler.get_jobs(**kwargs)

            # Update the last update time and clear the jobs cache
            self._last_updated = time.time()
            jobs_cache = {}
            self.logger.info('AuthInfo<{}>: successfully retrieved status of active jobs'.format(self._authinfo.pk))

            for job_id, job_info in scheduler_response.items():
                jobs_cache[job_id] = job_info

            raise gen.Return(jobs_cache)

    @gen.coroutine
    def _update_job_info(self):
        """Update all of the job information objects.

        This will set the futures for all pending update requests where the corresponding job has a new status compared
        to the last update.
        """
        try:
            if not self._update_requests_outstanding():
                return

            # Update our cache of the job states
            self._jobs_cache = yield self._get_jobs_from_scheduler()
        except Exception as exception:
            # Set the exception on all the update futures
            for future in self._job_update_requests.values():
                if not future.done():
                    future.set_exception(exception)

            # Reset the `_update_handle` manually. Normally this is done in the `updating` coroutine, but since we
            # reraise this exception, that code path is never hit. If the next time a request comes in, the method
            # `_ensure_updating` will falsely conclude we are still updating, since the handle is not `None` and so it
            # will not schedule the next update, causing the job update futures to never be resolved.
            self._update_handle = None

            raise
        else:
            for job_id, future in self._job_update_requests.items():
                if not future.done():
                    future.set_result(self._jobs_cache.get(job_id, None))
        finally:
            self._job_update_requests = {}

    @contextlib.contextmanager
    def request_job_info_update(self, job_id):
        """Request job info about a job when the job next changes state.

        If the job is not found in the jobs list at the update, the future will resolve to `None`.

        :param job_id: job identifier
        :return: future that will resolve to a `JobInfo` object when the job changes state
        """
        # Get or create the future
        request = self._job_update_requests.setdefault(job_id, concurrent.Future())
        assert not request.done(), 'Expected pending job info future, found in done state.'

        try:
            self._ensure_updating()
            yield request
        finally:
            pass

    def _ensure_updating(self):
        """Ensure that we are updating the job list from the remote resource.

        This will automatically stop if there are no outstanding requests.
        """

        @gen.coroutine
        def updating():
            """Do the actual update, stop if not requests left."""
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
        """Return whether the states `old` and `new` are different.

        :type old: :class:`aiida.schedulers.JobInfo` or `None`
        :type new: :class:`aiida.schedulers.JobInfo` or `None`
        :rtype: bool
        """
        if old is None and new is None:
            return False

        if old is None or new is None:
            # One is None and the other isn't
            return True

        return old.job_state != new.job_state or old.job_substate != new.job_substate

    def _get_next_update_delay(self):
        """Calculate when we are next allowed to poll the scheduler.

        This delay is calculated as the minimum polling interval defined by the authentication info for this instance,
        minus time elapsed since the last update.

        :return: delay (in seconds) after which the scheduler may be polled again
        :rtype: float
        """
        if self.last_updated is None:
            # Never updated, so do it straight away
            return 0.

        # Make sure to actually 'get' the minimum interval here, in case the user changed since last time
        minimum_interval = self.get_minimum_update_interval()
        elapsed = time.time() - self.last_updated

        delay = max(minimum_interval - elapsed, 0.)

        return delay

    def _update_requests_outstanding(self):
        return any(not request.done() for request in self._job_update_requests.values())

    def _get_jobs_with_scheduler(self):
        """Get all the jobs that are currently with scheduler.

        :return: the list of jobs with the scheduler
        :rtype: list
        """
        return [str(job_id) for job_id, _ in self._job_update_requests.items()]


class JobManager:
    """A manager for :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` submitted to ``Computer`` instances.

    When a calculation job is submitted to a :py:class:`~aiida.orm.computers.Computer`, it actually uses a specific
    :py:class:`~aiida.orm.authinfos.AuthInfo`, which is a computer configured for a :py:class:`~aiida.orm.users.User`.
    The ``JobManager`` maintains a mapping of :py:class:`~aiida.engine.processes.calcjobs.manager.JobsList` instances
    for each authinfo that has active calculation jobs. These jobslist instances are then responsible for bundling
    scheduler updates for all the jobs they maintain (i.e. that all share the same authinfo) and update their status.

    As long as a :py:class:`~aiida.engine.runners.Runner` will create a single ``JobManager`` instance and use that for
    its lifetime, the guarantees made by the ``JobsList`` about respecting the minimum polling interval of the scheduler
    will be maintained. Note, however, that since each ``Runner`` will create its own job manager, these guarantees
    only hold per runner.
    """

    def __init__(self, transport_queue):
        self._transport_queue = transport_queue
        self._job_lists = {}

    def get_jobs_list(self, authinfo):
        """Get or create a new `JobLists` instance for the given authinfo.

        :param authinfo: the `AuthInfo`
        :return: a `JobsList` instance
        """
        if authinfo.id not in self._job_lists:
            self._job_lists[authinfo.id] = JobsList(authinfo, self._transport_queue)

        return self._job_lists[authinfo.id]

    @contextlib.contextmanager
    def request_job_info_update(self, authinfo, job_id):
        """Get a future that will resolve to information about a given job.

        This is a context manager so that if the user leaves the context the request is automatically cancelled.

        :return: A tuple containing the `JobInfo` object and detailed job info. Both can be None.
        :rtype: :class:`tornado.concurrent.Future`
        """
        with self.get_jobs_list(authinfo).request_job_info_update(job_id) as request:
            try:
                yield request
            finally:
                if not request.done():
                    request.cancel()
