# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import,global-statement
"""Runners that can run and submit processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import namedtuple
import logging
import tornado.ioloop

import plumpy

from aiida.orm import load_node
from .processes import futures
from .processes.calcjobs import manager
from .utils import instantiate_process
from . import transports
from . import utils

__all__ = ('Runner',)

LOGGER = logging.getLogger(__name__)

ResultAndNode = namedtuple('ResultAndNode', ['result', 'node'])
ResultAndPk = namedtuple('ResultAndPk', ['result', 'pk'])


class Runner(object):  # pylint: disable=useless-object-inheritance
    """Class that can launch processes by running in the current interpreter or by submitting them to the daemon."""

    _persister = None
    _communicator = None
    _controller = None
    _closed = False

    def __init__(self, poll_interval=0, loop=None, communicator=None, rmq_submit=False, persister=None):
        """
        Construct a new runner

        :param poll_interval: interval in seconds between polling for status of active calculations
        :param loop: an event loop to use, if none is suppled a new one will be created
        :type loop: :class:`tornado.ioloop.IOLoop`
        :param communicator: the communicator to use
        :type communicator: :class:`kiwipy.Communicator`
        :param rmq_submit: if True, processes will be submitted to RabbitMQ, otherwise they will be scheduled here
        :param persister: the persister to use to persist processes
        :type persister: :class:`plumpy.Persister`
        """
        assert not (rmq_submit and persister is None), \
            'Must supply a persister if you want to submit using communicator'

        self._loop = loop if loop is not None else tornado.ioloop.IOLoop()
        self._poll_interval = poll_interval
        self._rmq_submit = rmq_submit
        self._transport = transports.TransportQueue(self._loop)
        self._job_manager = manager.JobManager(self._transport)
        self._persister = persister

        if communicator is not None:
            self._communicator = communicator
            self._controller = plumpy.RemoteProcessThreadController(communicator)
        elif self._rmq_submit:
            LOGGER.warning('Disabling RabbitMQ submission, no communicator provided')
            self._rmq_submit = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def loop(self):
        """
        Get the event loop of this runner

        :return: the event loop
        :rtype: :class:`tornado.ioloop.IOLoop`
        """
        return self._loop

    @property
    def transport(self):
        return self._transport

    @property
    def persister(self):
        return self._persister

    @property
    def communicator(self):
        """
        Get the communicator used by this runner

        :return: the communicator
        :rtype: :class:`kiwipy.Communicator`
        """
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
        assert not utils.is_process_function(process), 'Cannot submit a process function'
        assert not self._closed

        process = instantiate_process(self, process, *args, **inputs)

        if self._rmq_submit:
            self.persister.save_checkpoint(process)
            process.close()
            self.controller.continue_process(process.pid, nowait=False, no_reply=True)
        else:
            self.loop.add_callback(process.step_until_terminated)

        return process.node

    def schedule(self, process, *args, **inputs):
        """
        Schedule a process to be executed by this runner

        :param process: the process class to submit
        :param inputs: the inputs to be passed to the process
        :return: the calculation node of the process
        """
        assert not utils.is_process_function(process), 'Cannot submit a process function'
        assert not self._closed

        process = instantiate_process(self, process, *args, **inputs)
        self.loop.add_callback(process.step_until_terminated)
        return process.node

    def _run(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        assert not self._closed

        if utils.is_process_function(process):
            result, node = process.run_get_node(*args, **inputs)
            return result, node

        with utils.loop_scope(self.loop):
            process = instantiate_process(self, process, *args, **inputs)
            process.execute()
            return process.outputs, process.node

    def run(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: the outputs of the process
        """
        result, _ = self._run(process, *args, **inputs)
        return result

    def run_get_node(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        result, node = self._run(process, *args, **inputs)
        return ResultAndNode(result, node)

    def run_get_pk(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and process node pk
        """
        result, node = self._run(process, *args, **inputs)
        return ResultAndPk(result, node.pk)

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

    def _poll_calculation(self, calc_node, callback):
        if calc_node.is_terminated:
            self._loop.add_callback(callback, calc_node.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_calculation, calc_node, callback)
