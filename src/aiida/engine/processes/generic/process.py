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
"""The main Process module"""

import abc
import asyncio
import contextlib
import copy
import enum
import functools
import logging
import re
import sys
import time
import uuid
import warnings
from collections.abc import Awaitable, Callable, Generator, Hashable, Sequence
from contextvars import ContextVar
from types import TracebackType
from typing import (
    Any,
    Optional,
    TypeVar,
    cast,
)

import kiwipy
import yaml
from aio_pika.exceptions import ChannelInvalidStateError, ConnectionClosed

from aiida.common.extendeddicts import AttributesFrozendict
from aiida.common.lang import call_with_super_check, super_check
from aiida.common.lang import protected as protected_decorator
from aiida.common.processes import ProcessState
from aiida.engine.processes import communications as process_comms
from aiida.engine.processes import events, exceptions, persistence, state_machine
from aiida.engine.processes import states as process_states
from aiida.engine.processes.communications import FORCE_KILL_KEY, MESSAGE_TEXT_KEY, MessageBuilder, MessageType
from aiida.engine.processes.event_helper import EventHelper
from aiida.engine.processes.generic import futures, ports
from aiida.engine.processes.generic.spec import ProcessSpec
from aiida.engine.processes.greenback import run_until_complete, run_with_portal
from aiida.engine.processes.listener import ProcessListener
from aiida.engine.processes.persistence import PID_TYPE, SAVED_STATE_TYPE
from aiida.engine.processes.settings import check_protected
from aiida.engine.processes.state_machine import StateEntryFailed, StateMachine, event
from aiida.engine.utils import ensure_coroutine

protected = protected_decorator(check=check_protected)

T = TypeVar('T')

__all__: tuple[str, ...] = ()

_LOGGER = logging.getLogger(__name__)
PROCESS_STACK: ContextVar[list['Process']] = ContextVar('process stack', default=[])


class BundleKeys:
    """
    String keys used by the process to save its state in the state bundle.

    See :meth:`aiida.engine.processes.generic.process.Process.save_instance_state` and
    :meth:`aiida.engine.processes.generic.process.Process.load_instance_state`.

    """

    INPUTS_RAW = 'INPUTS_RAW'
    INPUTS_PARSED = 'INPUTS_PARSED'
    OUTPUTS = 'OUTPUTS'


class ProcessStateMachineMeta(abc.ABCMeta, state_machine.StateMachineMeta):
    pass


# Make ProcessStateMachineMeta instances (classes) YAML - able
yaml.representer.Representer.add_representer(
    ProcessStateMachineMeta,
    yaml.representer.Representer.represent_name,  # type: ignore[arg-type]
)


def ensure_not_closed(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to check that the process is not closed before running the method."""

    @functools.wraps(func)
    def func_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if self._closed:
            raise exceptions.ClosedError('Process is closed')
        return func(self, *args, **kwargs)

    return func_wrapper


@persistence.auto_persist(
    '_pid',
    '_creation_time',
    '_future',
    '_paused',
    '_status',
    '_pre_paused_status',
    '_event_helper',
)
class Process(StateMachine, persistence.Savable, metaclass=ProcessStateMachineMeta):
    """
    The Process class is the base for any unit of work in the process engine.

    A process can be in one of the following states:

    * CREATED
    * RUNNING
    * WAITING
    * FINISHED
    * EXCEPTED
    * KILLED

    as defined in the :class:`~aiida.engine.processes.states.ProcessState` enum.

    ::

                          ___
                         |   v
        CREATED (x) --- RUNNING (x) --- FINISHED (o)
                         |   ^          /
                         v   |         /
                        WAITING (x) --
                         |   ^
                          ---

        * -- EXCEPTED (o)
        * -- KILLED (o)

    * (o): terminal state
    * (x): non terminal state

    When a Process enters a state is always gets a corresponding message, e.g.
    on entering RUNNING it will receive the on_run message. These are
    always called immediately after that state is entered but before being
    executed.
    """

    # Static class stuff ######################
    _spec_class = ProcessSpec
    # Default placeholders, will be populated in init()
    _stepping = False
    _pausing: futures.CancellableAction | None = None
    _paused: persistence.SavableFuture | None = None
    _killing: futures.CancellableAction | None = None
    _interrupt_action: futures.CancellableAction | None = None
    _closed = False
    _cleanups: list[Callable[[], None]] | None = None

    __called: bool = False

    @classmethod
    def current(cls) -> Optional['Process']:
        """
        Get the currently running process i.e. the one at the top of the stack

        :return: the currently running process

        """
        if PROCESS_STACK.get():
            return PROCESS_STACK.get()[-1]

        return None

    @classmethod
    def get_states(cls) -> Sequence[type[process_states.State]]:
        """Return all allowed states of the process."""
        state_classes = cls.get_state_classes()
        return (
            state_classes[ProcessState.CREATED],
            *[state for state in state_classes.values() if state.LABEL != ProcessState.CREATED],
        )

    @classmethod
    def get_state_classes(cls) -> dict[Hashable, type[process_states.State]]:
        # A mapping of the State constants to the corresponding state class
        return {
            ProcessState.CREATED: process_states.Created,
            ProcessState.RUNNING: process_states.Running,
            ProcessState.WAITING: process_states.Waiting,
            ProcessState.FINISHED: process_states.Finished,
            ProcessState.EXCEPTED: process_states.Excepted,
            ProcessState.KILLED: process_states.Killed,
        }

    @classmethod
    def spec(cls) -> ProcessSpec:
        try:
            return cls.__getattribute__(cls, '_spec')
        except AttributeError:
            try:
                cls._spec: ProcessSpec = cls._spec_class()  # type: ignore[attr-defined, misc]
                cls.__called: bool = False  # type: ignore[misc]
                cls.define(cls._spec)  # type: ignore[attr-defined]
                assert cls.__called, (
                    f'Process.define() was not called by {cls}\nHint: Did you forget to call the superclass method in '
                    'your define? Try: super().define(spec)'
                )
                return cls._spec  # type: ignore[attr-defined]
            except Exception:
                del cls._spec  # type: ignore[attr-defined]
                cls.__called = False
                raise

    @classmethod
    def get_name(cls) -> str:
        """Return the process class name."""
        return cls.__name__

    @classmethod
    def define(cls, _spec: ProcessSpec) -> None:
        """Define the specification of the process.

        Normally should be overridden by subclasses.
        """
        cls.__called = True

    @classmethod
    def get_description(cls) -> dict[str, Any]:
        """
        Get a human readable description of what this :class:`Process` does.

        :return: The description.

        """
        description: dict[str, Any] = {}

        if cls.__doc__:
            description['description'] = cls.__doc__.strip()

        spec_description = cls.spec().get_description()
        if spec_description:
            description['spec'] = spec_description

        return description

    @classmethod
    def recreate_from(
        cls,
        saved_state: SAVED_STATE_TYPE,
        load_context: persistence.LoadSaveContext | None = None,
    ) -> 'Process':
        """
        Recreate a process from a saved state, passing any positional and
        keyword arguments on to load_instance_state

        :param saved_state: The saved state to load from
        :param load_context: The load context to use
        :return: An instance of the object with its state loaded from the save state.

        """
        process = cast(Process, super().recreate_from(saved_state, load_context))
        call_with_super_check(process.init)
        return process

    def __init__(
        self,
        inputs: dict | None = None,
        pid: PID_TYPE | None = None,
        logger: logging.Logger | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
        communicator: kiwipy.Communicator | None = None,
    ) -> None:
        """
        The signature of the constructor should not be changed by subclassing processes.

        :param inputs: A dictionary of the process inputs
        :param pid: The process ID, can be manually set, if not a unique pid will be chosen
        :param logger: An optional logger for the process to use
        :param loop: The event loop
        :param communicator: The (optional) communicator

        """
        super().__init__()

        # Don't allow the spec to be changed anymore
        self.spec().seal()

        self._loop = loop if loop is not None else events.get_or_create_event_loop()

        self._setup_event_hooks()

        self._status: str | None = None  # May hold a current status message
        self._pre_paused_status: str | None = (
            None  # Save status when a pause message replaces it, such that it can be restored
        )
        self._paused = None

        # Input/output
        self._raw_inputs = None if inputs is None else AttributesFrozendict(inputs)
        self._pid = pid
        self._parsed_inputs: AttributesFrozendict | None = None
        self._outputs: dict[str, Any] = {}
        self._uuid: uuid.UUID | None = None
        self._creation_time: float | None = None

        # Runtime variables
        self._future = persistence.SavableFuture(loop=self._loop)
        self._event_helper = EventHelper(ProcessListener)
        self._logger = logger
        self._communicator = communicator
        self._tasks: set[asyncio.Task[Any]] = set()

    @super_check
    def init(self) -> None:
        """Common initialisation logic, after create or load, goes here.

        This method is called in :class:`aiida.engine.processes.state_machine.StateMachineMeta`
        """
        self._cleanups = []  # a list of functions to be ran on terminated

        if self._communicator is not None:
            try:
                identifier = self._communicator.add_rpc_subscriber(self.message_receive, identifier=str(self.pid))
                self.add_cleanup(functools.partial(self._communicator.remove_rpc_subscriber, identifier))
            except kiwipy.TimeoutError:
                self.logger.exception('Process<%s>: failed to register as an RPC subscriber', self.pid)

            try:
                # filter out state change broadcasts
                subscriber = kiwipy.BroadcastFilter(self.broadcast_receive, subject=re.compile(r'^(?!state_changed).*'))
                identifier = self._communicator.add_broadcast_subscriber(subscriber, identifier=str(self.pid))
                self.add_cleanup(functools.partial(self._communicator.remove_broadcast_subscriber, identifier))
            except kiwipy.TimeoutError:
                self.logger.exception(
                    'Process<%s>: failed to register as a broadcast subscriber',
                    self.pid,
                )

        if not self._future.done():

            def try_killing(future: futures.Future) -> None:
                if future.cancelled():
                    if not self.kill('Killed by future being cancelled'):
                        self.logger.warning(
                            'Process<%s>: Failed to kill process on future cancel',
                            self.pid,
                        )

            self._future.add_done_callback(try_killing)

    def _setup_event_hooks(self) -> None:
        """Set the event hooks to process, when it is created or loaded(recreated)."""
        event_hooks = {
            state_machine.StateEventHook.ENTERING_STATE: lambda _s, _h, state: self.on_entering(
                cast(process_states.State, state)
            ),
            state_machine.StateEventHook.ENTERED_STATE: lambda _s, _h, from_state: self.on_entered(
                cast(process_states.State | None, from_state)
            ),
            state_machine.StateEventHook.EXITING_STATE: lambda _s, _h, _state: self.on_exiting(),
        }
        for hook, callback in event_hooks.items():
            self.add_state_event_callback(hook, callback)

    @property
    def creation_time(self) -> float | None:
        """
        The creation time of this Process as returned by time.time() when instantiated
        :return: The creation time
        """
        return self._creation_time

    @property
    def pid(self) -> PID_TYPE | None:
        """Return the pid of the process."""
        return self._pid

    @property
    def uuid(self) -> uuid.UUID | None:
        """Return the UUID of the process"""
        return self._uuid

    @property
    def raw_inputs(self) -> AttributesFrozendict | None:
        """The `AttributesFrozendict` of inputs (if not None)."""
        return self._raw_inputs

    @property
    def inputs(self) -> AttributesFrozendict | None:
        """Return the parsed inputs."""
        return self._parsed_inputs

    @property
    def outputs(self) -> dict[str, Any]:
        """
        Get the current outputs emitted by the Process.  These may grow over
        time as the process runs.

        :return: A mapping of {output_port: value} outputs

        """
        return self._outputs

    @property
    def logger(self) -> logging.Logger:
        """Return the logger for this class.

        If not set, return the default logger.

        :return: The logger.

        """
        if self._logger is not None:
            return self._logger

        return _LOGGER

    @property
    def status(self) -> str | None:
        """Return the status massage of the process."""
        return self._status

    def set_status(self, status: str | None) -> None:
        """Set the status message of the process."""
        self._status = status

    @property
    def paused(self) -> bool:
        """Return whether the process was being paused."""
        return self._paused is not None

    def future(self) -> persistence.SavableFuture:
        """Return a savable future representing an eventual result of an asynchronous operation.

        The result is set at the terminal state.
        """
        return self._future

    @ensure_not_closed
    def launch(
        self,
        process_class: type['Process'],
        inputs: dict | None = None,
        pid: PID_TYPE | None = None,
        logger: logging.Logger | None = None,
    ) -> 'Process':
        """Start running the nested process.

        The process is started asynchronously, without blocking other task in the event loop.
        """
        process = process_class(
            inputs=inputs,
            pid=pid,
            logger=logger,
            loop=self.loop,
            communicator=self._communicator,
        )
        task = self.loop.create_task(process.step_until_terminated())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return process

    # region State introspection methods

    def has_terminated(self) -> bool:
        """Return whether the process was terminated."""
        return self._state.is_terminal()

    def result(self) -> Any:
        """
        Get the result from the process if it is finished.
        If the process was killed then a KilledError will be raise.
        If the process has excepted then the failing exception will be raised.
        If in any other state this will raise an InvalidStateError.
        :return: The result of the process
        """
        if isinstance(self._state, process_states.Finished):
            return self._state.result
        if isinstance(self._state, process_states.Killed):
            raise exceptions.KilledError(self._state.msg)
        if isinstance(self._state, process_states.Excepted):
            raise (self._state.exception or Exception('process excepted'))

        raise exceptions.InvalidStateError

    def successful(self) -> bool:
        """
        Returns whether the result of the process is considered successful
        Will raise if the process is not in the FINISHED state
        """
        try:
            return self._state.successful  # type: ignore[attr-defined]
        except AttributeError as exception:
            raise exceptions.InvalidStateError('process is not in the finished state') from exception

    @property
    def is_successful(self) -> bool:
        """Return whether the result of the process is considered successful.

        :return: boolean, True if the process is in `Finished` state with `successful` attribute set to `True`
        """
        try:
            return self._state.successful  # type: ignore[attr-defined]
        except AttributeError:
            return False

    def killed(self) -> bool:
        """Return whether the process is killed."""
        return self.state == ProcessState.KILLED

    def killed_msg(self) -> MessageType | None:
        """Return the killed message."""
        if isinstance(self._state, process_states.Killed):
            return self._state.msg

        raise exceptions.InvalidStateError('Has not been killed')

    def exception(self) -> BaseException | None:
        """Return exception, if the process is terminated in excepted state."""
        if isinstance(self._state, process_states.Excepted):
            return self._state.exception

        return None

    @property
    def is_excepted(self) -> bool:
        """Return whether the process excepted.

        :return: boolean, True if the process is in ``EXCEPTED`` state.
        """
        return self.state == ProcessState.EXCEPTED

    def done(self) -> bool:
        """Return True if the call was successfully killed or finished running.

        .. deprecated:: 0.18.6
            Use the `has_terminated` method instead
        """
        warnings.warn('method is deprecated, use `has_terminated` instead', DeprecationWarning)
        return self._state.is_terminal()

    # endregion

    # region loop methods

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Return the event loop of the process."""
        return self._loop

    def call_soon(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> events.ProcessCallback:
        """
        Schedule a callback to what is considered an internal process function
        (this needn't be a method).
        If it raises an exception it will cause the process to fail.
        """
        args = (callback,) + args
        handle = events.ProcessCallback(self, self._run_task, args, kwargs)
        task = self.loop.create_task(handle.run())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return handle

    def callback_excepted(
        self,
        _callback: Callable[..., Any],
        exception: BaseException | None,
        trace: TracebackType | None,
    ) -> None:
        if self.state != ProcessState.EXCEPTED:
            self.fail(exception, trace)

    @contextlib.contextmanager
    def _process_scope(self) -> Generator[None, None, None]:
        """
        This context manager function is used to make sure the process stack is correct
        meaning that globally someone can ask for Process.current() to get the last process
        that is on the call stack.
        """
        stack_copy = PROCESS_STACK.get().copy()
        stack_copy.append(self)
        PROCESS_STACK.set(stack_copy)
        try:
            yield None
        finally:
            assert Process.current() is self, (
                'Somehow, the process at the top of the stack is not me, but another process! '
                f'({self} != {Process.current()})'
            )
            stack_copy = PROCESS_STACK.get().copy()
            stack_copy.pop()
            PROCESS_STACK.set(stack_copy)

    async def _run_task(self, callback: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        This method should be used to run all Process related functions and coroutines.
        If there is an exception the process will enter the EXCEPTED state.

        :param callback: A function or coroutine
        :param args: Optional positional arguments passed to fn
        :param kwargs:  Optional keyword arguments passed to fn
        :return: The value as returned by fn
        """
        # Make sure execute is a coroutine
        coro = ensure_coroutine(callback)
        with self._process_scope():
            result = await coro(*args, **kwargs)
        return result

    # endregion

    # region Persistence

    def save_instance_state(
        self,
        out_state: SAVED_STATE_TYPE,
        save_context: persistence.LoadSaveContext,
    ) -> None:
        """
        Ask the process to save its current instance state.

        :param out_state: A bundle to save the state to
        :param save_context: The save context
        """
        super().save_instance_state(out_state, save_context)

        out_state['_state'] = self._state.save()

        # Inputs/outputs
        if self.raw_inputs is not None:
            out_state[BundleKeys.INPUTS_RAW] = self.encode_input_args(self.raw_inputs)

        if self.inputs is not None:
            out_state[BundleKeys.INPUTS_PARSED] = self.encode_input_args(self.inputs)

        if self.outputs:
            out_state[BundleKeys.OUTPUTS] = self.encode_input_args(self.outputs)

    @protected
    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        """Load the process from its saved instance state.

        :param saved_state: A bundle to load the state from
        :param load_context: The load context

        """
        # First make sure the state machine constructor is called
        super().__init__()

        self._setup_event_hooks()

        if 'loop' in load_context:
            self._loop = load_context.loop
        else:
            self._loop = events.get_or_create_event_loop()

        # Runtime variables, set initial states
        self._future = persistence.SavableFuture(loop=self._loop)
        self._event_helper = EventHelper(ProcessListener)
        self._logger = None
        self._communicator = None
        self._tasks = set()

        self._state: process_states.State = self.recreate_state(saved_state['_state'])

        if 'communicator' in load_context:
            self._communicator = load_context.communicator

        if 'logger' in load_context:
            self._logger = load_context.logger

        # Need to call this here as things downstream may rely on us having the runtime variable above
        super().load_instance_state(saved_state, load_context)

        # Inputs/outputs
        try:
            decoded = self.decode_input_args(saved_state[BundleKeys.INPUTS_RAW])
            self._raw_inputs = AttributesFrozendict(decoded)
        except KeyError:
            self._raw_inputs = None

        try:
            decoded = self.decode_input_args(saved_state[BundleKeys.INPUTS_PARSED])
            self._parsed_inputs = AttributesFrozendict(decoded)
        except KeyError:
            self._parsed_inputs = None

        try:
            decoded = self.decode_input_args(saved_state[BundleKeys.OUTPUTS])
            self._outputs = decoded
        except KeyError:
            self._outputs = {}

    # endregion

    def add_process_listener(self, listener: ProcessListener) -> None:
        """Add a process listener to the process.

        The listener defines the actions to take when the process is triggering
        the specific state condition.

        """
        assert listener != self, 'Cannot listen to yourself!'  # type: ignore[comparison-overlap]
        self._event_helper.add_listener(listener)

    def remove_process_listener(self, listener: ProcessListener) -> None:
        """Remove a process listener from the process."""
        self._event_helper.remove_listener(listener)

    @protected
    def set_logger(self, logger: logging.Logger) -> None:
        """Set the logger of the process."""
        self._logger = logger

    @protected
    def log_with_pid(self, level: int, msg: str) -> None:
        """Log the message with the process pid."""
        self.logger.log(level, '%s: %s', self.pid, msg)

    # region Events

    def on_entering(self, state: process_states.State) -> None:
        # Map these onto direct functions that the subclass can implement
        state_label = state.LABEL
        if state_label == ProcessState.CREATED:
            call_with_super_check(self.on_create)
        elif state_label == ProcessState.RUNNING:
            call_with_super_check(self.on_run)
        elif state_label == ProcessState.WAITING:
            call_with_super_check(self.on_wait, state.data)  # type: ignore[attr-defined]
        elif state_label == ProcessState.FINISHED:
            call_with_super_check(self.on_finish, state.result, state.successful)  # type: ignore[attr-defined]
        elif state_label == ProcessState.KILLED:
            call_with_super_check(self.on_kill, state.msg)  # type: ignore[attr-defined]
        elif state_label == ProcessState.EXCEPTED:
            call_with_super_check(self.on_except, state.get_exc_info())  # type: ignore[attr-defined]

    def on_entered(self, from_state: process_states.State | None) -> None:
        # Map these onto direct functions that the subclass can implement
        state_label = self._state.LABEL
        if state_label == ProcessState.RUNNING:
            call_with_super_check(self.on_running)
        elif state_label == ProcessState.WAITING:
            call_with_super_check(self.on_waiting)
        elif state_label == ProcessState.FINISHED:
            call_with_super_check(self.on_finished)
        elif state_label == ProcessState.EXCEPTED:
            call_with_super_check(self.on_excepted)
        elif state_label == ProcessState.KILLED:
            call_with_super_check(self.on_killed)

        if self._communicator and isinstance(self.state, enum.Enum):
            from_label = cast(enum.Enum, from_state.LABEL).value if from_state is not None else None
            subject = f'state_changed.{from_label}.{self.state.value}'
            self.logger.info('Process<%s>: Broadcasting state change: %s', self.pid, subject)
            try:
                self._communicator.broadcast_send(body=None, sender=self.pid, subject=subject)
            except (ConnectionClosed, ChannelInvalidStateError):
                message = 'Process<%s>: no connection available to broadcast state change from %s to %s'
                self.logger.warning(message, self.pid, from_label, self.state.value)
            except kiwipy.TimeoutError:
                message = 'Process<%s>: sending broadcast of state change from %s to %s timed out'
                self.logger.warning(message, self.pid, from_label, self.state.value)

    def on_exiting(self) -> None:
        state = self.state
        if state == ProcessState.WAITING:
            call_with_super_check(self.on_exit_waiting)
        elif state == ProcessState.RUNNING:
            call_with_super_check(self.on_exit_running)

    @super_check
    def on_create(self) -> None:
        """Entering the CREATED state."""
        self._creation_time = time.time()

        def recursively_copy_dictionaries(value: Any) -> Any:
            """Recursively copy the mapping but only create copies of the dictionaries not the values."""
            if isinstance(value, dict):
                return {key: recursively_copy_dictionaries(subvalue) for key, subvalue in value.items()}
            return value

        # This will parse the inputs with respect to the input portnamespace of the spec and validate them. The
        # ``pre_process`` method of the inputs port namespace modifies its argument in place, and since the
        # ``_raw_inputs`` should not be modified, we pass a clone of it. Note that we only need a clone of the nested
        # dictionaries, so we don't use ``copy.deepcopy`` (which might seem like the obvious choice) as that will also
        # create a clone of the values, which we don't want.
        raw_inputs = recursively_copy_dictionaries(dict(self._raw_inputs)) if self._raw_inputs else {}
        self._parsed_inputs = self.spec().inputs.pre_process(raw_inputs)
        result = self.spec().inputs.validate(self._parsed_inputs)

        if result is not None:
            raise ValueError(result)

        # Set up a process ID
        self._uuid = uuid.uuid4()
        if self._pid is None:
            self._pid = self._uuid

    @super_check
    def on_exit_running(self) -> None:
        """Exiting the RUNNING state."""

    @super_check
    def on_exit_waiting(self) -> None:
        """Exiting the WAITING state."""

    @super_check
    def on_run(self) -> None:
        """Entering the RUNNING state."""

    @super_check
    def on_running(self) -> None:
        """Entered the RUNNING state."""
        self._fire_event(ProcessListener.on_process_running)

    def on_output_emitting(self, output_port: str, value: Any) -> None:
        """Output is about to be emitted."""

    def on_output_emitted(self, output_port: str, value: Any, dynamic: bool) -> None:
        self._event_helper.fire_event(ProcessListener.on_output_emitted, self, output_port, value, dynamic)

    @super_check
    def on_wait(self, awaitables: Sequence[Awaitable]) -> None:
        """Entering the WAITING state."""

    @super_check
    def on_waiting(self) -> None:
        """Entered the WAITING state."""
        self._fire_event(ProcessListener.on_process_waiting)

    @super_check
    def on_pausing(self, msg: str | None = None) -> None:
        """The process is being paused."""

    @super_check
    def on_paused(self, msg: str | None = None) -> None:
        """The process was paused."""
        self._pausing = None

        # Create a future to represent the duration of the paused state
        self._paused = persistence.SavableFuture(loop=self._loop)

        # Save the current status and potentially overwrite it with the passed message
        self._pre_paused_status = self.status
        if msg is not None:
            self.set_status(msg)

        self._fire_event(ProcessListener.on_process_paused)

    @super_check
    def on_playing(self) -> None:
        """The process was played."""
        # Done being paused
        if self._paused is not None:
            self._paused.set_result(True)
        self._paused = None

        self.set_status(self._pre_paused_status)
        self._pre_paused_status = None

        self._fire_event(ProcessListener.on_process_played)

    @super_check
    def on_finish(self, result: Any, successful: bool) -> None:
        """Entering the FINISHED state."""
        if successful:
            validation_error = self.spec().outputs.validate(self.outputs)
            if validation_error:
                state_cls = self.get_states_map()[ProcessState.FINISHED]
                finished_state = state_cls(self, result=result, successful=False)
                raise StateEntryFailed(finished_state)

        self.future().set_result(self.outputs)

    @super_check
    def on_finished(self) -> None:
        """Entered the FINISHED state."""
        self._fire_event(ProcessListener.on_process_finished, self.future().result())

    @super_check
    def on_except(self, exc_info: tuple[Any, Exception, TracebackType]) -> None:
        """Entering the EXCEPTED state."""
        exception = exc_info[1]
        exception.__traceback__ = exc_info[2]

        # It is possible that we already got into a finished state and the future result was set, in which case, we
        # should reset it before setting the exception or else ``asyncio`` will raise an exception.
        future = self.future()

        if future.done():
            self._future = persistence.SavableFuture(loop=self._loop)
        self.future().set_exception(exception)

    @super_check
    def on_excepted(self) -> None:
        """Entered the EXCEPTED state."""
        self._fire_event(ProcessListener.on_process_excepted, str(self.future().exception()))

    @super_check
    def on_kill(self, msg: MessageType | None) -> None:
        """Entering the KILLED state."""
        if msg is None:
            msg_txt = ''
        else:
            msg_txt = msg[MESSAGE_TEXT_KEY] or ''

        self.set_status(msg_txt)
        self.future().set_exception(exceptions.KilledError(msg_txt))

    @super_check
    def on_killed(self) -> None:
        """Entered the KILLED state."""
        self._killing = None
        self.future().exception()  # exception must be retrieved
        self._fire_event(ProcessListener.on_process_killed, self.killed_msg())

    def on_terminated(self) -> None:
        """Call when a terminal state is reached."""
        super().on_terminated()
        self.close()

    @super_check
    def on_close(self) -> None:
        """
        Called when the Process is being closed an will not be ran anymore.  This is an opportunity
        to free any runtime resources
        """
        try:
            for cleanup in self._cleanups or []:
                try:
                    cleanup()
                except Exception:
                    self.logger.exception('Process<%s>: Exception calling cleanup method %s', self.pid, cleanup)
            self._cleanups = None
        finally:
            self._event_callbacks = {}
            self._closed = True

    def _fire_event(self, evt: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self._event_helper.fire_event(evt, self, *args, **kwargs)

    # endregion

    # region Communication

    def message_receive(self, _comm: kiwipy.Communicator, msg: MessageType) -> Any:
        """
        Coroutine called when the process receives a message from the communicator

        :param _comm: the communicator that sent the message
        :param msg: the message
        :return: the outcome of processing the message, the return value will be sent back as a response to the sender
        """
        self.logger.debug(
            "Process<%s>: received RPC message with communicator '%s': %r",
            self.pid,
            _comm,
            msg,
        )

        intent = msg[process_comms.INTENT_KEY]

        if intent == process_comms.Intent.PLAY:
            return self._schedule_rpc(self.play)
        if intent == process_comms.Intent.PAUSE:
            return self._schedule_rpc(self.pause, msg_text=msg.get(process_comms.MESSAGE_TEXT_KEY, None))
        if intent == process_comms.Intent.KILL:
            default_message = MessageBuilder.kill()
            text = msg.get(process_comms.MESSAGE_TEXT_KEY, default_message.get(MESSAGE_TEXT_KEY))
            force_kill = msg.get(process_comms.FORCE_KILL_KEY, default_message.get(FORCE_KILL_KEY))
            return self._schedule_rpc(self.kill, msg_text=text, force_kill=force_kill)
        if intent == process_comms.Intent.STATUS:
            status_info: dict[str, Any] = {}
            self.get_status_info(status_info)
            return status_info

        # Didn't match any known intents
        raise RuntimeError('Unknown intent')

    def broadcast_receive(
        self, _comm: kiwipy.Communicator, msg: MessageType, sender: Any, subject: Any, correlation_id: Any
    ) -> kiwipy.Future | None:
        """
        Coroutine called when the process receives a message from the communicator

        :param _comm: the communicator that sent the message
        :param msg: the message
        """

        self.logger.debug(
            "Process<%s>: received broadcast message '%s' with communicator '%s': %r",
            self.pid,
            subject,
            _comm,
            msg,
        )

        # If we get a message we recognise then action it, otherwise ignore
        if subject == process_comms.Intent.PLAY:
            return self._schedule_rpc(self.play)
        if subject == process_comms.Intent.PAUSE:
            return self._schedule_rpc(self.pause, msg_text=msg.get(process_comms.MESSAGE_TEXT_KEY, None))
        if subject == process_comms.Intent.KILL:
            return self._schedule_rpc(self.kill, msg_text=msg.get(process_comms.MESSAGE_TEXT_KEY, None))
        return None

    def _schedule_rpc(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> kiwipy.Future:
        """
        Schedule a call to a callback as a result of an RPC communication call, this will return
        a future that resolves to the final result (even after one or more layer of futures being
        returned) of the callback.

        The callback will be scheduled at the working
        thread where the process event loop runs.

        :param callback: the callback function or coroutine
        :param args: the positional arguments to the callback
        :param kwargs: the keyword arguments to the callback
        :return: a kiwi future that resolves to the outcome of the callback

        """
        kiwi_future = kiwipy.Future()

        async def run_callback() -> None:
            with kiwipy.capture_exceptions(kiwi_future):
                try:
                    result = await run_with_portal(callback, *args, **kwargs)
                except Exception:
                    self.logger.exception(
                        "Process<%s>: error invoking callback '%s'", self.pid, getattr(callback, '__name__', callback)
                    )
                    raise

                while asyncio.isfuture(result):
                    result = await result

                kiwi_future.set_result(result)

        # Schedule the task and give back a kiwi future
        asyncio.run_coroutine_threadsafe(run_callback(), self.loop)

        return kiwi_future

    # endregion

    @ensure_not_closed
    def add_cleanup(self, cleanup: Callable[[], None]) -> None:
        """Add callback, which will be run when the process is being closed."""
        assert self._cleanups is not None
        self._cleanups.append(cleanup)

    def close(self) -> None:
        """
        Calling this method indicates that this process should not ran anymore and will trigger
        any runtime resources (such as the communicator connection) to be cleaned up.  The state
        of the process will still be accessible.

        It is safe to call this method multiple times.
        """
        if self._closed:
            return

        call_with_super_check(self.on_close)

    # region State related methods

    def transition_failed(
        self,
        initial_state: Hashable,
        final_state: Hashable,
        exception: Exception,
        trace: TracebackType,
    ) -> None:
        # If we are creating, then reraise instead of failing.
        if final_state == ProcessState.CREATED:
            raise exception.with_traceback(trace)

        new_state = self._create_state_instance(ProcessState.EXCEPTED, exception=exception, trace_back=trace)
        self.transition_to(new_state)

    def pause(self, msg_text: str | None = None) -> bool | futures.CancellableAction:
        """Pause the process.

        :param msg: an optional message to set as the status. The current status will be saved in the private
            `_pre_paused_status attribute`, such that it can be restored when the process is played again.

        :return: False if process is already terminated,
                 True if already paused or pausing,
                 a `CancellableAction` to pause if the process was running steps
        """
        if self.has_terminated():
            return False

        if self.paused:
            # Already paused
            return True

        if self._pausing is not None:
            # Already pausing
            return self._pausing

        if self._stepping:
            # Ask the step function to pause by setting this flag and giving the
            # caller back a future
            interrupt_exception = process_states.PauseInterruption(msg_text)
            self._set_interrupt_action_from_exception(interrupt_exception)
            self._pausing = self._interrupt_action
            # Try to interrupt the state
            self._state.interrupt(interrupt_exception)
            return cast(futures.CancellableAction, self._interrupt_action)

        msg = MessageBuilder.pause(msg_text)
        return self._do_pause(state_msg=msg)

    def _do_pause(self, state_msg: MessageType | None, next_state: process_states.State | None = None) -> bool:
        """Carry out the pause procedure, optionally transitioning to the next state first"""
        try:
            if next_state is not None:
                self.transition_to(next_state)

            if state_msg is None:
                msg_text = ''
            else:
                msg_text = state_msg[MESSAGE_TEXT_KEY]

            call_with_super_check(self.on_pausing, msg_text)
            call_with_super_check(self.on_paused, msg_text)
        finally:
            self._pausing = None

        return True

    def _create_interrupt_action(self, exception: process_states.Interruption) -> futures.CancellableAction:
        """
        Create an interrupt action from the corresponding interrupt exception

        :param exception: The interrupt exception
        :return: The interrupt action

        """
        if isinstance(exception, process_states.PauseInterruption):
            do_pause = functools.partial(self._do_pause, exception.msg)
            return futures.CancellableAction(do_pause, cookie=exception, loop=self.loop)

        if isinstance(exception, process_states.KillInterruption):

            def do_kill(_next_state: process_states.State) -> Any:
                try:
                    new_state = self._create_state_instance(ProcessState.KILLED, msg=exception.msg)
                    self.transition_to(new_state)
                    return True
                finally:
                    self._killing = None

            return futures.CancellableAction(do_kill, cookie=exception, loop=self.loop)

        raise ValueError(f"Got unknown interruption type '{type(exception)}'")

    def _set_interrupt_action(self, new_action: futures.CancellableAction | None) -> None:
        """
        Set the interrupt action cancelling the current one if it exists
        :param new_action: The new interrupt action to set
        """
        if self._interrupt_action is not None:
            self._interrupt_action.cancel()
        self._interrupt_action = new_action

    def _set_interrupt_action_from_exception(self, interrupt_exception: process_states.Interruption) -> None:
        """Set an interrupt action from the corresponding interrupt exception"""
        action = self._create_interrupt_action(interrupt_exception)
        self._set_interrupt_action(action)

    def play(self) -> bool:
        """
        Play a process. Returns True if after this call the process is playing, False otherwise

        :return: True if playing, False otherwise
        """
        if not self.paused:
            if self._pausing is not None:
                # Not going to pause after all
                self._pausing.cancel()
                self._pausing = None
                self._set_interrupt_action(None)
            return True

        call_with_super_check(self.on_playing)
        return True

    @event(from_states=process_states.Waiting)
    def resume(self, *args: Any) -> None:
        """Start running the process again."""
        return self._state.resume(*args)  # type: ignore[attr-defined]

    @event(to_states=process_states.Excepted)
    def fail(self, exception: BaseException | None, trace_back: TracebackType | None) -> None:
        """
        Fail the process in response to an exception
        :param exception: The exception that caused the failure
        :param trace_back: Optional exception traceback
        """
        new_state = self._create_state_instance(ProcessState.EXCEPTED, exception=exception, trace_back=trace_back)
        self.transition_to(new_state)

    def kill(self, msg_text: str | None = None, force_kill: bool = False) -> bool | asyncio.Future:
        """
        Kill the process
        :param msg: An optional kill message
        """
        if self.state == ProcessState.KILLED:
            # Already killed
            return True

        if self.has_terminated():
            # Can't kill
            return False

        if self._killing:
            self._killing.cancel()

        if force_kill:
            msg = MessageBuilder.kill(msg_text, force_kill=force_kill)
            new_state = self._create_state_instance(ProcessState.KILLED, msg=msg)
            self.transition_to(new_state)

            return True

        if self._stepping:
            # Ask the step function to pause by setting this flag and giving the
            # caller back a future
            interrupt_exception = process_states.KillInterruption(msg_text, force_kill)
            self._set_interrupt_action_from_exception(interrupt_exception)
            self._killing = self._interrupt_action
            self._state.interrupt(interrupt_exception)
            return cast(futures.CancellableAction, self._interrupt_action)

        msg = MessageBuilder.kill(text=msg_text, force_kill=force_kill)
        new_state = self._create_state_instance(ProcessState.KILLED, msg=msg)
        self.transition_to(new_state)
        return True

    @property
    def is_killing(self) -> bool:
        """Return if the process is already being killed."""
        return self._killing is not None

    # endregion

    def create_initial_state(self) -> process_states.State:
        """This method is here to override its superclass.

        Automatically enter the CREATED state when the process is created.

        :return: A Created state
        """
        return cast(
            process_states.State,
            self.get_state_class(ProcessState.CREATED)(self, self.run),
        )

    def recreate_state(self, saved_state: persistence.Bundle) -> process_states.State:
        """
        Create a state object from a saved state

        :param saved_state: The saved state
        :return: An instance of the object with its state loaded from the save state.
        """
        load_context = persistence.LoadSaveContext(process=self)
        return cast(process_states.State, persistence.Savable.load(saved_state, load_context))

    # endregion

    # region Execution related methods

    async def run(self) -> Any:
        """This function will be run when the process is triggered.
        It should be overridden by a subclass.
        """

    @ensure_not_closed
    def execute(self) -> dict[str, Any] | None:
        """Execute the process synchronously.

        :return: None if not terminated, otherwise `self.outputs`
        """
        if self.has_terminated():
            return self.future().result()

        run_until_complete(self.loop, self.step_until_terminated())

        return self.future().result()

    @ensure_not_closed
    async def step(self) -> None:
        """Run a step.

        The step is run synchronously with steps in its own process,
        and asynchronously with steps in other processes.

        The execute function running in this method is dependent on the state of the process.

        """
        assert not self.has_terminated(), 'Cannot step, already terminated'

        if self.paused and self._paused is not None:
            await self._paused

        try:
            self._stepping = True
            next_state = None
            try:
                next_state = await self._run_task(self._state.execute)
            except process_states.Interruption as exception:
                # If the interruption was caused by a call to a Process method then there should
                # be an interrupt action ready to be executed, so just check if the cookie matches
                # that of the exception i.e. if it is the _same_ interruption.  If not cancel and
                # build the interrupt action below
                if self._interrupt_action is not None:
                    if self._interrupt_action.cookie is not exception:
                        self._set_interrupt_action_from_exception(exception)
                else:
                    self._set_interrupt_action_from_exception(exception)

            except KeyboardInterrupt:
                raise
            except Exception:
                # Overwrite the next state to go to excepted directly
                next_state = self.create_state(ProcessState.EXCEPTED, *sys.exc_info()[1:])
                self._set_interrupt_action(None)

            if self._interrupt_action and not self._interrupt_action.cancelled():
                self._interrupt_action.run(next_state)
            else:
                # Everything nominal so transition to the next state
                self.transition_to(next_state)

        finally:
            self._stepping = False
            self._set_interrupt_action(None)

    async def step_until_terminated(self) -> None:
        """If the process has not terminated,
        run the current step and wait until the step finished.

        This is the function run by the event loop (not ``step``).

        """
        while not self.has_terminated():
            await self.step()

    # endregion

    @ensure_not_closed
    @protected
    def out(self, output_port: str, value: Any) -> None:
        """
        Record an output value for a specific output port. If the output port matches an
        explicitly defined Port it will be validated against that. If not it will be validated
        against the PortNamespace, which means it will be checked for dynamicity and whether
        the type of the value is valid

        Emitting an output never changes the process specification. The specification is built once per process
        class and shared by all its instances, so a port added here would validate the outputs of every later
        instance of that class.

        :param output_port: the name of the output port, can be namespaced
        :param value: the value for the output port
        :raises: ValueError if the output value is not validated against the port
        """
        self.on_output_emitting(output_port, value)

        namespace_separator = self.spec().namespace_separator

        output_path = output_port.split(namespace_separator)
        port_name = output_path[-1]
        namespace = output_path[:-1]

        unresolved_path = output_path.copy()
        port_namespace = self.spec().outputs

        # For output_path == ['sub', 'a', 'b'], where only sub is declared, this leaves
        # port_namespace as sub and unresolved_path as ['a', 'b'].
        while len(unresolved_path) > 1:
            namespace_name = unresolved_path[0]

            if namespace_name not in port_namespace:
                if not port_namespace.dynamic:
                    raise ValueError(
                        f"port '{namespace_name}' does not exist in port namespace '{port_namespace.name}'"
                    )
                break

            port = port_namespace[namespace_name]
            if not isinstance(port, ports.PortNamespace):
                raise ValueError(
                    f"port '{namespace_name}' in port namespace '{port_namespace.name}' is not a namespace"
                )

            port_namespace = port
            unresolved_path.pop(0)

        port_key = namespace_separator.join(unresolved_path)
        is_declared_output = port_key in port_namespace
        if is_declared_output:
            validation_error = port_namespace[port_key].validate(value)
            is_dynamic_output = False
        else:
            # potentially dynamic output
            validation_error = port_namespace.validate_dynamic_ports({port_key: value})
            is_dynamic_output = True

        if validation_error:
            msg = f"Error validating output '{value}' for port '{validation_error.port}': {validation_error.message}"
            raise ValueError(msg)

        output_namespace = self._outputs
        for sub_space in namespace:
            output_namespace = output_namespace.setdefault(sub_space, {})

        output_namespace[port_name] = value
        self.on_output_emitted(output_port, value, is_dynamic_output)

    @protected
    def encode_input_args(self, inputs: Any) -> Any:
        """
        Encode input arguments such that they may be saved in a :class:`aiida.engine.processes.persistence.Bundle`.
        The encoded inputs should contain no reference to the inputs that were passed in.
        This often will mean making a deepcopy of the input dictionary.

        :param inputs: A mapping of the inputs as passed to the process
        :return: The encoded inputs
        """
        return copy.deepcopy(inputs)

    @protected
    def decode_input_args(self, encoded: Any) -> Any:
        """
        Decode saved input arguments as they came from the saved instance state
        :class:`aiida.engine.processes.persistence.Bundle`.
        The decoded inputs should contain no reference to the encoded inputs that were passed in.
        This often will mean making a deepcopy of the encoded input dictionary.

        :param encoded:
        :return: The decoded input args
        """
        return copy.deepcopy(encoded)

    def get_status_info(self, out_status_info: dict) -> None:
        """Return updated status information of process.

        :param out_status_info: the old status

        """
        out_status_info.update(
            {
                'ctime': self.creation_time,
                'paused': self.paused,
                'process_string': str(self),
                'state': str(self.state),
            }
        )
