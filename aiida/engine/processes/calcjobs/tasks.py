# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Transport tasks for calculation jobs."""
import asyncio
import functools
import logging
import tempfile
from typing import Any, Callable, Optional, TYPE_CHECKING

import plumpy
import plumpy.process_states
import plumpy.futures

from aiida.common.datastructures import CalcJobState
from aiida.common.exceptions import FeatureNotAvailable, TransportTaskException
from aiida.common.folders import SandboxFolder
from aiida.engine.daemon import execmanager
from aiida.engine.transports import TransportQueue
from aiida.engine.utils import exponential_backoff_retry, interruptable_task, InterruptableFuture
from aiida.orm.nodes.process.calculation.calcjob import CalcJobNode
from aiida.schedulers.datastructures import JobState
from aiida.manage.configuration import get_config_option

from ..process import ProcessState

if TYPE_CHECKING:
    from .calcjob import CalcJob

UPLOAD_COMMAND = 'upload'
SUBMIT_COMMAND = 'submit'
UPDATE_COMMAND = 'update'
RETRIEVE_COMMAND = 'retrieve'
STASH_COMMAND = 'stash'
KILL_COMMAND = 'kill'

RETRY_INTERVAL_OPTION = 'transport.task_retry_initial_interval'
MAX_ATTEMPTS_OPTION = 'transport.task_maximum_attempts'

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class PreSubmitException(Exception):
    """Raise in the `do_upload` coroutine when an exception is raised in `CalcJob.presubmit`."""


async def task_upload_job(process: 'CalcJob', transport_queue: TransportQueue, cancellable: InterruptableFuture):
    """Transport task that will attempt to upload the files of a job calculation to the remote.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param process: the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled

    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    node = process.node

    if node.get_state() == CalcJobState.SUBMITTING:
        logger.warning(f'CalcJob<{node.pk}> already marked as SUBMITTING, skipping task_update_job')
        return

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    authinfo = node.get_authinfo()

    async def do_upload():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)

            with SandboxFolder() as folder:
                # Any exception thrown in `presubmit` call is not transient so we circumvent the exponential backoff
                try:
                    calc_info = process.presubmit(folder)
                except Exception as exception:  # pylint: disable=broad-except
                    raise PreSubmitException('exception occurred in presubmit call') from exception
                else:
                    execmanager.upload_calculation(node, transport, calc_info, folder)
                    skip_submit = calc_info.skip_submit or False

            return skip_submit

    try:
        logger.info(f'scheduled request to upload CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, PreSubmitException, plumpy.process_states.Interruption)
        skip_submit = await exponential_backoff_retry(
            do_upload, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except PreSubmitException:
        raise
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):
        raise
    except Exception as exception:
        logger.warning(f'uploading CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'upload_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'uploading CalcJob<{node.pk}> successful')
        node.set_state(CalcJobState.SUBMITTING)
        return skip_submit


async def task_submit_job(node: CalcJobNode, transport_queue: TransportQueue, cancellable: InterruptableFuture):
    """Transport task that will attempt to submit a job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled

    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.WITHSCHEDULER:
        assert node.get_job_id() is not None, 'job is WITHSCHEDULER, however, it does not have a job id'
        logger.warning(f'CalcJob<{node.pk}> already marked as WITHSCHEDULER, skipping task_submit_job')
        return node.get_job_id()

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    authinfo = node.get_authinfo()

    async def do_submit():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)
            return execmanager.submit_calculation(node, transport)

    try:
        logger.info(f'scheduled request to submit CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, plumpy.process_states.Interruption)
        result = await exponential_backoff_retry(
            do_submit, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):  # pylint: disable=try-except-raise
        raise
    except Exception as exception:
        logger.warning(f'submitting CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'submit_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'submitting CalcJob<{node.pk}> successful')
        node.set_state(CalcJobState.WITHSCHEDULER)
        return result


async def task_update_job(node: CalcJobNode, job_manager, cancellable: InterruptableFuture):
    """Transport task that will attempt to update the scheduler status of the job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :type node: :class:`aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`
    :param job_manager: The job manager
    :type job_manager: :class:`aiida.engine.processes.calcjobs.manager.JobManager`
    :param cancellable: A cancel flag
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :return: True if the tasks was successfully completed, False otherwise
    """
    state = node.get_state()

    if state in [CalcJobState.RETRIEVING, CalcJobState.STASHING]:
        logger.warning(f'CalcJob<{node.pk}> already marked as `{state}`, skipping task_update_job')
        return True

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    authinfo = node.get_authinfo()
    job_id = node.get_job_id()

    async def do_update():
        # Get the update request
        with job_manager.request_job_info_update(authinfo, job_id) as update_request:
            job_info = await cancellable.with_interrupt(update_request)

        if job_info is None:
            # If the job is computed or not found assume it's done
            node.set_scheduler_state(JobState.DONE)
            job_done = True
        else:
            node.set_last_job_info(job_info)
            node.set_scheduler_state(job_info.job_state)
            job_done = job_info.job_state == JobState.DONE

        return job_done

    try:
        logger.info(f'scheduled request to update CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, plumpy.process_states.Interruption)
        job_done = await exponential_backoff_retry(
            do_update, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):  # pylint: disable=try-except-raise
        raise
    except Exception as exception:
        logger.warning(f'updating CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'update_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'updating CalcJob<{node.pk}> successful')
        if job_done:
            node.set_state(CalcJobState.STASHING)

        return job_done


async def task_retrieve_job(
    node: CalcJobNode, transport_queue: TransportQueue, retrieved_temporary_folder: str,
    cancellable: InterruptableFuture
):
    """Transport task that will attempt to retrieve all files of a completed job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param retrieved_temporary_folder: the absolute path to a directory to store files
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled

    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.PARSING:
        logger.warning(f'CalcJob<{node.pk}> already marked as PARSING, skipping task_retrieve_job')
        return

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    authinfo = node.get_authinfo()

    async def do_retrieve():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)

            # Perform the job accounting and set it on the node if successful. If the scheduler does not implement this
            # still set the attribute but set it to `None`. This way we can distinguish calculation jobs for which the
            # accounting was called but could not be set.
            scheduler = node.computer.get_scheduler()  # type: ignore[union-attr]
            scheduler.set_transport(transport)

            if node.get_job_id() is None:
                logger.warning(f'there is no job id for CalcJobNoe<{node.pk}>: skipping `get_detailed_job_info`')
                return execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder)

            try:
                detailed_job_info = scheduler.get_detailed_job_info(node.get_job_id())
            except FeatureNotAvailable:
                logger.info(f'detailed job info not available for scheduler of CalcJob<{node.pk}>')
                node.set_detailed_job_info(None)
            else:
                node.set_detailed_job_info(detailed_job_info)

            return execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder)

    try:
        logger.info(f'scheduled request to retrieve CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, plumpy.process_states.Interruption)
        result = await exponential_backoff_retry(
            do_retrieve, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):  # pylint: disable=try-except-raise
        raise
    except Exception as exception:
        logger.warning(f'retrieving CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'retrieve_calculation failed {max_attempts} times consecutively') from exception
    else:
        node.set_state(CalcJobState.PARSING)
        logger.info(f'retrieving CalcJob<{node.pk}> successful')
        return result


async def task_stash_job(node: CalcJobNode, transport_queue: TransportQueue, cancellable: InterruptableFuture):
    """Transport task that will optionally stash files of a completed job calculation on the remote.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.RETRIEVING:
        logger.warning(f'calculation<{node.pk}> already marked as RETRIEVING, skipping task_stash_job')
        return

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    authinfo = node.get_authinfo()

    async def do_stash():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)

            logger.info(f'stashing calculation<{node.pk}>')
            return execmanager.stash_calculation(node, transport)

    try:
        await exponential_backoff_retry(
            do_stash,
            initial_interval,
            max_attempts,
            logger=node.logger,
            ignore_exceptions=plumpy.process_states.Interruption
        )
    except plumpy.process_states.Interruption:
        raise
    except Exception as exception:
        logger.warning(f'stashing calculation<{node.pk}> failed')
        raise TransportTaskException(f'stash_calculation failed {max_attempts} times consecutively') from exception
    else:
        node.set_state(CalcJobState.RETRIEVING)
        logger.info(f'stashing calculation<{node.pk}> successful')
        return


async def task_kill_job(node: CalcJobNode, transport_queue: TransportQueue, cancellable: InterruptableFuture):
    """Transport task that will attempt to kill a job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled

    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    if node.get_state() in [CalcJobState.UPLOADING, CalcJobState.SUBMITTING]:
        logger.warning(f'CalcJob<{node.pk}> killed, it was in the {node.get_state()} state')
        return True

    authinfo = node.get_authinfo()

    async def do_kill():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)
            return execmanager.kill_calculation(node, transport)

    try:
        logger.info(f'scheduled request to kill CalcJob<{node.pk}>')
        result = await exponential_backoff_retry(do_kill, initial_interval, max_attempts, logger=node.logger)
    except plumpy.process_states.Interruption:
        raise
    except Exception as exception:
        logger.warning(f'killing CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'kill_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'killing CalcJob<{node.pk}> successful')
        node.set_scheduler_state(JobState.DONE)
        return result


class Waiting(plumpy.process_states.Waiting):
    """The waiting state for the `CalcJob` process."""

    def __init__(
        self,
        process: 'CalcJob',
        done_callback: Optional[Callable[..., Any]],
        msg: Optional[str] = None,
        data: Optional[Any] = None
    ):
        """
        :param process: The process this state belongs to
        """
        super().__init__(process, done_callback, msg, data)
        self._task: Optional[InterruptableFuture] = None
        self._killing: Optional[plumpy.futures.Future] = None

    @property
    def process(self) -> 'CalcJob':
        """
        :return: The process
        """
        return self.state_machine  # type: ignore[return-value]

    def load_instance_state(self, saved_state, load_context):
        super().load_instance_state(saved_state, load_context)
        self._task = None
        self._killing = None

    async def execute(self) -> plumpy.process_states.State:  # type: ignore[override] # pylint: disable=invalid-overridden-method
        """Override the execute coroutine of the base `Waiting` state."""
        # pylint: disable=too-many-branches,too-many-statements
        node = self.process.node
        transport_queue = self.process.runner.transport
        result: plumpy.process_states.State = self
        command = self.data

        process_status = f'Waiting for transport task: {command}'

        try:

            if command == UPLOAD_COMMAND:
                node.set_process_status(process_status)
                skip_submit = await self._launch_task(task_upload_job, self.process, transport_queue)
                if skip_submit:
                    result = self.retrieve()
                else:
                    result = self.submit()

            elif command == SUBMIT_COMMAND:
                node.set_process_status(process_status)
                await self._launch_task(task_submit_job, node, transport_queue)
                result = self.update()

            elif command == UPDATE_COMMAND:
                job_done = False

                while not job_done:
                    scheduler_state = node.get_scheduler_state()
                    scheduler_state_string = scheduler_state.name if scheduler_state else 'UNKNOWN'
                    process_status = f'Monitoring scheduler: job state {scheduler_state_string}'
                    node.set_process_status(process_status)
                    job_done = await self._launch_task(task_update_job, node, self.process.runner.job_manager)

                if node.get_option('stash') is not None:
                    result = self.stash()
                else:
                    result = self.retrieve()

            elif command == STASH_COMMAND:
                node.set_process_status(process_status)
                await self._launch_task(task_stash_job, node, transport_queue)
                result = self.retrieve()

            elif command == RETRIEVE_COMMAND:
                node.set_process_status(process_status)
                temp_folder = tempfile.mkdtemp()
                await self._launch_task(task_retrieve_job, node, transport_queue, temp_folder)
                result = self.parse(temp_folder)

            else:
                raise RuntimeError('Unknown waiting command')

        except TransportTaskException as exception:
            raise plumpy.process_states.PauseInterruption(f'Pausing after failed transport task: {exception}')
        except plumpy.process_states.KillInterruption:
            await self._launch_task(task_kill_job, node, transport_queue)
            if self._killing is not None:
                self._killing.set_result(True)
            else:
                logger.warning(f'killed CalcJob<{node.pk}> but async future was None')
            raise
        except (plumpy.futures.CancelledError, asyncio.CancelledError):
            node.set_process_status(f'Transport task {command} was cancelled')
            raise
        except plumpy.process_states.Interruption:
            node.set_process_status(f'Transport task {command} was interrupted')
            raise
        else:
            node.set_process_status(None)
            return result
        finally:
            # If we were trying to kill but we didn't deal with it, make sure it's set here
            if self._killing and not self._killing.done():
                self._killing.set_result(False)

    async def _launch_task(self, coro, *args, **kwargs):
        """Launch a coroutine as a task, making sure to make it interruptable."""
        task_fn = functools.partial(coro, *args, **kwargs)
        try:
            self._task = interruptable_task(task_fn)
            result = await self._task
            return result
        finally:
            self._task = None

    def upload(self) -> 'Waiting':
        """Return the `Waiting` state that will `upload` the `CalcJob`."""
        msg = 'Waiting for calculation folder upload'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=UPLOAD_COMMAND)  # type: ignore[return-value]

    def submit(self) -> 'Waiting':
        """Return the `Waiting` state that will `submit` the `CalcJob`."""
        msg = 'Waiting for scheduler submission'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=SUBMIT_COMMAND)  # type: ignore[return-value]

    def update(self) -> 'Waiting':
        """Return the `Waiting` state that will `update` the `CalcJob`."""
        msg = 'Waiting for scheduler update'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=UPDATE_COMMAND)  # type: ignore[return-value]

    def retrieve(self) -> 'Waiting':
        """Return the `Waiting` state that will `retrieve` the `CalcJob`."""
        msg = 'Waiting to retrieve'
        return self.create_state(
            ProcessState.WAITING, None, msg=msg, data=RETRIEVE_COMMAND
        )  # type: ignore[return-value]

    def stash(self):
        """Return the `Waiting` state that will `stash` the `CalcJob`."""
        msg = 'Waiting to stash'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=STASH_COMMAND)

    def parse(self, retrieved_temporary_folder: str) -> plumpy.process_states.Running:
        """Return the `Running` state that will parse the `CalcJob`.

        :param retrieved_temporary_folder: temporary folder used in retrieving that can be used during parsing.
        """
        return self.create_state(
            ProcessState.RUNNING, self.process.parse, retrieved_temporary_folder
        )  # type: ignore[return-value]

    def interrupt(self, reason: Any) -> Optional[plumpy.futures.Future]:  # type: ignore[override]
        """Interrupt the `Waiting` state by calling interrupt on the transport task `InterruptableFuture`."""
        if self._task is not None:
            self._task.interrupt(reason)

        if isinstance(reason, plumpy.process_states.KillInterruption):
            if self._killing is None:
                self._killing = plumpy.futures.Future()
            return self._killing

        return None
