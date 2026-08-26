###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from Plumpy.                         #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The Plumpy license is reproduced in open_source_licenses.txt.         #
###########################################################################
"""Communication helpers and process-level controllers."""

from __future__ import annotations

import asyncio
import functools
import logging
from collections.abc import Callable, Hashable, Sequence
from typing import TYPE_CHECKING, Any, cast

import kiwipy

from aiida.common import loaders
from aiida.engine.processes import events, persistence
from aiida.engine.processes.generic import futures
from aiida.engine.processes.persistence import PID_TYPE
from aiida.engine.utils import ensure_coroutine

__all__: tuple[str, ...] = ()

RemoteException = kiwipy.RemoteException
DeliveryFailed = kiwipy.DeliveryFailed
TaskRejected = kiwipy.TaskRejected
Communicator = kiwipy.Communicator

if TYPE_CHECKING:
    from aiida.engine.processes.generic.process import Process

    # identifiers for subscribers
    ID_TYPE = Hashable
    Subscriber = Callable[..., Any]
    # RPC subscriber params: communicator, msg
    RpcSubscriber = Callable[[kiwipy.Communicator, Any], Any]
    # Task subscriber params: communicator, task
    TaskSubscriber = Callable[[kiwipy.Communicator, Any], Any]
    # Broadcast subscribers params: communicator, body, sender, subject, correlation id
    BroadcastSubscriber = Callable[[kiwipy.Communicator, Any, Any, Any, ID_TYPE], Any]


def plum_to_kiwi_future(plum_future: futures.Future) -> kiwipy.Future:
    """
    Return a kiwi future that resolves to the outcome of the plum future

    :param plum_future: the plum future
    :return: the kiwipy future

    """
    kiwi_future = kiwipy.Future()

    def on_done(_plum_future: futures.Future) -> None:
        with kiwipy.capture_exceptions(kiwi_future):
            if plum_future.cancelled():
                kiwi_future.cancel()
            else:
                result = plum_future.result()
                # Did we get another future?  In which case convert it too
                if isinstance(result, futures.Future):
                    result = plum_to_kiwi_future(result)
                kiwi_future.set_result(result)

    plum_future.add_done_callback(on_done)
    return kiwi_future


def convert_to_comm(
    callback: Subscriber, loop: asyncio.AbstractEventLoop | None = None
) -> Callable[..., kiwipy.Future]:
    """
    Take a callback function and converted it to one that will schedule a callback
    on the given even loop and return a kiwi future representing the future outcome
    of the original method.

    :param callback: the function to convert
    :param loop: the even loop to schedule the callback in
    :return: a new callback function that returns a future
    """
    if isinstance(callback, kiwipy.BroadcastFilter):
        # if the broadcast is filtered for this callback,
        # we don't want to go through the (costly) process
        # of setting up async tasks and callbacks

        def _passthrough(*args: Any, **kwargs: Any) -> bool:
            sender = kwargs['sender'] if 'sender' in kwargs else args[1]
            subject = kwargs['subject'] if 'subject' in kwargs else args[2]
            return callback.is_filtered(sender, subject)
    else:

        def _passthrough(*args: Any, **kwargs: Any) -> bool:
            return False

    coro = ensure_coroutine(callback)

    def converted(communicator: kiwipy.Communicator, *args: Any, **kwargs: Any) -> kiwipy.Future:
        if _passthrough(*args, **kwargs):
            kiwi_future = kiwipy.Future()
            kiwi_future.set_result(None)
            return kiwi_future

        msg_fn = functools.partial(coro, communicator, *args, **kwargs)
        task_future = futures.create_task(msg_fn, loop)
        return plum_to_kiwi_future(task_future)

    return converted


def wrap_communicator(
    communicator: kiwipy.Communicator, loop: asyncio.AbstractEventLoop | None = None
) -> LoopCommunicator:
    """
    Wrap a communicator such that all callbacks made to any subscribers are scheduled on the
    given event loop.

    If the communicator is already an equivalent communicator wrapper then it will not be
    wrapped again.

    :param communicator: the communicator to wrap
    :param loop: the event loop to schedule callbacks on

    :return: a communicator wrapper

    """
    if isinstance(communicator, LoopCommunicator) and communicator.loop() is loop:
        return communicator

    return LoopCommunicator(communicator, loop)


class LoopCommunicator(kiwipy.Communicator):
    """Wrapper around a `kiwipy.Communicator` that schedules any subscriber messages on a given event loop."""

    def __init__(self, communicator: kiwipy.Communicator, loop: asyncio.AbstractEventLoop | None = None):
        """
        :param communicator: The kiwipy communicator
        :param loop: The event loop to schedule callbacks on

        """
        assert communicator is not None

        self._communicator = communicator
        self._loop = loop or events.get_or_create_event_loop()

    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def add_rpc_subscriber(self, subscriber: RpcSubscriber, identifier: ID_TYPE | None = None) -> ID_TYPE:
        converted = convert_to_comm(subscriber, self._loop)
        return self._communicator.add_rpc_subscriber(converted, identifier)

    def remove_rpc_subscriber(self, identifier: ID_TYPE) -> None:
        return self._communicator.remove_rpc_subscriber(identifier)

    def add_task_subscriber(self, subscriber: TaskSubscriber, identifier: ID_TYPE | None = None) -> ID_TYPE:
        converted = convert_to_comm(subscriber, self._loop)
        return self._communicator.add_task_subscriber(converted, identifier)

    def remove_task_subscriber(self, identifier: ID_TYPE) -> None:
        return self._communicator.remove_task_subscriber(identifier)

    def add_broadcast_subscriber(self, subscriber: BroadcastSubscriber, identifier: ID_TYPE | None = None) -> ID_TYPE:
        converted = convert_to_comm(subscriber, self._loop)
        return self._communicator.add_broadcast_subscriber(converted, identifier)

    def remove_broadcast_subscriber(self, identifier: ID_TYPE) -> None:
        return self._communicator.remove_broadcast_subscriber(identifier)

    def task_send(self, task: Any, no_reply: bool = False) -> kiwipy.Future:
        return self._communicator.task_send(task, no_reply)

    def rpc_send(self, recipient_id: ID_TYPE, msg: Any) -> kiwipy.Future:
        return self._communicator.rpc_send(recipient_id, msg)

    def broadcast_send(
        self,
        body: Any | None,
        sender: str | None = None,
        subject: str | None = None,
        correlation_id: ID_TYPE | None = None,
    ) -> futures.Future:
        return self._communicator.broadcast_send(body, sender, subject, correlation_id)

    def is_closed(self) -> bool:
        """Return `True` if the communicator was closed"""
        return self._communicator.is_closed()

    def close(self) -> None:
        """Close a communicator, free up all resources and do not allow any further operations"""
        self._communicator.close()


ProcessResult = Any
ProcessStatus = Any

INTENT_KEY = 'intent'
MESSAGE_TEXT_KEY = 'message'
FORCE_KILL_KEY = 'force_kill'


class Intent:
    """Intent constants for a process message"""

    PLAY: str = 'play'
    PAUSE: str = 'pause'
    KILL: str = 'kill'
    STATUS: str = 'status'


MessageType = dict[str, Any]


class MessageBuilder:
    """MessageBuilder will construct different messages that can passing over communicator."""

    @classmethod
    def play(cls, text: str | None = None) -> MessageType:
        """The play message send over communicator."""
        return {
            INTENT_KEY: Intent.PLAY,
            MESSAGE_TEXT_KEY: text,
        }

    @classmethod
    def pause(cls, text: str | None = None) -> MessageType:
        """The pause message send over communicator."""
        return {
            INTENT_KEY: Intent.PAUSE,
            MESSAGE_TEXT_KEY: text,
        }

    @classmethod
    def kill(cls, text: str | None = None, force_kill: bool = False) -> MessageType:
        """The kill message send over communicator."""
        return {
            INTENT_KEY: Intent.KILL,
            MESSAGE_TEXT_KEY: text,
            FORCE_KILL_KEY: force_kill,
        }

    @classmethod
    def status(cls, text: str | None = None) -> MessageType:
        """The status message send over communicator."""
        return {
            INTENT_KEY: Intent.STATUS,
            MESSAGE_TEXT_KEY: text,
        }


TASK_KEY = 'task'
TASK_ARGS = 'args'
PERSIST_KEY = 'persist'
# Launch
PROCESS_CLASS_KEY = 'process_class'
ARGS_KEY = 'init_args'
KWARGS_KEY = 'init_kwargs'
NOWAIT_KEY = 'nowait'
# Continue
PID_KEY = 'pid'
TAG_KEY = 'tag'
# Task types
LAUNCH_TASK = 'launch'
CONTINUE_TASK = 'continue'
CREATE_TASK = 'create'

LOGGER = logging.getLogger(__name__)


def create_launch_body(
    process_class: type[Process],
    init_args: Sequence[Any] | None = None,
    init_kwargs: dict[str, Any] | None = None,
    persist: bool = False,
    loader: loaders.ObjectLoader | None = None,
    nowait: bool = True,
) -> dict[str, Any]:
    """
    Create a message body for the launch action

    :param process_class: the class of the process to launch
    :param init_args: any initialisation positional arguments
    :param init_kwargs: any initialisation keyword arguments
    :param persist: persist this process if True, otherwise don't
    :param loader: the loader to use to load the persisted process
    :param nowait: wait for the process to finish before completing the task, otherwise just return the PID
    :return: a dictionary with the body of the message to launch the process
    :rtype: dict
    """
    if loader is None:
        loader = loaders.get_object_loader()

    msg_body = {
        TASK_KEY: LAUNCH_TASK,
        TASK_ARGS: {
            PROCESS_CLASS_KEY: loader.identify_object(process_class),
            PERSIST_KEY: persist,
            NOWAIT_KEY: nowait,
            ARGS_KEY: init_args,
            KWARGS_KEY: init_kwargs,
        },
    }
    return msg_body


def create_continue_body(pid: PID_TYPE, tag: str | None = None, nowait: bool = False) -> dict[str, Any]:
    """
    Create a message body to continue an existing process
    :param pid: the pid of the existing process
    :param tag: the optional persistence tag
    :param nowait: wait for the process to finish before completing the task, otherwise just return the PID
    :return: a dictionary with the body of the message to continue the process

    """
    msg_body = {TASK_KEY: CONTINUE_TASK, TASK_ARGS: {PID_KEY: pid, NOWAIT_KEY: nowait, TAG_KEY: tag}}
    return msg_body


def create_create_body(
    process_class: type[Process],
    init_args: Sequence[Any] | None = None,
    init_kwargs: dict[str, Any] | None = None,
    persist: bool = False,
    loader: loaders.ObjectLoader | None = None,
) -> dict[str, Any]:
    """
    Create a message body to create a new process
    :param process_class: the class of the process to launch
    :param init_args: any initialisation positional arguments
    :param init_kwargs: any initialisation keyword arguments
    :param persist: persist this process if True, otherwise don't
    :param loader: the loader to use to load the persisted process
    :return: a dictionary with the body of the message to launch the process

    """
    if loader is None:
        loader = loaders.get_object_loader()

    msg_body = {
        TASK_KEY: CREATE_TASK,
        TASK_ARGS: {
            PROCESS_CLASS_KEY: loader.identify_object(process_class),
            PERSIST_KEY: persist,
            ARGS_KEY: init_args,
            KWARGS_KEY: init_kwargs,
        },
    }
    return msg_body


class RemoteProcessController:
    """
    Control remote processes using coroutines that will send messages and wait
    (in a non-blocking way) for their response
    """

    def __init__(self, communicator: kiwipy.Communicator) -> None:
        self._communicator = communicator

    async def get_status(self, pid: PID_TYPE) -> ProcessStatus:
        """
        Get the status of a process with the given PID
        :param pid: the process id
        :return: the status response from the process
        """
        status_future = self._communicator.rpc_send(pid, MessageBuilder.status())
        future = await asyncio.wrap_future(status_future)
        result = await asyncio.wrap_future(future)
        return result

    async def pause_process(self, pid: PID_TYPE, msg_text: str | None = None) -> ProcessResult:
        """
        Pause the process

        :param pid: the pid of the process to pause
        :param msg: optional pause message
        :return: True if paused, False otherwise
        """
        msg = MessageBuilder.pause(text=msg_text)

        pause_future = self._communicator.rpc_send(pid, msg)
        # rpc_send return a thread future from communicator
        future = await asyncio.wrap_future(pause_future)
        # future is just returned from rpc call which return a kiwipy future
        result = await asyncio.wrap_future(future)
        return result

    async def play_process(self, pid: PID_TYPE) -> ProcessResult:
        """
        Play the process

        :param pid: the pid of the process to play
        :return: True if played, False otherwise
        """
        play_future = self._communicator.rpc_send(pid, MessageBuilder.play())
        future = await asyncio.wrap_future(play_future)
        result = await asyncio.wrap_future(future)
        return result

    async def kill_process(self, pid: PID_TYPE, msg_text: str | None = None, force_kill: bool = False) -> ProcessResult:
        """
        Kill the process

        :param pid: the pid of the process to kill
        :param msg: optional kill message
        :return: True if killed, False otherwise
        """
        msg = MessageBuilder.kill(text=msg_text, force_kill=force_kill)

        # Wait for the communication to go through
        kill_future = self._communicator.rpc_send(pid, msg)
        future = await asyncio.wrap_future(kill_future)
        # Now wait for the kill to be enacted
        result = await asyncio.wrap_future(future)
        return result

    async def continue_process(
        self, pid: PID_TYPE, tag: str | None = None, nowait: bool = False, no_reply: bool = False
    ) -> ProcessResult | None:
        """
        Continue the process

        :param _communicator: the communicator
        :param pid: the pid of the process to continue
        :param tag: the checkpoint tag to continue from
        """
        message = create_continue_body(pid=pid, tag=tag, nowait=nowait)
        # Wait for the communication to go through
        continue_future = self._communicator.task_send(message, no_reply=no_reply)
        future = await asyncio.wrap_future(continue_future)

        if no_reply:
            return None

        # Now wait for the result of the task
        result = await asyncio.wrap_future(future)
        return result

    async def launch_process(
        self,
        process_class: type[Process],
        init_args: Sequence[Any] | None = None,
        init_kwargs: dict[str, Any] | None = None,
        persist: bool = False,
        loader: loaders.ObjectLoader | None = None,
        nowait: bool = False,
        no_reply: bool = False,
    ) -> ProcessResult:
        """
        Launch a process given the class and constructor arguments

        :param process_class: the class of the process to launch
        :param init_args: the constructor positional arguments
        :param init_kwargs: the constructor keyword arguments
        :param persist: should the process be persisted
        :param loader: the classloader to use
        :param nowait: if True, don't wait for the process to send a response, just return the pid
        :param no_reply: if True, this call will be fire-and-forget, i.e. no return value
        :return: the result of launching the process
        """

        message = create_launch_body(process_class, init_args, init_kwargs, persist, loader, nowait)
        launch_future = self._communicator.task_send(message, no_reply=no_reply)
        future = await asyncio.wrap_future(launch_future)

        if no_reply:
            return

        result = await asyncio.wrap_future(future)
        return result

    async def execute_process(
        self,
        process_class: type[Process],
        init_args: Sequence[Any] | None = None,
        init_kwargs: dict[str, Any] | None = None,
        loader: loaders.ObjectLoader | None = None,
        nowait: bool = False,
        no_reply: bool = False,
    ) -> ProcessResult:
        """
        Execute a process.  This call will first send a create task and then a continue task over
        the communicator.  This means that if communicator messages are durable then the process
        will run until the end even if this interpreter instance ceases to exist.

        :param process_class: the process class to execute
        :param init_args: the positional arguments to the class constructor
        :param init_kwargs: the keyword arguments to the class constructor
        :param loader: the class loader to use
        :param nowait: if True, don't wait for the process to send a response
        :param no_reply: if True, this call will be fire-and-forget, i.e. no return value
        :return: the result of executing the process
        """

        message = create_create_body(process_class, init_args, init_kwargs, persist=True, loader=loader)

        create_future = self._communicator.task_send(message)
        future = await asyncio.wrap_future(create_future)
        pid: PID_TYPE = await asyncio.wrap_future(future)

        message = create_continue_body(pid, nowait=nowait)
        continue_future = self._communicator.task_send(message, no_reply=no_reply)
        future = await asyncio.wrap_future(continue_future)

        if no_reply:
            return

        result = await asyncio.wrap_future(future)
        return result


class RemoteProcessThreadController:
    """
    A class that can be used to control and launch remote processes
    """

    def __init__(self, communicator: kiwipy.Communicator):
        """
        Create a new process controller

        :param communicator: the communicator to use

        """
        self._communicator = communicator

    def get_status(self, pid: PID_TYPE) -> kiwipy.Future:
        """Get the status of a process with the given PID.

        :param pid: the process id
        :return: the status response from the process
        """
        return self._communicator.rpc_send(pid, MessageBuilder.status())

    def pause_process(self, pid: PID_TYPE, msg_text: str | None = None) -> kiwipy.Future:
        """
        Pause the process

        :param pid: the pid of the process to pause
        :param msg: optional pause message
        :return: a response future from the process to be paused

        """
        msg = MessageBuilder.pause(text=msg_text)

        return self._communicator.rpc_send(pid, msg)

    def pause_all(self, msg_text: str | None) -> None:
        """
        Pause all processes that are subscribed to the same communicator

        :param msg: an optional pause message
        """
        msg = MessageBuilder.pause(text=msg_text)
        self._communicator.broadcast_send(msg, subject=Intent.PAUSE)

    def play_process(self, pid: PID_TYPE) -> kiwipy.Future:
        """
        Play the process

        :param pid: the pid of the process to pause
        :return: a response future from the process to be played

        """
        return self._communicator.rpc_send(pid, MessageBuilder.play())

    def play_all(self) -> None:
        """
        Play all processes that are subscribed to the same communicator
        """
        self._communicator.broadcast_send(None, subject=Intent.PLAY)

    def kill_process(self, pid: PID_TYPE, msg_text: str | None = None, force_kill: bool = False) -> kiwipy.Future:
        """
        Kill the process

        :param pid: the pid of the process to kill
        :param msg: optional kill message
        :return: a response future from the process to be killed
        """
        msg = MessageBuilder.kill(text=msg_text, force_kill=force_kill)
        return self._communicator.rpc_send(pid, msg)

    def kill_all(self, msg_text: str | None) -> None:
        """
        Kill all processes that are subscribed to the same communicator

        :param msg: an optional pause message
        """
        msg = MessageBuilder.kill(msg_text)

        self._communicator.broadcast_send(msg, subject=Intent.KILL)

    def continue_process(
        self, pid: PID_TYPE, tag: str | None = None, nowait: bool = False, no_reply: bool = False
    ) -> None | PID_TYPE | ProcessResult:
        message = create_continue_body(pid=pid, tag=tag, nowait=nowait)
        return self.task_send(message, no_reply=no_reply)

    def launch_process(
        self,
        process_class: type[Process],
        init_args: Sequence[Any] | None = None,
        init_kwargs: dict[str, Any] | None = None,
        persist: bool = False,
        loader: loaders.ObjectLoader | None = None,
        nowait: bool = False,
        no_reply: bool = False,
    ) -> None | PID_TYPE | ProcessResult:
        """
        Launch the process

        :param process_class: the process class to launch
        :param init_args: positional arguments to the process constructor
        :param init_kwargs: keyword arguments to the process constructor
        :param persist: should the process be persisted
        :param loader: the class loader to use
        :param nowait: if True only return when the process finishes
        :param no_reply: don't send a reply to the sender
        :return: the pid of the created process or the outputs (if nowait=False)
        """
        message = create_launch_body(process_class, init_args, init_kwargs, persist, loader, nowait)
        return self.task_send(message, no_reply=no_reply)

    def execute_process(
        self,
        process_class: type[Process],
        init_args: Sequence[Any] | None = None,
        init_kwargs: dict[str, Any] | None = None,
        loader: loaders.ObjectLoader | None = None,
        nowait: bool = False,
        no_reply: bool = False,
    ) -> None | PID_TYPE | ProcessResult:
        """
        Execute a process.  This call will first send a create task and then a continue task over
        the communicator.  This means that if communicator messages are durable then the process
        will run until the end even if this interpreter instance ceases to exist.

        :param process_class: the process class to execute
        :param init_args: the positional arguments to the class constructor
        :param init_kwargs: the keyword arguments to the class constructor
        :param loader: the class loader to use
        :param nowait: if True, don't wait for the process to send a response
        :param no_reply: if True, this call will be fire-and-forget, i.e. no return value
        :return: the result of executing the process
        """

        message = create_create_body(process_class, init_args, init_kwargs, persist=True, loader=loader)

        execute_future = kiwipy.Future()
        create_future = futures.unwrap_kiwi_future(self._communicator.task_send(message))

        def on_created(_: Any) -> None:
            with kiwipy.capture_exceptions(execute_future):
                pid: PID_TYPE = create_future.result()
                continue_future = self.continue_process(pid, nowait=nowait, no_reply=no_reply)
                kiwipy.chain(continue_future, execute_future)

        create_future.add_done_callback(on_created)
        return execute_future

    def task_send(self, message: Any, no_reply: bool = False) -> Any | None:
        """
        Send a task to be performed using the communicator

        :param message: the task message
        :param no_reply: if True, this call will be fire-and-forget, i.e. no return value
        :return: the response from the remote side (if no_reply=False)
        """
        return self._communicator.task_send(message, no_reply=no_reply)


class ProcessLauncher:
    """
    Takes incoming task messages and uses them to launch processes.

    Expected format of task:

    For launch::

        {
            'task': <LAUNCH_TASK>
            'process_class': <Process class to launch>
            'args': <tuple of positional args for process constructor>
            'kwargs': <dict of keyword args for process constructor>.
            'nowait': True or False
        }

    For continue::

        {
            'task': <CONTINUE_TASK>
            'pid': <Process ID>
            'nowait': True or False
        }
    """

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop | None = None,
        persister: persistence.Persister | None = None,
        load_context: persistence.LoadSaveContext | None = None,
        loader: loaders.ObjectLoader | None = None,
    ) -> None:
        self._loop = loop
        self._persister = persister
        self._load_context = load_context if load_context is not None else persistence.LoadSaveContext()

        if loader is not None:
            self._loader = loader
            self._load_context = self._load_context.copyextend(loader=loader)
        else:
            self._loader = loaders.get_object_loader()

    async def __call__(self, communicator: kiwipy.Communicator, task: dict[str, Any]) -> PID_TYPE | ProcessResult:
        """
        Receive a task.
        :param task: The task message
        """
        task_type = task[TASK_KEY]
        if task_type == LAUNCH_TASK:
            return await self._launch(communicator, **task.get(TASK_ARGS, {}))
        if task_type == CONTINUE_TASK:
            return await self._continue(communicator, **task.get(TASK_ARGS, {}))
        if task_type == CREATE_TASK:
            return await self._create(communicator, **task.get(TASK_ARGS, {}))

        raise TaskRejected

    async def _launch(
        self,
        _communicator: kiwipy.Communicator,
        process_class: str,
        persist: bool,
        nowait: bool,
        init_args: Sequence[Any] | None = None,
        init_kwargs: dict[str, Any] | None = None,
    ) -> PID_TYPE | ProcessResult:
        """
        Launch the process

        :param _communicator: the communicator
        :param process_class: the process class to launch
        :param persist: should the process be persisted
        :param nowait: if True only return when the process finishes
        :param init_args: positional arguments to the process constructor
        :param init_kwargs: keyword arguments to the process constructor
        :return: the pid of the created process or the outputs (if nowait=False)
        """
        if persist and not self._persister:
            raise TaskRejected('Cannot persist process, no persister')

        if init_args is None:
            init_args = ()
        if init_kwargs is None:
            init_kwargs = {}

        proc_class = self._loader.load_object(process_class)
        proc = proc_class(*init_args, **init_kwargs)
        if persist and self._persister is not None:
            self._persister.save_checkpoint(proc)

        if nowait:
            # XXX: can return a reference and gracefully use task to cancel itself when the upper call stack fails
            asyncio.ensure_future(proc.step_until_terminated())  # noqa: RUF006
            return proc.pid

        await proc.step_until_terminated()

        return proc.future().result()

    async def _continue(
        self, _communicator: kiwipy.Communicator, pid: PID_TYPE, nowait: bool, tag: str | None = None
    ) -> PID_TYPE | ProcessResult:
        """
        Continue the process

        :param _communicator: the communicator
        :param pid: the pid of the process to continue
        :param nowait: if True don't wait for the process to complete
        :param tag: the checkpoint tag to continue from
        """
        if not self._persister:
            LOGGER.warning('rejecting task: cannot continue process<%d> because no persister is available', pid)
            raise TaskRejected('Cannot continue process, no persister')

        # Do not catch exceptions here, because if these operations fail, the continue task should except and bubble up
        saved_state = self._persister.load_checkpoint(pid, tag)
        proc = cast('Process', saved_state.unbundle(self._load_context))

        if nowait:
            # XXX: can return a reference and gracefully use task to cancel itself when the upper call stack fails
            asyncio.ensure_future(proc.step_until_terminated())  # noqa: RUF006
            return proc.pid

        await proc.step_until_terminated()

        return proc.future().result()

    async def _create(
        self,
        _communicator: kiwipy.Communicator,
        process_class: str,
        persist: bool,
        init_args: Sequence[Any] | None = None,
        init_kwargs: dict[str, Any] | None = None,
    ) -> PID_TYPE:
        """
        Create the process

        :param _communicator: the communicator
        :param process_class: the process class to create
        :param persist: should the process be persisted
        :param init_args: positional arguments to the process constructor
        :param init_kwargs: keyword arguments to the process constructor
        :return: the pid of the created process
        """
        if persist and not self._persister:
            raise TaskRejected('Cannot persist process, no persister')

        if init_args is None:
            init_args = ()
        if init_kwargs is None:
            init_kwargs = {}

        proc_class = self._loader.load_object(process_class)
        proc = proc_class(*init_args, **init_kwargs)
        if persist and self._persister is not None:
            self._persister.save_checkpoint(proc)

        return proc.pid
