# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Runners that can run and submit processes."""
from __future__ import absolute_import
from collections import namedtuple
from contextlib import contextmanager
import logging
import tornado.ioloop

import plumpy

from aiida.orm import load_node, load_workflow
from . import futures
from . import persistence
from . import rmq
from . import transports
from . import utils

__all__ = ['Runner', 'DaemonRunner', 'new_runner', 'set_runner', 'get_runner']

ResultAndNode = namedtuple('ResultAndNode', ['result', 'node'])
ResultAndPid = namedtuple('ResultAndPid', ['result', 'pid'])

RUNNER = None


def new_runner(**kwargs):
    """
    Create a default runner optionally passing keyword arguments

    :param kwargs: arguments to be passed to Runner constructor
    :return: a new runner instance
    """
    if 'rmq_config' not in kwargs:
        kwargs['rmq_config'] = rmq.get_rmq_config()

    return Runner(**kwargs)


def get_runner():
    """
    Get the global runner instance

    :returns: the global runner
    """
    global RUNNER
    if RUNNER is None or RUNNER.is_closed():
        RUNNER = new_runner()
    return RUNNER


def set_runner(runner):
    """
    Set the global runner instance

    :param runner: the runner instance to set as the global runner
    """
    global RUNNER
    RUNNER = runner


class Runner(object):
    """Class that can launch processes by running in the current interpreter or by submitting them to the daemon."""

    _persister = None
    _rmq_connector = None
    _communicator = None
    _closed = False

    # pylint: disable=too-many-arguments
    def __init__(self,
                 rmq_config=None,
                 poll_interval=0.,
                 loop=None,
                 rmq_submit=False,
                 enable_persistence=True,
                 persister=None):
        self._loop = loop if loop is not None else tornado.ioloop.IOLoop()
        self._poll_interval = poll_interval
        self._rmq_submit = rmq_submit
        self._transport = transports.TransportQueue(self._loop)

        if enable_persistence:
            self._persister = persister if persister is not None else persistence.AiiDAPersister()

        if rmq_config is not None:
            self._setup_rmq(**rmq_config)
        elif self._rmq_submit:
            logger = logging.getLogger(__name__)
            logger.warning('Disabling rmq submission, no RMQ config provided')
            self._rmq_submit = False

        # Save kwargs for creating child runners
        self._kwargs = {
            'rmq_config': rmq_config,
            'poll_interval': poll_interval,
            'rmq_submit': rmq_submit,
            'enable_persistence': enable_persistence
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def loop(self):
        return self._loop

    @property
    def rmq(self):
        return self._rmq

    @property
    def transport(self):
        return self._transport

    @property
    def persister(self):
        return self._persister

    @property
    def communicator(self):
        return self._communicator

    def is_closed(self):
        return self._closed

    def start(self):
        """Start the internal event loop."""
        self._loop.start()

    def stop(self):
        """Stop the internal event loop."""
        self._loop.stop()

    def run_until_complete(self, future):
        """Run the loop until the future has finished and return the result."""
        with utils.loop_scope(self._loop):
            return self._loop.run_sync(lambda: future)

    def close(self):
        """Close the runner by stopping the loop and disconnecting the RmqConnector if it has one."""
        assert not self._closed

        self.stop()

        if self._rmq_connector is not None:
            self._rmq_connector.disconnect()

        self._closed = True

    def instantiate_process(self, process, *args, **inputs):
        """
        Return an instance of the process with the given runner and inputs. The function can deal with various types
        of the `process`:

            * Process instance: will simply return the instance
            * JobCalculation class: will construct the JobProcess and instantiate it
            * ProcessBuilder instance: will instantiate the Process from the class and inputs defined within it
            * Process class: will instantiate with the specified inputs

        If anything else is passed, a ValueError will be raised

        :param self: instance of a Runner
        :param process: Process instance or class, JobCalculation class or ProcessBuilder instance
        :param inputs: the inputs for the process to be instantiated with
        """
        from aiida.orm.calculation.job import JobCalculation
        from aiida.work.process_builder import ProcessBuilder
        from aiida.work.processes import Process

        if isinstance(process, Process):
            assert not args
            assert not inputs
            assert self is process.runner
            return process

        if isinstance(process, ProcessBuilder):
            builder = process
            process_class = builder.process_class
            inputs.update(**builder)
        elif issubclass(process, JobCalculation):
            process_class = process.process()
        elif issubclass(process, Process):
            process_class = process
        else:
            raise ValueError('invalid process {}, needs to be Process, JobCalculation or ProcessBuilder'.format(
                type(process)))

        process = process_class(runner=self, inputs=inputs)

        return process

    def submit(self, process, *args, **inputs):
        """
        Submit the process with the supplied inputs to this runner immediately returning control to
        the interpreter. The return value will be the calculation node of the submitted process

        :param process: the process class to submit
        :param inputs: the inputs to be passed to the process
        :return: the calculation node of the process
        """
        assert not utils.is_workfunction(process), 'Cannot submit a workfunction'
        assert not self._closed

        process = self.instantiate_process(process, *args, **inputs)
        if self._rmq_submit:
            self.persister.save_checkpoint(process)
            process.close()
            self.rmq.continue_process(process.pid)
        else:
            # Run in this runner
            self.loop.add_callback(process.step_until_terminated)

        return process.calc

    def _run(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        assert not self._closed

        if utils.is_workfunction(process):
            result, node = process.run_get_node(*args, **inputs)
            return result, node

        with utils.loop_scope(self.loop):
            process = self.instantiate_process(process, *args, **inputs)
            process.execute()
            return process.outputs, process.calc

    def run(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: the outputs of the process
        """
        result, _ = self._run(process, *args, **inputs)
        return result

    def run_get_node(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        result, node = self._run(process, *args, **inputs)
        return ResultAndNode(result, node)

    def run_get_pid(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and process pid
        """
        result, node = self._run(process, *args, **inputs)
        return ResultAndPid(result, node.pk)

    def call_on_legacy_workflow_finish(self, pk, callback):
        """
        Callback to be called when the workflow of the given pk is terminated

        :param pk: the pk of the workflow
        :param callback: the function to be called upon workflow termination
        """
        workflow = load_workflow(pk=pk)
        self._poll_legacy_wf(workflow, callback)

    def call_on_calculation_finish(self, pk, callback):
        """
        Callback to be called when the calculation of the given pk is terminated

        :param pk: the pk of the calculation
        :param callback: the function to be called upon calculation termination
        """
        calculation = load_node(pk=pk)
        self._poll_calculation(calculation, callback)

    def get_calculation_future(self, pk):
        """
        Get a future for an orm Calculation. The future will have the calculation node
        as the result when finished.

        :return: A future representing the completion of the calculation node
        """
        return futures.CalculationFuture(pk, self._loop, self._poll_interval, self._communicator)

    @contextmanager
    def child_runner(self):
        """
        Contextmanager that will yield a runner that is a child of this runner

        :returns: a Runner instance that inherits the attributes of this runner
        """
        runner = self._create_child_runner()
        try:
            yield runner
        finally:
            runner.close()

    def _setup_rmq(self, url, prefix=None, task_prefetch_count=None, testing_mode=False):
        """
        Setup the RabbitMQ connection by creating a connector, communicator and control panel

        :param url: the url to use for the connector
        :param prefix: the rmq prefix to use for the communicator
        :param task_prefetch_count: the maximum number of tasks the communicator may retrieve at a given time
        :param testing_mode: whether to create a communicator in testing mode
        """
        self._rmq_connector = plumpy.rmq.RmqConnector(amqp_url=url, loop=self._loop)

        self._rmq_communicator = plumpy.rmq.RmqCommunicator(
            self._rmq_connector,
            exchange_name=rmq.get_message_exchange_name(prefix),
            task_queue=rmq.get_launch_queue_name(prefix),
            testing_mode=testing_mode,
            task_prefetch_count=task_prefetch_count)

        self._rmq = rmq.ProcessControlPanel(prefix=prefix, rmq_connector=self._rmq_connector, testing_mode=testing_mode)
        self._communicator = self._rmq.communicator

        # Establish RMQ connection
        self._communicator.connect()

    def _create_child_runner(self):
        return Runner(**self._kwargs)

    def _poll_legacy_wf(self, workflow, callback):
        if workflow.has_finished_ok() or workflow.has_failed():
            self._loop.add_callback(callback, workflow.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_legacy_wf, workflow, callback)

    def _poll_calculation(self, calc_node, callback):
        if calc_node.is_terminated:
            self._loop.add_callback(callback, calc_node.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_calculation, calc_node, callback)


class DaemonRunner(Runner):
    """
    A sub class of Runner suited for a daemon runner
    """

    def __init__(self, *args, **kwargs):
        kwargs['rmq_submit'] = True
        super(DaemonRunner, self).__init__(*args, **kwargs)

    def _setup_rmq(self, url, prefix=None, task_prefetch_count=None, testing_mode=False):
        super(DaemonRunner, self)._setup_rmq(url, prefix, task_prefetch_count, testing_mode)

        # Create a context for loading new processes
        load_context = plumpy.LoadSaveContext(runner=self)

        # Listen for incoming launch requests
        task_receiver = rmq.ProcessLauncher(
            loop=self.loop, persister=self.persister, load_context=load_context, loader=persistence.get_object_loader())
        self.communicator.add_task_subscriber(task_receiver)
