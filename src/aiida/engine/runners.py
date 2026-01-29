###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Runners that can run and submit processes."""

from __future__ import annotations

import asyncio
import functools
import logging
import signal
import threading
import uuid
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple, Type, Union

import kiwipy
from plumpy.communications import wrap_communicator
from plumpy.events import reset_event_loop_policy, set_event_loop_policy
from plumpy.persistence import Persister
from plumpy.process_comms import RemoteProcessThreadController

from aiida.common import exceptions
from aiida.orm import ProcessNode, load_node
from aiida.plugins.utils import PluginVersionProvider

from . import transports, utils
from .processes import Process, ProcessBuilder, ProcessState, futures
from .processes.calcjobs import manager

__all__ = ('Runner',)

LOGGER = logging.getLogger(__name__)


class ResultAndNode(NamedTuple):
    result: Dict[str, Any]
    node: ProcessNode


class ResultAndPk(NamedTuple):
    result: Dict[str, Any]
    pk: int | None


TYPE_RUN_PROCESS = Union[Process, Type[Process], ProcessBuilder]
# run can also be process function, but it is not clear what type this should be
TYPE_SUBMIT_PROCESS = Union[Process, Type[Process], ProcessBuilder]


class Runner:
    """Class that can launch processes by running in the current interpreter or by submitting them to the daemon."""

    _persister: Optional[Persister] = None
    _communicator: Optional[kiwipy.Communicator] = None
    _controller: Optional[RemoteProcessThreadController] = None
    _closed: bool = False

    def __init__(
        self,
        poll_interval: Union[int, float] = 0,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        communicator: Optional[kiwipy.Communicator] = None,
        broker_submit: bool = False,
        persister: Optional[Persister] = None,
    ):
        """Construct a new runner.

        :param poll_interval: interval in seconds between polling for status of active sub processes
        :param loop: an asyncio event loop, if none is suppled a new one will be created
        :param communicator: the communicator to use
        :param broker_submit: if True, processes will be submitted to the broker, otherwise they will be scheduled here
        :param persister: the persister to use to persist processes

        """
        assert not (
            broker_submit and persister is None
        ), 'Must supply a persister if you want to submit using communicator'

        set_event_loop_policy()
        self._loop = loop if loop is not None else asyncio.get_event_loop()
        self._poll_interval = poll_interval
        self._broker_submit = broker_submit
        self._transport = transports.TransportQueue(self._loop)
        self._job_manager = manager.JobManager(self._transport)
        self._persister = persister
        self._plugin_version_provider = PluginVersionProvider()

        if communicator is not None:
            self._communicator = wrap_communicator(communicator, self._loop)
            self._controller = RemoteProcessThreadController(communicator)
        elif self._broker_submit:
            LOGGER.warning('Disabling broker submission, no communicator provided')
            self._broker_submit = False

    def __enter__(self) -> 'Runner':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get the event loop of this runner."""
        return self._loop

    @property
    def transport(self) -> transports.TransportQueue:
        return self._transport

    @property
    def persister(self) -> Optional[Persister]:
        """Get the persister used by this runner."""
        return self._persister

    @property
    def communicator(self) -> Optional[kiwipy.Communicator]:
        """Get the communicator used by this runner."""
        return self._communicator

    @property
    def plugin_version_provider(self) -> PluginVersionProvider:
        return self._plugin_version_provider

    @property
    def job_manager(self) -> manager.JobManager:
        return self._job_manager

    @property
    def controller(self) -> Optional[RemoteProcessThreadController]:
        """Get the controller used by this runner."""
        return self._controller

    @property
    def is_daemon_runner(self) -> bool:
        """Return whether the runner is a daemon runner, which means it submits processes over a broker.

        :return: True if the runner is a daemon runner
        """
        return self._broker_submit

    def is_closed(self) -> bool:
        return self._closed

    def start(self) -> None:
        """Start the internal event loop."""
        self._loop.run_forever()

    def stop(self) -> None:
        """Stop the internal event loop."""
        self._loop.stop()

    def run_until_complete(self, future: asyncio.Future) -> Any:
        """Run the loop until the future has finished and return the result."""
        from plumpy.greenlet_bridge import run_until_complete

        with utils.loop_scope(self._loop):
            return run_until_complete(self._loop, future)

    def close(self) -> None:
        """Close the runner by stopping the loop."""
        assert not self._closed
        self.stop()
        if not self._loop.is_running():
            self._loop.close()
        reset_event_loop_policy()
        self._closed = True

    def instantiate_process(self, process: TYPE_RUN_PROCESS, **inputs):
        from .utils import instantiate_process

        return instantiate_process(self, process, **inputs)

    def submit(self, process: TYPE_SUBMIT_PROCESS, inputs: dict[str, Any] | None = None, **kwargs: Any):
        """Submit the process with the supplied inputs to this runner immediately returning control to the interpreter.

        The return value will be the calculation node of the submitted process

        :param process: the process class to submit
        :param inputs: the inputs to be passed to the process
        :return: the calculation node of the process
        """
        assert not utils.is_process_function(process), 'Cannot submit a process function'
        assert not self._closed

        inputs = utils.prepare_inputs(inputs, **kwargs)
        process_inited = self.instantiate_process(process, **inputs)

        if not process_inited.metadata.store_provenance:
            raise exceptions.InvalidOperation('cannot submit a process with `store_provenance=False`')

        if process_inited.metadata.get('dry_run', False):
            raise exceptions.InvalidOperation('cannot submit a process from within another with `dry_run=True`')

        if self._broker_submit:
            assert self.persister is not None, 'runner does not have a persister'
            assert self.controller is not None, 'runner does not have a controller'
            self.persister.save_checkpoint(process_inited)
            process_inited.close()
            self.controller.continue_process(process_inited.pid, nowait=False, no_reply=True)
        else:
            self.loop.create_task(process_inited.step_until_terminated())

        return process_inited.node

    def schedule(
        self, process: TYPE_SUBMIT_PROCESS, inputs: dict[str, Any] | None = None, **kwargs: Any
    ) -> ProcessNode:
        """Schedule a process to be executed by this runner.

        :param process: the process class to submit
        :param inputs: the inputs to be passed to the process
        :return: the calculation node of the process
        """
        assert not utils.is_process_function(process), 'Cannot submit a process function'
        assert not self._closed

        inputs = utils.prepare_inputs(inputs, **kwargs)
        process_inited = self.instantiate_process(process, **inputs)
        self.loop.create_task(process_inited.step_until_terminated())
        return process_inited.node

    def _run(
        self, process: TYPE_RUN_PROCESS, inputs: dict[str, Any] | None = None, **kwargs: Any
    ) -> Tuple[Dict[str, Any], ProcessNode]:
        """Run the process with the supplied inputs in this runner that will block until the process is completed.

        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        assert not self._closed

        inputs = utils.prepare_inputs(inputs, **kwargs)

        if utils.is_process_function(process):
            result, node = process.run_get_node(**inputs)  # type: ignore[union-attr]
            return result, node

        with utils.loop_scope(self.loop):
            process_inited = self.instantiate_process(process, **inputs)

            def kill_process(_num, _frame):
                """Send the kill signal to the process in the current scope."""
                if process_inited.is_killing:
                    LOGGER.warning('runner received interrupt, process %s already being killed', process_inited.pid)
                    return
                LOGGER.critical('runner received interrupt, killing process %s', process_inited.pid)
                process_inited.kill(msg_text='Process was killed because the runner received an interrupt')

            original_handler_int = signal.getsignal(signal.SIGINT)
            original_handler_term = signal.getsignal(signal.SIGTERM)

            try:
                signal.signal(signal.SIGINT, kill_process)
                signal.signal(signal.SIGTERM, kill_process)
                process_inited.execute()
            finally:
                signal.signal(signal.SIGINT, original_handler_int)
                signal.signal(signal.SIGTERM, original_handler_term)

            return process_inited.outputs, process_inited.node

    def run(self, process: TYPE_RUN_PROCESS, inputs: dict[str, Any] | None = None, **kwargs: Any) -> Dict[str, Any]:
        """Run the process with the supplied inputs in this runner that will block until the process is completed.

        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: the outputs of the process
        """
        result, _ = self._run(process, inputs, **kwargs)
        return result

    def run_get_node(
        self, process: TYPE_RUN_PROCESS, inputs: dict[str, Any] | None = None, **kwargs: Any
    ) -> ResultAndNode:
        """Run the process with the supplied inputs in this runner that will block until the process is completed.

        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        result, node = self._run(process, inputs, **kwargs)
        return ResultAndNode(result, node)

    def run_get_pk(self, process: TYPE_RUN_PROCESS, inputs: dict[str, Any] | None = None, **kwargs: Any) -> ResultAndPk:
        """Run the process with the supplied inputs in this runner that will block until the process is completed.

        The return value will be the results of the completed process

        :param process: the process class or process function to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and process node pk
        """
        result, node = self._run(process, inputs, **kwargs)
        return ResultAndPk(result, node.pk)

    def call_on_process_finish(self, pk: int, callback: Callable[[], Any]) -> None:
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

        def inline_callback(event, *args, **kwargs):
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
                if self.communicator:
                    self.communicator.remove_broadcast_subscriber(subscriber_identifier)

        broadcast_filter = kiwipy.BroadcastFilter(functools.partial(inline_callback, event), sender=pk)
        for state in [ProcessState.FINISHED, ProcessState.KILLED, ProcessState.EXCEPTED]:
            broadcast_filter.add_subject_filter(f'state_changed.*.{state.value}')

        if self.communicator:
            LOGGER.info('adding subscriber for broadcasts of %d', pk)
            self.communicator.add_broadcast_subscriber(broadcast_filter, subscriber_identifier)
        self._poll_process(node, functools.partial(inline_callback, event))

    def get_process_future(self, pk: int) -> futures.ProcessFuture:
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
            self._loop.call_soon(callback)
        else:
            self._loop.call_later(self._poll_interval, self._poll_process, node, callback)
