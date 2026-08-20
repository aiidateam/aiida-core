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
"""Process state machine states."""

from __future__ import annotations

import sys
import traceback
from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import TYPE_CHECKING, Any, cast

import yaml
from yaml.loader import Loader

from aiida.common.loaders import load_function
from aiida.common.processes import ProcessState
from aiida.engine.processes.communications import MessageBuilder, MessageType

try:
    import tblib

    _HAS_TBLIB: bool = True
except ImportError:
    _HAS_TBLIB = False

from aiida.engine.processes import exceptions, persistence, state_machine
from aiida.engine.processes.generic import futures
from aiida.engine.processes.persistence import SAVED_STATE_TYPE, auto_persist
from aiida.engine.utils import ensure_coroutine

__all__: tuple[str, ...] = ()

if TYPE_CHECKING:
    from aiida.engine.processes.generic.process import Process


class __NULL:
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__)


NULL = __NULL()


class Interruption(Exception):  # noqa: N818
    pass


class KillInterruption(Interruption):
    def __init__(self, msg_text: str | None, force_kill: bool = False):
        super().__init__(msg_text)
        msg = MessageBuilder.kill(text=msg_text, force_kill=force_kill)

        self.msg: MessageType = msg
        self.force_kill: bool = force_kill


class PauseInterruption(Interruption):
    def __init__(self, msg_text: str | None):
        super().__init__(msg_text)
        msg = MessageBuilder.pause(text=msg_text)

        self.msg: MessageType = msg


# region Commands


class Command(persistence.Savable):
    pass


@auto_persist('msg')
class Kill(Command):
    def __init__(self, msg: MessageType | None = None):
        super().__init__()
        self.msg = msg


class Pause(Command):
    pass


@auto_persist('msg', 'data')
class Wait(Command):
    def __init__(
        self,
        continue_fn: Callable[..., Any] | None = None,
        msg: Any | None = None,
        data: Any | None = None,
    ):
        super().__init__()
        self.continue_fn = continue_fn
        self.msg = msg
        self.data = data


@auto_persist('result')
class Stop(Command):
    def __init__(self, result: Any, successful: bool) -> None:
        super().__init__()
        self.result = result
        self.successful = successful


@auto_persist('args', 'kwargs')
class Continue(Command):
    CONTINUE_FN = 'continue_fn'

    def __init__(self, continue_fn: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.continue_fn = continue_fn
        self.args = args
        self.kwargs = kwargs

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        out_state[self.CONTINUE_FN] = self.continue_fn.__name__

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        try:
            self.continue_fn = load_function(saved_state[self.CONTINUE_FN])
        except ValueError:
            process = load_context.process
            self.continue_fn = getattr(process, saved_state[self.CONTINUE_FN])


# endregion

# region States


@auto_persist('in_state')
class State(state_machine.State, persistence.Savable):
    @property
    def process(self) -> state_machine.StateMachine:
        """
        :return: The process
        """
        return self.state_machine

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self.state_machine = load_context.process

    def interrupt(self, reason: Any) -> None:
        pass


@auto_persist('args', 'kwargs')
class Created(State):
    LABEL = ProcessState.CREATED
    ALLOWED = {ProcessState.RUNNING, ProcessState.KILLED, ProcessState.EXCEPTED}

    RUN_FN = 'run_fn'

    def __init__(self, process: Process, run_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__(process)
        assert run_fn is not None
        self.run_fn = run_fn
        self.args = args
        self.kwargs = kwargs

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        out_state[self.RUN_FN] = self.run_fn.__name__

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self.run_fn = getattr(self.process, saved_state[self.RUN_FN])

    def execute(self) -> state_machine.State:
        return self.create_state(ProcessState.RUNNING, self.run_fn, *self.args, **self.kwargs)


@auto_persist('args', 'kwargs')
class Running(State):
    LABEL = ProcessState.RUNNING
    ALLOWED = {
        ProcessState.RUNNING,
        ProcessState.WAITING,
        ProcessState.FINISHED,
        ProcessState.KILLED,
        ProcessState.EXCEPTED,
    }

    RUN_FN = 'run_fn'  # The key used to store the function to run
    COMMAND = 'command'  # The key used to store an upcoming command

    # Class level defaults
    _command: None | Kill | Stop | Wait | Continue = None
    _running: bool = False
    _run_handle = None

    def __init__(
        self, process: Process, run_fn: Callable[..., Awaitable[Any] | Any], *args: Any, **kwargs: Any
    ) -> None:
        super().__init__(process)
        assert run_fn is not None
        self.run_fn = ensure_coroutine(run_fn)
        # We wrap `run_fn` to a coroutine so we can apply await on it,
        # even it if it was not a coroutine in the first place.
        # This allows the same usage of async and non-async function
        # with the await syntax while not changing the program logic.
        self.args = args
        self.kwargs = kwargs
        self._run_handle = None

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        out_state[self.RUN_FN] = self.run_fn.__name__
        if self._command is not None:
            out_state[self.COMMAND] = self._command.save()

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self.run_fn = ensure_coroutine(getattr(self.process, saved_state[self.RUN_FN]))
        if self.COMMAND in saved_state:
            self._command = persistence.Savable.load(saved_state[self.COMMAND], load_context)  # type: ignore[assignment]

    def interrupt(self, reason: Any) -> None:
        pass

    async def execute(self) -> State:  # type: ignore[override]
        if self._command is not None:
            command = self._command
        else:
            try:
                try:
                    self._running = True
                    result = await self.run_fn(*self.args, **self.kwargs)
                finally:
                    self._running = False
            except Interruption:
                # Let this bubble up to the caller
                raise
            except Exception:
                excepted = self.create_state(ProcessState.EXCEPTED, *sys.exc_info()[1:])
                return cast(State, excepted)
            else:
                if not isinstance(result, Command):
                    if isinstance(result, exceptions.UnsuccessfulResult):
                        result = Stop(result.result, False)
                    else:
                        # Got passed a basic return type
                        result = Stop(result, True)

                command = result

        next_state = self._action_command(command)
        return next_state

    def _action_command(self, command: Kill | Stop | Wait | Continue) -> State:
        if isinstance(command, Kill):
            state = self.create_state(ProcessState.KILLED, command.msg)
        # elif isinstance(command, Pause):
        #     self.pause()
        elif isinstance(command, Stop):
            state = self.create_state(ProcessState.FINISHED, command.result, command.successful)
        elif isinstance(command, Wait):
            state = self.create_state(ProcessState.WAITING, command.continue_fn, command.msg, command.data)
        elif isinstance(command, Continue):
            state = self.create_state(ProcessState.RUNNING, command.continue_fn, *command.args)
        else:
            raise ValueError('Unrecognised command')

        return cast(State, state)  # casting from base.State to process.State


@auto_persist('msg', 'data')
class Waiting(State):
    LABEL = ProcessState.WAITING
    ALLOWED = {
        ProcessState.RUNNING,
        ProcessState.WAITING,
        ProcessState.KILLED,
        ProcessState.EXCEPTED,
        ProcessState.FINISHED,
    }

    DONE_CALLBACK = 'DONE_CALLBACK'

    _interruption = None

    def __str__(self) -> str:
        state_info = super().__str__()
        if self.msg is not None:
            state_info += f' ({self.msg})'
        return state_info

    def __init__(
        self,
        process: Process,
        done_callback: Callable[..., Any] | None,
        msg: str | None = None,
        data: Any | None = None,
    ) -> None:
        super().__init__(process)
        self.done_callback = done_callback
        self.msg = msg
        self.data = data
        self._waiting_future: futures.Future = futures.Future()

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        if self.done_callback is not None:
            out_state[self.DONE_CALLBACK] = self.done_callback.__name__

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        callback_name = saved_state.get(self.DONE_CALLBACK, None)
        if callback_name is not None:
            self.done_callback = getattr(self.process, callback_name)
        else:
            self.done_callback = None
        self._waiting_future = futures.Future()

    def interrupt(self, reason: Any) -> None:
        # This will cause the future in execute() to raise the exception
        self._waiting_future.set_exception(reason)

    async def execute(self) -> State:  # type: ignore[override]
        try:
            result = await self._waiting_future
        except Interruption:
            # Deal with the interruption (by raising) but make sure our internal
            # state is back to how it was before the interruption so that we can be
            # re-executed
            self._waiting_future = futures.Future()
            raise

        if result == NULL:
            next_state = self.create_state(ProcessState.RUNNING, self.done_callback)
        else:
            next_state = self.create_state(ProcessState.RUNNING, self.done_callback, result)

        return cast(State, next_state)  # casting from base.State to process.State

    def resume(self, value: Any = NULL) -> None:
        assert self._waiting_future is not None, 'Not yet waiting'

        if self._waiting_future.done():
            return

        self._waiting_future.set_result(value)


class Excepted(State):
    """
    Excepted state, can optionally provide exception and trace_back

    :param exception: The exception instance
    :param trace_back: An optional exception traceback
    """

    LABEL = ProcessState.EXCEPTED

    EXC_VALUE = 'ex_value'
    TRACEBACK = 'traceback'

    def __init__(
        self,
        process: Process,
        exception: BaseException | None,
        trace_back: TracebackType | None = None,
    ):
        """
        :param process: The associated process
        :param exception: The exception instance
        :param trace_back: An optional exception traceback
        """
        super().__init__(process)
        self.exception = exception
        self.traceback = trace_back

    def __str__(self) -> str:
        exception = traceback.format_exception_only(type(self.exception) if self.exception else None, self.exception)[0]
        return super().__str__() + f'({exception})'

    def save_instance_state(self, out_state: SAVED_STATE_TYPE, save_context: persistence.LoadSaveContext) -> None:
        super().save_instance_state(out_state, save_context)
        out_state[self.EXC_VALUE] = yaml.dump(self.exception)
        if self.traceback is not None:
            out_state[self.TRACEBACK] = ''.join(traceback.format_tb(self.traceback))

    def load_instance_state(self, saved_state: SAVED_STATE_TYPE, load_context: persistence.LoadSaveContext) -> None:
        super().load_instance_state(saved_state, load_context)
        self.exception = yaml.load(saved_state[self.EXC_VALUE], Loader=Loader)
        if _HAS_TBLIB:
            try:
                self.traceback = tblib.Traceback.from_string(saved_state[self.TRACEBACK], strict=False)
            except KeyError:
                self.traceback = None
        else:
            self.traceback = None

    def get_exc_info(
        self,
    ) -> tuple[type[BaseException] | None, BaseException | None, TracebackType | None]:
        """
        Recreate the exc_info tuple and return it
        """
        return (
            type(self.exception) if self.exception else None,
            self.exception,
            self.traceback,
        )


@auto_persist('result', 'successful')
class Finished(State):
    """State for process is finished.

    :param result: The result of process
    :param successful: Boolean for the exit code is ``0`` the process is successful.
    """

    LABEL = ProcessState.FINISHED

    def __init__(self, process: Process, result: Any, successful: bool) -> None:
        super().__init__(process)
        self.result = result
        self.successful = successful


@auto_persist('msg')
class Killed(State):
    """
    Represents a state where a process has been killed.

    This state is used to indicate that a process has been terminated and can optionally
    include a message providing details about the termination.

    :param msg: An optional message explaining the reason for the process termination.
    """

    LABEL = ProcessState.KILLED

    def __init__(self, process: Process, msg: MessageType | None):
        """
        :param process: The associated process
        :param msg: Optional kill message
        """
        super().__init__(process)
        self.msg = msg


# endregion
