###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Transport tasks for calculation jobs."""

from __future__ import annotations

import asyncio
import functools
import logging
import tempfile
from typing import TYPE_CHECKING, Any, Callable, Optional

import plumpy
import plumpy.futures
import plumpy.persistence
import plumpy.process_states

from aiida.common.datastructures import CalcJobState
from aiida.common.exceptions import FeatureNotAvailable, TransportTaskException
from aiida.common.folders import SandboxFolder
from aiida.engine import utils
from aiida.engine.daemon import execmanager
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.transports import TransportQueue
from aiida.engine.utils import InterruptableFuture, interruptable_task
from aiida.manage.configuration import get_config_option
from aiida.orm import load_node
from aiida.orm.nodes.process.calculation.calcjob import CalcJobNode
from aiida.schedulers.datastructures import JobState

from ..process import ProcessState
from .monitors import CalcJobMonitorAction, CalcJobMonitorResult, CalcJobMonitors

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

logger = logging.getLogger(__name__)


class PreSubmitException(Exception):  # noqa: N818
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

    if node.get_state() == CalcJobState.UNSTASHING:
        logger.warning(f'CalcJob<{node.pk}> already marked as UNSTASHING, skipping task_update_job')
        return

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)
    filepath_sandbox = get_config_option('storage.sandbox') or None

    authinfo = node.get_authinfo()

    async def do_upload():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)

            with SandboxFolder(filepath_sandbox) as folder:
                # Any exception thrown in `presubmit` call is not transient so we circumvent the exponential backoff
                try:
                    calc_info = process.presubmit(folder)
                except Exception as exception:
                    raise PreSubmitException('exception occurred in presubmit call') from exception
                else:
                    remote_folder = await execmanager.upload_calculation(node, transport, calc_info, folder)
                    if remote_folder is not None:
                        process.out('remote_folder', remote_folder)
                    skip_submit = calc_info.skip_submit or False

            return skip_submit

    try:
        logger.info(f'scheduled request to upload CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, PreSubmitException, plumpy.process_states.Interruption)
        skip_submit = await utils.exponential_backoff_retry(
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
        node.set_state(CalcJobState.UNSTASHING)
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
        result = await utils.exponential_backoff_retry(
            do_submit, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):
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
    :param job_manager: The job manager
    :param cancellable: A cancel flag
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
        job_done = await utils.exponential_backoff_retry(
            do_update, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):
        raise
    except Exception as exception:
        logger.warning(f'updating CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'update_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'updating CalcJob<{node.pk}> successful')
        if job_done:
            node.set_state(CalcJobState.STASHING)

        return job_done


async def task_monitor_job(
    node: CalcJobNode, transport_queue: TransportQueue, cancellable: InterruptableFuture, monitors: CalcJobMonitors
):
    """Transport task that will monitor the job calculation if any monitors have been defined.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: A cancel flag
    :param monitors: An instance of ``CalcJobMonitors`` holding the collection of monitors to process.
    :return: True if the tasks was successfully completed, False otherwise
    """
    state = node.get_state()

    if state in [CalcJobState.RETRIEVING, CalcJobState.STASHING]:
        logger.warning(f'CalcJob<{node.pk}> already marked as `{state}`, skipping task_monitor_job')
        return None

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)
    authinfo = node.get_authinfo()

    async def do_monitor():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)
            return monitors.process(node, transport)

    try:
        logger.info(f'scheduled request to monitor CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, plumpy.process_states.Interruption)
        monitor_result = await utils.exponential_backoff_retry(
            do_monitor, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):
        raise
    except Exception as exception:
        logger.warning(f'monitoring CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'monitor_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'monitoring CalcJob<{node.pk}> successful')
        return monitor_result


async def task_retrieve_job(
    process: 'CalcJob',
    transport_queue: TransportQueue,
    retrieved_temporary_folder: str,
    cancellable: InterruptableFuture,
):
    """Transport task that will attempt to retrieve all files of a completed job calculation.
    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException
    :param process: the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param retrieved_temporary_folder: the absolute path to a directory to store files
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    node = process.node
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

            job_id = node.get_job_id()
            if job_id is None:
                logger.warning(f'there is no job id for CalcJobNoe<{node.pk}>: skipping `get_detailed_job_info`')
                retrieved = await execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder)
            else:
                try:
                    detailed_job_info = scheduler.get_detailed_job_info(job_id)
                except FeatureNotAvailable:
                    logger.info(f'detailed job info not available for scheduler of CalcJob<{node.pk}>')
                    node.set_detailed_job_info(None)
                else:
                    node.set_detailed_job_info(detailed_job_info)

                retrieved = await execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder)

            if retrieved is not None:
                process.out(node.link_label_retrieved, retrieved)
            return retrieved

    try:
        logger.info(f'scheduled request to retrieve CalcJob<{node.pk}>')
        ignore_exceptions = (plumpy.futures.CancelledError, plumpy.process_states.Interruption)
        result = await utils.exponential_backoff_retry(
            do_retrieve, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except (plumpy.futures.CancelledError, plumpy.process_states.Interruption):
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
            return await execmanager.stash_calculation(node, transport)

    try:
        await utils.exponential_backoff_retry(
            do_stash,
            initial_interval,
            max_attempts,
            logger=node.logger,
            ignore_exceptions=plumpy.process_states.Interruption,
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


async def task_unstash_job(node: CalcJobNode, transport_queue: TransportQueue, cancellable: InterruptableFuture):
    if node.get_state() == CalcJobState.SUBMITTING:
        logger.warning(f'CalcJob<{node.pk}> already marked as SUBMITTING, skipping task_update_job')
        return

    initial_interval = get_config_option(RETRY_INTERVAL_OPTION)
    max_attempts = get_config_option(MAX_ATTEMPTS_OPTION)

    authinfo = node.get_authinfo()

    async def do_unstash():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)

            logger.info(f'unstashing calculation<{node.pk}>')
            return await execmanager.unstash_calculation(node, transport)

    try:
        await utils.exponential_backoff_retry(
            do_unstash,
            initial_interval,
            max_attempts,
            logger=node.logger,
            ignore_exceptions=plumpy.process_states.Interruption,
        )
    except plumpy.process_states.Interruption:
        raise
    except Exception as exception:
        logger.warning(f'unstashing calculation<{node.pk}> failed')
        raise TransportTaskException(f'unstash_calculation failed {max_attempts} times consecutively') from exception
    else:
        node.set_state(CalcJobState.SUBMITTING)
        logger.info(f'unstashing calculation<{node.pk}> successful')
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
        result = await utils.exponential_backoff_retry(do_kill, initial_interval, max_attempts, logger=node.logger)
    except plumpy.process_states.Interruption:
        raise
    except Exception as exception:
        logger.warning(f'killing CalcJob<{node.pk}> failed')
        raise TransportTaskException(f'kill_calculation failed {max_attempts} times consecutively') from exception
    else:
        logger.info(f'killing CalcJob<{node.pk}> successful')
        node.set_scheduler_state(JobState.DONE)
        return result


@plumpy.persistence.auto_persist('msg', 'data', '_command', '_monitor_result')
class Waiting(plumpy.process_states.Waiting):
    """The waiting state for the `CalcJob` process."""

    def __init__(
        self,
        process: 'CalcJob',
        done_callback: Optional[Callable[..., Any]],
        msg: Optional[str] = None,
        data: Optional[Any] = None,
    ):
        """:param process: The process this state belongs to"""
        super().__init__(process, done_callback, msg, data)
        self._task: InterruptableFuture | None = None
        self._killing: plumpy.futures.Future | None = None
        self._command: str | None = None
        self._monitor_result: CalcJobMonitorResult | None = None
        self._monitors: CalcJobMonitors | None = None

        if isinstance(self.data, dict):
            self._command = self.data['command']
            self._monitor_result = self.data.get('monitor_result', None)
        else:
            self._command = self.data

    @property
    def monitors(self) -> CalcJobMonitors | None:
        """Return the collection of monitors if specified in the inputs.

        :return: Instance of ``CalcJobMonitors`` containing monitors if specified in the process' input.
        """
        if not hasattr(self, '_monitors'):
            self._monitors = None

        if self._monitors is None and 'monitors' in self.process.node.inputs:
            self._monitors = CalcJobMonitors(self.process.node.inputs.monitors)

        return self._monitors

    @property
    def process(self) -> 'CalcJob':
        """:return: The process"""
        return self.state_machine  # type: ignore[return-value]

    def load_instance_state(self, saved_state, load_context):
        super().load_instance_state(saved_state, load_context)
        self._task = None
        self._killing = None

    async def execute(self) -> plumpy.process_states.State | plumpy.base.state_machine.State:  # type: ignore[override]
        """Override the execute coroutine of the base `Waiting` state.
        Using the plumpy state machine the waiting state is repeatedly re-entered with different commands.
        The waiting state is not always the same instance, it could be re-instantiated when re-entering this method,
        therefor any newly created attribute in each command block
        (e.g. `SUBMIT_COMMAND`, `UPLOAD_COMMAND`, etc.) will be lost, and is not usable in other blocks.
        The advantage of this design, is that the sequence is interruptable,
        meaning, the process can potentially come back and start from where it left off.

        The overall sequence is as follows:
        in case `skip_submit` is True:

        UPLOAD -> STASH -> RETRIEVE
        |   ^     |   ^     |   ^
        v   |     v   |     v   |
        .. ..     .. ..     .. ..

        otherwise:

        UPLOAD -> SUBMIT -> UPDATE -> STASH -> RETRIEVE
        |   ^     |   ^     |   ^     |   ^     |   ^
        v   |     v   |     v   |     v   |     v   |
        .. ..     .. ..     .. ..     .. ..     .. ..
        """

        node = self.process.node
        transport_queue = self.process.runner.transport
        result: plumpy.process_states.State = self

        process_status = f'Waiting for transport task: {self._command}'
        node.set_process_status(process_status)

        if self.process.awaitables:
            if any(
                load_node(awaitable).process_state
                not in [
                    ProcessState.FINISHED,
                    ProcessState.KILLED,
                    ProcessState.EXCEPTED,
                ]
                for awaitable in self.process.awaitables
            ):
                logger.info(f'CalcJob<{node.pk}> waiting for awaitables to finish')
                await asyncio.sleep(5)
        try:
            if self._command == UPLOAD_COMMAND:
                skip_submit = await self._launch_task(task_upload_job, self.process, transport_queue)
                # Note: we do both `task_upload_job` and `task_unstash_job` at the same time,
                # only because `skip_submit` is not easily accesible outside this `if` block!
                if node.get_option('unstash') and node.process_type == 'aiida.calculations:core.unstash':
                    await self._launch_task(task_unstash_job, node, transport_queue)
                if skip_submit:
                    result = self.stash(monitor_result=self._monitor_result)
                else:
                    result = self.submit()

            elif self._command == SUBMIT_COMMAND:
                task_result = await self._launch_task(task_submit_job, node, transport_queue)

                if isinstance(task_result, ExitCode):
                    # The scheduler plugin returned an exit code from ``Scheduler.submit_job`` indicating the
                    # job submission failed due to a non-transient problem and the job should be terminated.
                    return self.create_state(ProcessState.RUNNING, self.process.terminate, task_result)

                result = self.update()

            elif self._command == UPDATE_COMMAND:
                job_done = False

                while not job_done:
                    scheduler_state = node.get_scheduler_state()
                    scheduler_state_string = scheduler_state.name if scheduler_state else 'UNKNOWN'
                    process_status = f'Monitoring scheduler: job state {scheduler_state_string}'
                    node.set_process_status(process_status)
                    job_done = await self._launch_task(task_update_job, node, self.process.runner.job_manager)
                    monitor_result = await self._monitor_job(node, transport_queue, self.monitors)

                    if monitor_result and monitor_result.action is CalcJobMonitorAction.KILL:
                        await self._kill_job(node, transport_queue)
                        job_done = True

                    if monitor_result and not monitor_result.retrieve:
                        exit_code = self.process.exit_codes.STOPPED_BY_MONITOR.format(message=monitor_result.message)
                        return self.create_state(ProcessState.RUNNING, self.process.terminate, exit_code)

                result = self.stash(monitor_result=monitor_result)

            elif self._command == STASH_COMMAND:
                if node.get_option('stash'):
                    await self._launch_task(task_stash_job, node, transport_queue)
                result = self.retrieve(monitor_result=self._monitor_result)

            elif self._command == RETRIEVE_COMMAND:
                temp_folder = tempfile.mkdtemp()
                await self._launch_task(task_retrieve_job, self.process, transport_queue, temp_folder)

                if not self._monitor_result:
                    result = self.parse(temp_folder)

                elif self._monitor_result.parse is False:
                    exit_code = self.process.exit_codes.STOPPED_BY_MONITOR.format(message=self._monitor_result.message)
                    result = self.create_state(  # type: ignore[assignment]
                        ProcessState.RUNNING, self.process.terminate, exit_code
                    )

                elif self._monitor_result.override_exit_code:
                    exit_code = self.process.exit_codes.STOPPED_BY_MONITOR.format(message=self._monitor_result.message)
                    result = self.parse(temp_folder, exit_code)
                else:
                    result = self.parse(temp_folder)

            else:
                raise RuntimeError('Unknown waiting command')

        except TransportTaskException as exception:
            raise plumpy.process_states.PauseInterruption(f'Pausing after failed transport task: {exception}')
        except plumpy.process_states.KillInterruption as exception:
            node.set_process_status(str(exception))
            return self.retrieve(monitor_result=self._monitor_result)
        except (plumpy.futures.CancelledError, asyncio.CancelledError):
            node.set_process_status(f'Transport task {self._command} was cancelled')
            raise
        except plumpy.process_states.Interruption:
            node.set_process_status(f'Transport task {self._command} was interrupted')
            raise
        else:
            node.set_process_status(None)
            return result
        finally:
            # If we were trying to kill but we didn't deal with it, make sure it's set here
            if self._killing and not self._killing.done():
                self._killing.set_result(False)

    async def _monitor_job(self, node, transport_queue, monitors) -> CalcJobMonitorResult | None:
        """Process job monitors if any were specified as inputs."""
        if monitors is None:
            return None

        if self._monitor_result and self._monitor_result.action == CalcJobMonitorAction.DISABLE_ALL:
            return None

        monitor_result = await self._launch_task(task_monitor_job, node, transport_queue, monitors=monitors)

        if monitor_result and monitor_result.outputs:
            for label, output in monitor_result.outputs.items():
                self.process.out(label, output)
            self.process.update_outputs()

        if monitor_result and monitor_result.action == CalcJobMonitorAction.DISABLE_SELF:
            monitors.monitors[monitor_result.key].disabled = True

        if monitor_result is not None:
            self._monitor_result = monitor_result

        return monitor_result

    async def _kill_job(self, node, transport_queue) -> None:
        """Kill the job."""
        await self._launch_task(task_kill_job, node, transport_queue)
        if self._killing is not None:
            self._killing.set_result(True)
        else:
            logger.info(f'killed CalcJob<{node.pk}> but async future was None')

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
        return self.create_state(  # type: ignore[return-value]
            ProcessState.WAITING, None, msg=msg, data={'command': UPLOAD_COMMAND}
        )

    def submit(self) -> 'Waiting':
        """Return the `Waiting` state that will `submit` the `CalcJob`."""
        msg = 'Waiting for scheduler submission'
        return self.create_state(  # type: ignore[return-value]
            ProcessState.WAITING, None, msg=msg, data={'command': SUBMIT_COMMAND}
        )

    def update(self) -> 'Waiting':
        """Return the `Waiting` state that will `update` the `CalcJob`."""
        msg = 'Waiting for scheduler update'
        return self.create_state(  # type: ignore[return-value]
            ProcessState.WAITING, None, msg=msg, data={'command': UPDATE_COMMAND}
        )

    def stash(self, monitor_result: CalcJobMonitorResult | None = None) -> 'Waiting':
        """Return the `Waiting` state that will `stash` the `CalcJob`."""
        msg = 'Waiting to stash'
        return self.create_state(  # type: ignore[return-value]
            ProcessState.WAITING, None, msg=msg, data={'command': STASH_COMMAND, 'monitor_result': monitor_result}
        )

    # def unstash(self, monitor_result: CalcJobMonitorResult | None = None) -> 'Waiting':
    #     """Return the `Waiting` state that will `unstash` the `CalcJob`."""
    #     msg = 'Waiting to unstash'
    #     return self.create_state(  # type: ignore[return-value]
    #         ProcessState.WAITING, None, msg=msg, data={'command': UNSTASH_COMMAND, 'monitor_result': monitor_result}
    #     )

    def retrieve(self, monitor_result: CalcJobMonitorResult | None = None) -> 'Waiting':
        """Return the `Waiting` state that will `retrieve` the `CalcJob`."""
        msg = 'Waiting to retrieve'
        return self.create_state(  # type: ignore[return-value]
            ProcessState.WAITING, None, msg=msg, data={'command': RETRIEVE_COMMAND, 'monitor_result': monitor_result}
        )

    def parse(
        self, retrieved_temporary_folder: str, exit_code: ExitCode | None = None
    ) -> plumpy.process_states.Running:
        """Return the `Running` state that will parse the `CalcJob`.

        :param retrieved_temporary_folder: temporary folder used in retrieving that can be used during parsing.
        """
        return self.create_state(  # type: ignore[return-value]
            ProcessState.RUNNING, self.process.parse, retrieved_temporary_folder, exit_code
        )

    def interrupt(self, reason: Any) -> Optional[plumpy.futures.Future]:  # type: ignore[override]
        """Interrupt the `Waiting` state by calling interrupt on the transport task `InterruptableFuture`."""
        if self._task is not None:
            self._task.interrupt(reason)

        if isinstance(reason, plumpy.process_states.KillInterruption):
            if self._killing is None:
                self._killing = plumpy.futures.Future()
            return self._killing

        return None
