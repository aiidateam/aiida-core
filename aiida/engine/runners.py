# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Runners that can run and submit processes."""
import collections
import functools
import logging
import signal
import threading
import uuid

import kiwipy
import plumpy
import tornado.ioloop

from aiida.common import exceptions
from aiida.orm import load_node
from aiida.plugins.utils import PluginVersionProvider

from .processes import futures, ProcessState
from .processes.calcjobs import manager
from . import transports
from . import utils

__all__ = ('Runner',)

LOGGER = logging.getLogger(__name__)

ResultAndNode = collections.namedtuple('ResultAndNode', ['result', 'node'])
ResultAndPk = collections.namedtuple('ResultAndPk', ['result', 'pk'])


class Runner:  # pylint: disable=too-many-public-methods
    """Class that can launch processes by running in the current interpreter or by submitting them to the daemon."""

    _persister = None
    _communicator = None
    _controller = None
    _closed = False

    def __init__(self, poll_interval=0, loop=None, communicator=None, rmq_submit=False, persister=None):
        """Construct a new runner.

        :param poll_interval: interval in seconds between polling for status of active sub processes
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

        # Runner take responsibility to clear up loop only if the loop was created by Runner
        self._do_close_loop = False
        if loop is not None:
            self._loop = loop
        else:
            self._loop = tornado.ioloop.IOLoop()
            self._do_close_loop = True

        self._poll_interval = poll_interval
        self._rmq_submit = rmq_submit
        self._transport = transports.TransportQueue(self._loop)
        self._job_manager = manager.JobManager(self._transport)
        self._persister = persister
        self._plugin_version_provider = PluginVersionProvider()

        if communicator is not None:
            self._communicator = plumpy.wrap_communicator(communicator, self._loop)
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
    def plugin_version_provider(self):
        return self._plugin_version_provider

    @property
    def job_manager(self):
        return self._job_manager

    @property
    def controller(self):
        return self._controller

    @property
    def is_daemon_runner(self):
        """Return whether the runner is a daemon runner, which means it submits processes over RabbitMQ.

        :return: True if the runner is a daemon runner
        :rtype: bool
        """
        return self._rmq_submit

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
        if self._do_close_loop:
            self._loop.close()
        self._closed = True

    def instantiate_process(self, process, *args, **inputs):
        from .utils import instantiate_process
        return instantiate_process(self, process, *args, **inputs)

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

        process = self.instantiate_process(process, *args, **inputs)

        if not process.metadata.store_provenance:
            raise exceptions.InvalidOperation('cannot submit a process with `store_provenance=False`')

        if process.metadata.get('dry_run', False):
            raise exceptions.InvalidOperation('cannot submit a process from within another with `dry_run=True`')

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

        process = self.instantiate_process(process, *args, **inputs)
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
            process = self.instantiate_process(process, *args, **inputs)

            def kill_process(_num, _frame):
                """Send the kill signal to the process in the current scope."""
                LOGGER.critical('runner received interrupt, killing process %s', process.pid)
                process.kill(msg='Process was killed because the runner received an interrupt')

            signal.signal(signal.SIGINT, kill_process)
            signal.signal(signal.SIGTERM, kill_process)

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

    def call_on_process_finish(self, pk, callback):
        """Schedule a callback when the process of the given pk is terminated.

        This method will add a broadcast subscriber that will listen for state changes of the target process to be
        terminated. As a fail-safe, a polling-mechanism is used to check the state of the process, should the broadcast
        message be missed by the subscriber, in order to prevent the caller to wait indefinitely.

        :param pk: pk of the process
        :param callback: function to be called upon process termination
        """
        node = load_node(pk=pk)
        subscriber_identifier = str(uuid.uuid4())
        event = threading.Event()

        def inline_callback(event, *args, **kwargs):  # pylint: disable=unused-argument
            """Callback to wrap the actual callback, that will always remove the subscriber that will be registered.

            As soon as the callback is called successfully once, the `event` instance is toggled, such that if this
            inline callback is called a second time, the actual callback is not called again.
            """
            if event.is_set():
                return

            try:
                callback()
            finally:
                event.set()
                self._communicator.remove_broadcast_subscriber(subscriber_identifier)

        broadcast_filter = kiwipy.BroadcastFilter(functools.partial(inline_callback, event), sender=pk)
        for state in [ProcessState.FINISHED, ProcessState.KILLED, ProcessState.EXCEPTED]:
            broadcast_filter.add_subject_filter(f'state_changed.*.{state.value}')

        LOGGER.info('adding subscriber for broadcasts of %d', pk)
        self._communicator.add_broadcast_subscriber(broadcast_filter, subscriber_identifier)
        self._poll_process(node, functools.partial(inline_callback, event))

    def get_process_future(self, pk):
        """Return a future for a process.

        The future will have the process node as the result when finished.

        :return: A future representing the completion of the process node
        """
        return futures.ProcessFuture(pk, self._loop, self._poll_interval, self._communicator)

    def _poll_process(self, node, callback):
        """Check whether the process state of the node is terminated and call the callback or reschedule it.

        :param node: the process node
        :param callback: callback to be called when process is terminated
        """
        if node.is_terminated:
            args = [node.__class__.__name__, node.pk]
            LOGGER.info('%s<%d> confirmed to be terminated by backup polling mechanism', *args)
            self._loop.add_callback(callback)
        else:
            self._loop.call_later(self._poll_interval, self._poll_process, node, callback)
