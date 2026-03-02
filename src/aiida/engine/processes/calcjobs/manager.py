###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module containing utilities and classes relating to job calculations running on systems that require transport."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import logging
import time
from typing import TYPE_CHECKING, Dict, Hashable, Iterator, Optional, cast

from aiida.common import lang
from aiida.orm import AuthInfo

if TYPE_CHECKING:
    from aiida.engine.transports import TransportQueue
    from aiida.schedulers.datastructures import JobInfo

__all__ = ('JobManager', 'JobsList')


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

    def __init__(self, authinfo: AuthInfo, transport_queue: 'TransportQueue', last_updated: Optional[float] = None):
        """Construct an instance for the given authinfo and transport queue.

        :param authinfo: The authinfo used to check the jobs list
        :param transport_queue: A transport queue
        :param last_updated: initialize the last updated timestamp

        """
        lang.type_check(last_updated, float, allow_none=True)

        self._authinfo = authinfo
        self._transport_queue = transport_queue
        self._loop = transport_queue.loop
        self._logger = logging.getLogger(__name__)

        self._jobs_cache: Dict[str, 'JobInfo'] = {}
        self._job_update_requests: Dict[str, asyncio.Future] = {}  # Mapping: {job_id: Future}
        self._last_updated = last_updated
        self._update_handle: Optional[asyncio.TimerHandle] = None
        self._polling_jobs: frozenset[str] = frozenset()

    @property
    def logger(self) -> logging.Logger:
        """Return the logger configured for this instance.

        :return: the logger
        """
        return self._logger

    def get_minimum_update_interval(self) -> float:
        """Get the minimum interval that should be respected between updates of the list.

        :return: the minimum interval

        """
        return self._authinfo.computer.get_minimum_job_poll_interval()

    @property
    def last_updated(self) -> Optional[float]:
        """Get the timestamp of when the list was last updated as produced by `time.time()`

        :return: The last update point

        """
        return self._last_updated

    async def _get_jobs_from_scheduler(self) -> Dict[str, 'JobInfo']:
        """Get the current jobs list from the scheduler.

        :return: a mapping of job ids to :py:class:`~aiida.schedulers.datastructures.JobInfo` instances

        """
        async with self._transport_queue.request_transport(self._authinfo) as request:
            self.logger.info('waiting for transport')
            transport = await request

            scheduler = self._authinfo.computer.get_scheduler()
            scheduler.set_transport(transport)

            self._polling_jobs = frozenset([str(job_id) for job_id in self._job_update_requests.keys()])

            if scheduler.get_feature('can_query_by_user'):
                scheduler_response = scheduler.get_jobs(user='$USER', as_dict=True)
            else:
                scheduler_response = scheduler.get_jobs(jobs=list(self._polling_jobs), as_dict=True)

            # Update the last update time and clear the jobs cache
            self._last_updated = time.time()
            jobs_cache = {}
            self.logger.info(f'AuthInfo<{self._authinfo.pk}>: successfully retrieved status of active jobs')

            for job_id, job_info in scheduler_response.items():
                jobs_cache[job_id] = job_info

            return jobs_cache

    async def _update_job_info(self) -> None:
        """Update job information and resolve pending requests.

        This will set the futures for all pending update requests where the corresponding job has a new status compared
        to the last update.
        Note, _job_update_requests is dynamic, and might get new entries while polling from scheduler.
        Therefore we only update the jobs actually polled, and the new entries will be handled in the next update.
        """

        try:
            if not self._update_requests_outstanding():
                return

            # Update our cache of the job states
            self._jobs_cache = await self._get_jobs_from_scheduler()
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
            self._job_update_requests = {}

            raise
        else:
            for job_id in self._polling_jobs:
                future = self._job_update_requests.pop(job_id, None)  # type: ignore[arg-type]
                if future is None:
                    # This should not happen after fixing the mutation bug
                    # where schedulers could modify _polling_jobs (#7155, now
                    # immutable frozenset). If this warning fires, there may be
                    # a race condition or other issue where job_id was removed
                    # from _job_update_requests.
                    self.logger.warning(  # type: ignore[unreachable]
                        f'This should not happen: polled job_id {job_id} '
                        f'not in _job_update_requests {self._job_update_requests}'
                    )
                elif not future.done():
                    future.set_result(self._jobs_cache.get(job_id, None))

    @contextlib.contextmanager
    def request_job_info_update(self, authinfo: AuthInfo, job_id: Hashable) -> Iterator['asyncio.Future[JobInfo]']:
        """Request job info about a job when the job next changes state.

        If the job is not found in the jobs list at the update, the future will resolve to `None`.

        :param job_id: job identifier
        :return: future that will resolve to a `JobInfo` object when the job changes state
        """
        self._authinfo = authinfo
        # Get or create the future
        request = self._job_update_requests.setdefault(str(job_id), asyncio.Future())
        assert not request.done(), 'Expected pending job info future, found in done state.'

        try:
            self._ensure_updating()
            yield request
        finally:
            pass

    def _ensure_updating(self) -> None:
        """Ensure that we are updating the job list from the remote resource.

        This will automatically stop if there are no outstanding requests.
        """

        async def updating() -> None:
            """Do the actual update, stop if not requests left."""
            await self._update_job_info()
            # Any outstanding requests?
            if self._update_requests_outstanding():
                self._update_handle = self._loop.call_later(
                    self._get_next_update_delay(),
                    asyncio.ensure_future,
                    updating(),
                    context=contextvars.Context(),
                )
            else:
                self._update_handle = None

        # Check if we're already updating
        if self._update_handle is None:
            self._update_handle = self._loop.call_later(
                self._get_next_update_delay(),
                asyncio.ensure_future,
                updating(),
                context=contextvars.Context(),
            )

    @staticmethod
    def _has_job_state_changed(old: Optional['JobInfo'], new: Optional['JobInfo']) -> bool:
        """Return whether the states `old` and `new` are different."""
        if old is None and new is None:
            return False

        if old is None or new is None:
            # One is None and the other isn't
            return True

        return old.job_state != new.job_state or old.job_substate != new.job_substate

    def _get_next_update_delay(self) -> float:
        """Calculate when we are next allowed to poll the scheduler.

        This delay is calculated as the minimum polling interval defined by the authentication info for this instance,
        minus time elapsed since the last update.

        :return: delay (in seconds) after which the scheduler may be polled again

        """
        if self.last_updated is None:
            # Never updated, so do it straight away
            return 0.0

        # Make sure to actually 'get' the minimum interval here, in case the user changed since last time
        minimum_interval = self.get_minimum_update_interval()
        elapsed = time.time() - self.last_updated

        delay = max(minimum_interval - elapsed, 0.0)

        return delay

    def _update_requests_outstanding(self) -> bool:
        return any(not request.done() for request in self._job_update_requests.values())


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

    def __init__(self, transport_queue: 'TransportQueue') -> None:
        self._transport_queue = transport_queue
        self._job_lists: dict[int, JobsList] = {}

    def get_jobs_list(self, authinfo: AuthInfo) -> JobsList:
        """Get or create a new `JobLists` instance for the given authinfo.

        :param authinfo: the `AuthInfo`
        :return: a `JobsList` instance
        """
        # TODO: Mypy infers type of `authinfo.pk` as `int | None`
        # It's not clear if it can actually by None at runtime,
        # or is just a limitation of the current typing.
        # Instead of using `cast` Perhaps we should do:
        # assert authinfo.pk is not None
        pk = cast(int, authinfo.pk)
        if pk not in self._job_lists:
            self._job_lists[pk] = JobsList(authinfo, self._transport_queue)

        return self._job_lists[pk]

    @contextlib.contextmanager
    def request_job_info_update(self, authinfo: AuthInfo, job_id: Hashable) -> Iterator['asyncio.Future[JobInfo]']:
        """Get a future that will resolve to information about a given job.

        This is a context manager so that if the user leaves the context the request is automatically cancelled.

        """
        with self.get_jobs_list(authinfo).request_job_info_update(authinfo, job_id) as request:
            try:
                yield request
            finally:
                if not request.done():
                    request.cancel()
