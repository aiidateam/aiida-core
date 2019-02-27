# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import functools
import logging
import sys
import tempfile

import six
from tornado.gen import coroutine, Return

import plumpy

from aiida.common.datastructures import CalcJobState
from aiida.common.exceptions import TransportTaskException
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

logger = logging.getLogger(__name__)


@coroutine
def task_upload_job(node, transport_queue, calc_info, script_filename, cancellable):
    """
    Transport task that will attempt to upload the files of a job calculation to the remote

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param calc_info: the calculation info datastructure returned by `CalcJobNode._presubmit`
    :param script_filename: the job launch script returned by `CalcJobNode._presubmit`
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.SUBMITTING:
        logger.warning('calculation<{}> already marked as SUBMITTING, skipping task_update_job'.format(node.pk))
        raise Return(True)

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)

    @coroutine
    def do_upload():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield cancellable.with_interrupt(request)

            logger.info('uploading calculation<{}>'.format(node.pk))
            raise Return(execmanager.upload_calculation(node, transport, calc_info, script_filename))

    try:
        result = yield exponential_backoff_retry(
            do_upload, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.CancelledError)
    except plumpy.CancelledError:
        pass
    except Exception:
        logger.warning('uploading calculation<{}> failed'.format(node.pk))
        raise TransportTaskException('upload_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('uploading calculation<{}> successful'.format(node.pk))
        node.set_state(CalcJobState.SUBMITTING)
        raise Return(result)


@coroutine
def task_submit_job(node, transport_queue, calc_info, script_filename, cancellable):
    """
    Transport task that will attempt to submit a job calculation

    The task will first request a transport from the queue. Once the transport is yielded, the relevant execmanager
    function is called, wrapped in the exponential_backoff_retry coroutine, which, in case of a caught exception, will
    retry after an interval that increases exponentially with the number of retries, for a maximum number of retries.
    If all retries fail, the task will raise a TransportTaskException

    :param node: the node that represents the job calculation
    :param transport_queue: the TransportQueue from which to request a Transport
    :param calc_info: the calculation info datastructure returned by `CalcJobNode._presubmit`
    :param script_filename: the job launch script returned by `CalcJobNode._presubmit`
    :param cancellable: the cancelled flag that will be queried to determine whether the task was cancelled
    :type cancellable: :class:`aiida.engine.utils.InterruptableFuture`
    :raises: Return if the tasks was successfully completed
    :raises: TransportTaskException if after the maximum number of retries the transport task still excepted
    """
    if node.get_state() == CalcJobState.WITHSCHEDULER:
        assert node.get_job_id() is not None, 'job is WITHSCHEDULER, however, it does not have a job id'
        logger.warning('CalcJob<{}> already marked as WITHSCHEDULER, skipping task_submit_job'.format(node.pk))
        raise Return(node.get_job_id())

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)

    @coroutine
    def do_submit():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield cancellable.with_interrupt(request)

            logger.info('submitting CalcJob<{}>'.format(node.pk))
            raise Return(execmanager.submit_calculation(node, transport, calc_info, script_filename))

    try:
        result = yield exponential_backoff_retry(
            do_submit, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.Interruption)
    except plumpy.Interruption:
        pass
    except Exception:
        logger.warning('submitting CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('submit_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('submitting CalcJob<{}> successful'.format(node.pk))
        node.set_state(CalcJobState.WITHSCHEDULER)
        raise Return(result)


@coroutine
def task_update_job(node, job_manager, cancellable):
    """
    Transport task that will attempt to update the scheduler status of the job calculation

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
    :raises: Return containing True if the tasks was successfully completed, False otherwise
    """
    if node.get_state() == CalcJobState.RETRIEVING:
        logger.warning('CalcJob<{}> already marked as RETRIEVING, skipping task_update_job'.format(node.pk))
        raise Return(True)

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)
    job_id = node.get_job_id()

    @coroutine
    def do_update():
        # Get the update request
        with job_manager.request_job_info_update(authinfo, job_id) as update_request:
            job_info = yield cancellable.with_interrupt(update_request)

        if job_info is None:
            # If the job is computed or not found assume it's done
            node.set_scheduler_state(JobState.DONE)
            job_done = True
        else:
            node.set_last_job_info(job_info)
            node.set_scheduler_state(job_info.job_state)
            job_done = job_info.job_state == JobState.DONE

        raise Return(job_done)

    try:
        job_done = yield exponential_backoff_retry(
            do_update, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.Interruption)
    except plumpy.Interruption:
        raise
    except Exception:
        logger.warning('updating CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('update_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('updating CalcJob<{}> successful'.format(node.pk))
        if job_done:
            node.set_state(CalcJobState.RETRIEVING)

        raise Return(job_done)


@coroutine
def task_retrieve_job(node, transport_queue, retrieved_temporary_folder, cancellable):
    """
    Transport task that will attempt to retrieve all files of a completed job calculation

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
    if node.get_state() == CalcJobState.PARSING:
        logger.warning('CalcJob<{}> already marked as PARSING, skipping task_retrieve_job'.format(node.pk))
        raise Return(True)

    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    authinfo = node.computer.get_authinfo(node.user)

    @coroutine
    def do_retrieve():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield cancellable.with_interrupt(request)

            logger.info('retrieving CalcJob<{}>'.format(node.pk))
            raise Return(execmanager.retrieve_calculation(node, transport, retrieved_temporary_folder))

    try:
        result = yield exponential_backoff_retry(
            do_retrieve, initial_interval, max_attempts, logger=node.logger, ignore_exceptions=plumpy.Interruption)
    except plumpy.Interruption:
        raise
    except Exception:
        logger.warning('retrieving CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('retrieve_calculation failed {} times consecutively'.format(max_attempts))
    else:
        node.set_state(CalcJobState.PARSING)
        logger.info('retrieving CalcJob<{}> successful'.format(node.pk))
        raise Return(result)


@coroutine
def task_kill_job(node, transport_queue, cancellable):
    """
    Transport task that will attempt to kill a job calculation

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
    initial_interval = TRANSPORT_TASK_RETRY_INITIAL_INTERVAL
    max_attempts = TRANSPORT_TASK_MAXIMUM_ATTEMTPS

    if node.get_state() in [CalcJobState.UPLOADING, CalcJobState.SUBMITTING]:
        logger.warning('CalcJob<{}> killed, it was in the {} state'.format(node.pk, node.get_state()))
        raise Return(True)

    authinfo = node.computer.get_authinfo(node.user)

    @coroutine
    def do_kill():
        with transport_queue.request_transport(authinfo) as request:
            transport = yield cancellable.with_interrupt(request)
            logger.info('killing CalcJob<{}>'.format(node.pk))
            raise Return(execmanager.kill_calculation(node, transport))

    try:
        result = yield exponential_backoff_retry(do_kill, initial_interval, max_attempts, logger=node.logger)
    except plumpy.Interruption:
        raise
    except Exception:
        logger.warning('killing CalcJob<{}> failed'.format(node.pk))
        raise TransportTaskException('kill_calculation failed {} times consecutively'.format(max_attempts))
    else:
        logger.info('killing CalcJob<{}> successful'.format(node.pk))
        node.set_scheduler_state(JobState.DONE)
        raise Return(result)


class Waiting(plumpy.Waiting):
    """The waiting state for the `CalcJob` process."""

    def __init__(self, process, done_callback, msg=None, data=None):
        super(Waiting, self).__init__(process, done_callback, msg, data)
        self._task = None
        self._killing = None

    def load_instance_state(self, saved_state, load_context):
        super(Waiting, self).load_instance_state(saved_state, load_context)
        self._task = None
        self._killing = None

    @coroutine
    def execute(self):

        node = self.process.node
        transport_queue = self.process.runner.transport

        if isinstance(self.data, tuple):
            command = self.data[0]
            args = self.data[1:]
        else:
            command = self.data

        node.set_process_status('Waiting for transport task: {}'.format(command))

        try:

            if command == UPLOAD_COMMAND:
                calc_info, script_filename = yield self._launch_task(task_upload_job, node, transport_queue, *args)
                raise Return(self.submit(calc_info, script_filename))

            elif command == SUBMIT_COMMAND:
                yield self._launch_task(task_submit_job, node, transport_queue, *args)
                raise Return(self.update())

            elif self.data == UPDATE_COMMAND:
                job_done = False

                while not job_done:
                    job_done = yield self._launch_task(task_update_job, node, self.process.runner.job_manager)

                raise Return(self.retrieve())

            elif self.data == RETRIEVE_COMMAND:
                # Create a temporary folder that has to be deleted by JobProcess.retrieved after successful parsing
                temp_folder = tempfile.mkdtemp()
                yield self._launch_task(task_retrieve_job, node, transport_queue, temp_folder)
                raise Return(self.parse(temp_folder))

            else:
                raise RuntimeError('Unknown waiting command')

        except TransportTaskException as exception:
            raise plumpy.PauseInterruption('Pausing after failed transport task: {}'.format(exception))
        except plumpy.KillInterruption:
            exc_info = sys.exc_info()
            yield self._launch_task(task_kill_job, node, transport_queue)
            self._killing.set_result(True)
            six.reraise(*exc_info)
        except Return:
            node.set_process_status(None)
            raise
        except (plumpy.Interruption, plumpy.CancelledError):
            node.set_process_status('Transport task {} was interrupted'.format(command))
            raise
        finally:
            # If we were trying to kill but we didn't deal with it, make sure it's set here
            if self._killing and not self._killing.done():
                self._killing.set_result(False)

    @coroutine
    def _launch_task(self, coro, *args, **kwargs):
        task_fn = functools.partial(coro, *args, **kwargs)
        try:
            self._task = interruptable_task(task_fn)
            result = yield self._task
            raise Return(result)
        finally:
            self._task = None

    def upload(self, calc_info, script_filename):
        """Return the `Waiting` state that will `upload` the `CalcJob`."""
        return self.create_state(
            ProcessState.WAITING,
            None,
            msg='Waiting for calculation folder upload',
            data=(UPLOAD_COMMAND, calc_info, script_filename))

    def submit(self, calc_info, script_filename):
        """Return the `Waiting` state that will `submit` the `CalcJob`."""
        return self.create_state(
            ProcessState.WAITING,
            None,
            msg='Waiting for scheduler submission',
            data=(SUBMIT_COMMAND, calc_info, script_filename))

    def update(self):
        """Return the `Waiting` state that will `update` the `CalcJob`."""
        return self.create_state(
            ProcessState.WAITING, None, msg='Waiting for scheduler update', data=UPDATE_COMMAND)

    def retrieve(self):
        """Return the `Waiting` state that will `retrieve` the `CalcJob`."""
        return self.create_state(ProcessState.WAITING, None, msg='Waiting to retrieve', data=RETRIEVE_COMMAND)

    def parse(self, retrieved_temporary_folder):
        """Return the `Running` state that will `parse` the `CalcJob`.

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
