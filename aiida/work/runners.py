# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement,cyclic-import
"""Runners that can run and submit processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from collections import namedtuple
import logging
import tornado.ioloop

import plumpy

from aiida.orm import load_node, load_workflow
from aiida.work.communication import controllers
from aiida.work.processes import instantiate_process
from . import job_calcs
from . import futures
from . import persistence
from . import rmq
from . import transports
from . import utils

__all__ = ['Runner', 'create_runner', 'set_runner', 'get_runner']

ResultAndNode = namedtuple('ResultAndNode', ['result', 'node'])
ResultAndPid = namedtuple('ResultAndPid', ['result', 'pid'])

RUNNER = None


def create_runner(**kwargs):
    """
    Create a default runner optionally passing keyword arguments

    :param kwargs: arguments to be passed to Runner constructor
    :return: a new runner instance
    """
    from aiida.work.communication import communicators

    if 'communicator' not in kwargs:
        kwargs['communicator'] = communicators.get_communicator()

    return Runner(**kwargs)


def get_runner():
    """
    Get the global runner instance

    :returns: the global runner
    """
    global RUNNER

    if RUNNER is None or RUNNER.is_closed():
        RUNNER = create_runner()

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
    _communicator = None
    _controller = None
    _closed = False

    def __init__(self,
                 poll_interval=0.,
                 loop=None,
                 communicator=None,
                 rmq_submit=False,
                 enable_persistence=True,
                 persister=None,
                 daemon=False):
        # pylint: disable=too-many-arguments
        self._loop = loop if loop is not None else tornado.ioloop.IOLoop()
        self._poll_interval = poll_interval
        self._rmq_submit = rmq_submit
        self._transport = transports.TransportQueue(self._loop)
        self._job_manager = job_calcs.JobManager(self._transport)

        if enable_persistence:
            self._persister = persister if persister is not None else persistence.AiiDAPersister()

        if daemon:
            assert communicator is not None, 'a daemon runner needs a communicator'
            communicator = plumpy.wrap_communicator(communicator, self._loop)

        if communicator is not None:
            self._communicator = communicator
            self._controller = controllers.create_controller(communicator)
        elif self._rmq_submit:
            logger = logging.getLogger(__name__)
            logger.warning('Disabling RabbitMQ submission, no communicator provided')
            self._rmq_submit = False

        if daemon:
            # Create a context for loading new processes
            load_context = plumpy.LoadSaveContext(runner=self)

            # Listen for incoming launch requests
            task_receiver = rmq.ProcessLauncher(
                loop=self.loop,
                persister=self.persister,
                load_context=load_context,
                loader=persistence.get_object_loader())
            self.communicator.add_task_subscriber(task_receiver)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def loop(self):
        return self._loop

    @property
    def transport(self):
        return self._transport

    @property
    def persister(self):
        return self._persister

    @property
    def communicator(self):
        return self._communicator

    @property
    def job_manager(self):
        return self._job_manager

    @property
    def controller(self):
        return self._controller

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
        """Close the runner by stopping the loop."""
        assert not self._closed
        self.stop()
        self._closed = True

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

        process = instantiate_process(self, process, *args, **inputs)

        if self._rmq_submit:
            self.persister.save_checkpoint(process)
            process.close()
            self.controller.continue_process(process.pid, nowait=False, no_reply=True)
        else:
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
            process = instantiate_process(self, process, *args, **inputs)
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
