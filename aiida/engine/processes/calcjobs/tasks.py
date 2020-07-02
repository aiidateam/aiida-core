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
import functools
import logging
import tempfile

import plumpy

from aiida.common.datastructures import CalcJobState
from aiida.common.exceptions import FeatureNotAvailable, TransportTaskException
from aiida.common.folders import SandboxFolder
from aiida.engine.daemon import execmanager
from aiida.engine.utils import exponential_backoff_retry, interruptable_task
from aiida.schedulers.datastructures import JobState

from ..process import ProcessState

UPLOAD_COMMAND = 'upload'
SUBMIT_COMMAND = 'submit'
UPDATE_COMMAND = 'update'
RETRIEVE_COMMAND = 'retrieve'
KILL_COMMAND = 'kill'

TRANSPORT_TASK_RETRY_INITIAL_INTERVAL = 20
TRANSPORT_TASK_MAXIMUM_ATTEMTPS = 5

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class PreSubmitException(Exception):
    """Raise in the `do_upload` coroutine when an exception is raised in `CalcJob.presubmit`."""


async def task_upload_job(process, transport_queue, cancellable):
    """Transport task that will attempt to upload the files of a job calculation to the remote.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    node = process.node

    if node.get_state() == CalcJobState.SUBMITTING:
        logger.warning('CalcJob<{}> already marked as SUBMITTING, skipping task_update_job'.format(node.pk))
        return

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)

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

            return

    try:
        logger.info('scheduled request to upload CalcJob<{}>'.format(node.pk))
        ignore_exceptions = (plumpy.CancelledError, PreSubmitException)
        result = await exponential_backoff_retry(
            do_upload, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=ignore_exceptions
        )
    except PreSubmitException:
        raise
    except plumpy.CancelledError:
        pass
    except Exception:
        logger.warning('uploading CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('upload_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('uploading CalcJob<{}> successful'.format(node.pk))
        node.set_state(CalcJobState.SUBMITTING)
        return result


async def task_submit_job(node, transport_queue, cancellable):
    """Transport task that will attempt to submit a job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.WITHSCHEDULER:
        assert node.get_job_id() is not None, 'job is WITHSCHEDULER, however, it does not have a job id'
        logger.warning('CalcJob<{}> already marked as WITHSCHEDULER, skipping task_submit_job'.format(node.pk))
        return node.get_job_id()

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)

    async def do_submit():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)
            return execmanager.submit_calculation(node, transport)

    try:
        logger.info('scheduled request to submit CalcJob<{}>'.format(node.pk))
        result = await exponential_backoff_retry(
            do_submit, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.Interruption
        )
    except plumpy.Interruption:
        pass
    except Exception:
        logger.warning('submitting CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('submit_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('submitting CalcJob<{}> successful'.format(node.pk))
        node.set_state(CalcJobState.WITHSCHEDULER)
        return result


async def task_update_job(node, job_manager, cancellable):
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
    if node.get_state() == CalcJobState.RETRIEVING:
        logger.warning('CalcJob<{}> already marked as RETRIEVING, skipping task_update_job'.format(node.pk))
        return True

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)
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
        logger.info('scheduled request to update CalcJob<{}>'.format(node.pk))
        job_done = await exponential_backoff_retry(
            do_update, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.Interruption
        )
    except plumpy.Interruption:
        raise
    except Exception:
        logger.warning('updating CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('update_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('updating CalcJob<{}> successful'.format(node.pk))
        if job_done:
            node.set_state(CalcJobState.RETRIEVING)

        return job_done


async def task_retrieve_job(node, transport_queue, retrieved_temporary_folder, cancellable):
    """Transport task that will attempt to retrieve all files of a completed job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.PARSING:
        logger.warning('CalcJob<{}> already marked as PARSING, skipping task_retrieve_job'.format(node.pk))
        return

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)

    async def do_retrieve():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)

            # Perform the job accounting and set it on the node if successful. If the scheduler does not implement this
            # still set the attribute but set it to `None`. This way we can distinguish calculation jobs for which the
            # accounting was called but could not be set.
            scheduler = node.computer.get_scheduler()
            scheduler.set_transport(transport)

            try:
                detailed_job_info = scheduler.get_detailed_job_info(node.get_job_id())
            except FeatureNotAvailable:
                logger.info('detailed job info not available for scheduler of CalcJob<{}>'.format(node.pk))
                node.set_detailed_job_info(None)
            else:
                node.set_detailed_job_info(detailed_job_info)

            return execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder)

    try:
        logger.info('scheduled request to retrieve CalcJob<{}>'.format(node.pk))
        result = await exponential_backoff_retry(
            do_retrieve, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.Interruption
        )
    except plumpy.Interruption:
        raise
    except Exception:
        logger.warning('retrieving CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('retrieve_calculation failed {} times consecutively'.format(max_attempts))
    else:
        node.set_state(CalcJobState.PARSING)
        logger.info('retrieving CalcJob<{}> successful'.format(node.pk))
        return result


async def task_kill_job(node, transport_queue, cancellable):
    """Transport task that will attempt to kill a job calculation.

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    if node.get_state() in [CalcJobState.UPLOADING, CalcJobState.SUBMITTING]:
        logger.warning('CalcJob<{}> killed, it was in the {} state'.format(node.pk, node.get_state()))
        return True

    authinfo = node.computer.get_authinfo(node.user)

    async def do_kill():
        with transport_queue.request_transport(authinfo) as request:
            transport = await cancellable.with_interrupt(request)
            return execmanager.kill_calculation(node, transport)

    try:
        logger.info('scheduled request to kill CalcJob<{}>'.format(node.pk))
        result = await exponential_backoff_retry(do_kill, initial_interval, max_attempts, logger=node.logger)
    except plumpy.Interruption:
        raise
    except Exception:
        logger.warning('killing CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('kill_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('killing CalcJob<{}> successful'.format(node.pk))
        node.set_scheduler_state(JobState.DONE)
        return result


class Waiting(plumpy.Waiting):
    """The waiting state for the `CalcJob` process."""

    def __init__(self, process, done_callback, msg=None, data=None):
        """
        :param :class:`~plumpy.base.state_machine.StateMachine` process: The process this state belongs to
        """
        super().__init__(process, done_callback, msg, data)
        self._task = None
        self._killing = None

    def load_instance_state(self, saved_state, load_context):
        super().load_instance_state(saved_state, load_context)
        self._task = None
        self._killing = None

    async def execute(self):  # pylint: disable=invalid-overridden-method
        """Override the execute coroutine of the base `Waiting` state."""
        # pylint: disable=too-many-branches
        node = self.process.node
        transport_queue = self.process.runner.transport
        command = self.data
        result = self

        process_status = 'Waiting for transport task: {}'.format(command)

        try:

            if command == UPLOAD_COMMAND:
                node.set_process_status(process_status)
                await self._launch_task(task_upload_job, self.process, transport_queue)
                result = self.submit()

            elif command == SUBMIT_COMMAND:
                node.set_process_status(process_status)
                await self._launch_task(task_submit_job, node, transport_queue)
                result = self.update()

            elif self.data == UPDATE_COMMAND:
                job_done = False

                while not job_done:
                    scheduler_state = node.get_scheduler_state()
                    scheduler_state_string = scheduler_state.name if scheduler_state else 'UNKNOWN'
                    process_status = 'Monitoring scheduler: job state {}'.format(scheduler_state_string)
                    node.set_process_status(process_status)
                    job_done = await self._launch_task(task_update_job, node, self.process.runner.job_manager)

                result = self.retrieve()

            elif self.data == RETRIEVE_COMMAND:
                node.set_process_status(process_status)
                # Create a temporary folder that has to be deleted by JobProcess.retrieved after successful parsing
                temp_folder = tempfile.mkdtemp()
                await self._launch_task(task_retrieve_job, node, transport_queue, temp_folder)
                result = self.parse(temp_folder)

            else:
                raise RuntimeError('Unknown waiting command')

        except TransportTaskException as exception:
            raise plumpy.PauseInterruption('Pausing after failed transport task: {}'.format(exception))
        except plumpy.KillInterruption:
            await self._launch_task(task_kill_job, node, transport_queue)
            self._killing.set_result(True)
            raise
        except (plumpy.Interruption, plumpy.CancelledError):
            node.set_process_status('Transport task {} was interrupted'.format(command))
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

    def upload(self):
        """Return the `Waiting` state that will `upload` the `CalcJob`."""
        msg = 'Waiting for calculation folder upload'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=UPLOAD_COMMAND)

    def submit(self):
        """Return the `Waiting` state that will `submit` the `CalcJob`."""
        msg = 'Waiting for scheduler submission'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=SUBMIT_COMMAND)

    def update(self):
        """Return the `Waiting` state that will `update` the `CalcJob`."""
        msg = 'Waiting for scheduler update'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=UPDATE_COMMAND)

    def retrieve(self):
        """Return the `Waiting` state that will `retrieve` the `CalcJob`."""
        msg = 'Waiting to retrieve'
        return self.create_state(ProcessState.WAITING, None, msg=msg, data=RETRIEVE_COMMAND)

    def parse(self, retrieved_temporary_folder):
        """Return the `Running` state that will parse the `CalcJob`.

        :param retrieved_temporary_folder: temporary folder used in retrieving that can be used during parsing.
        """
        return self.create_state(ProcessState.RUNNING, self.process.parse, retrieved_temporary_folder)

    def interrupt(self, reason):
        """Interrupt the `Waiting` state by calling interrupt on the transport task `InterruptableFuture`."""
        if self._task is not None:
            self._task.interrupt(reason)

        if isinstance(reason, plumpy.KillInterruption):
            if self._killing is None:
                self._killing = plumpy.Future()
            return self._killing
