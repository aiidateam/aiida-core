###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Waiting for something outside the graph before going on."""

from __future__ import annotations

import asyncio
import functools
import time
import typing as t

from aiida.common.lang import override
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.graphs.process import TaskProcess
from aiida.engine.processes.process import Process
from aiida.engine.processes.states import Wait
from aiida.orm import Float, Int, WorkflowNode, WorkFunctionNode, load_node
from aiida.orm.nodes.data.base import to_aiida_type

if t.TYPE_CHECKING:
    from aiida.orm import Data

__all__ = ('MonitorProcess', 'WaitProcess')

INTERVAL = 'interval'
"""How long to wait between one look and the next."""

TIMEOUT = 'timeout'
"""How long to keep looking before giving up."""


class MonitorProcess(TaskProcess):
    """Look at a condition until it holds, so that what waits on it goes on only then.

    The condition is an ordinary function returning whether it is met, called every ``interval`` seconds until it
    says yes or ``timeout`` seconds have gone by. Waiting is awaited rather than slept through, so the worker
    running it carries on with everything else in the meantime.

    It does wait resident, holding one of the process slots a worker has, so a monitor waiting on something that
    needs a free slot to be produced holds the slot that would produce it, and only the timeout ends that.
    """

    _node_class = WorkFunctionNode

    @classmethod
    def define(cls, spec: t.Any) -> None:
        super().define(spec)
        spec.input(
            INTERVAL,
            valid_type=Float,
            default=lambda: Float(1.0),
            serializer=to_aiida_type,
            help='Seconds to wait between one look at the condition and the next.',
        )
        spec.input(
            TIMEOUT,
            valid_type=Float,
            default=lambda: Float(86400.0),
            serializer=to_aiida_type,
            help='Seconds to keep looking before giving up, which fails the task and so the graph around it.',
        )
        spec.exit_code(
            410,
            'ERROR_TIMED_OUT',
            message='Waited {timeout} seconds for the condition to be met, and it was not.',
        )

    @override
    async def run(self) -> ExitCode | None:
        """Look at the condition until it holds, or until there is no time left to look again."""
        if self.node.exit_status is not None:
            return ExitCode(self.node.exit_status, self.node.exit_message)

        from aiida.engine.processes.greenback import run_with_portal

        interval, timeout = self.inputs[INTERVAL].value, self.inputs[TIMEOUT].value
        args, kwargs = self._function_arguments()
        deadline = time.monotonic() + timeout

        while True:
            if await run_with_portal(self._func, *args, **kwargs):
                return ExitCode()

            if time.monotonic() + interval > deadline:
                self.report(f'the condition was not met within {timeout} seconds')
                return self.exit_codes.ERROR_TIMED_OUT.format(timeout=timeout)

            await asyncio.sleep(interval)

    @override
    def _function_arguments(self) -> tuple[list[t.Any], dict[str, Data]]:
        """Return the arguments of the condition, which is not given how long to wait between looks."""
        args, kwargs = super()._function_arguments()

        for name in (INTERVAL, TIMEOUT):
            kwargs.pop(name, None)

        return args, kwargs


class WaitProcess(Process):
    """Wait for a process this graph did not run to end, being told when rather than asking over and over.

    The engine says when a process ends, so nothing here looks at it on a timer: what waits is woken when it
    happens. A process that this graph ran is waited for by depending on it, so this is for one submitted
    elsewhere, whose pk a run is given.
    """

    _node_class = WorkflowNode

    PK = 'pk'
    """Port naming the process to wait for.

    A port named ``process`` would be unreachable: every way of submitting hands the inputs on as
    keywords, and ``process`` is what each of them calls its first parameter.
    """

    @classmethod
    def define(cls, spec: t.Any) -> None:
        super().define(spec)
        spec.input(
            cls.PK,
            valid_type=Int,
            serializer=to_aiida_type,
            help='The pk of the process to wait for, which this graph did not run itself.',
        )
        spec.exit_code(
            410,
            'ERROR_PROCESS_DID_NOT_FINISH_OK',
            message='The process <{pk}> that was waited for ended as {state}.',
        )

    @override
    async def run(self) -> t.Any:
        """Wait for the process to end, unless it already has."""
        if self._awaited.is_terminated:
            return self._outcome()

        self.report(f'waiting for {self._awaited.process_label}<{self._awaited.pk}> to end')

        return Wait(self._outcome, f'waiting for <{self._awaited.pk}>')

    @override
    def on_wait(self, awaitables: t.Sequence[t.Awaitable]) -> None:
        """Ask to be woken when the process ends, which is what the engine broadcasts."""
        super().on_wait(awaitables)
        self.runner.call_on_process_finish(self._awaited.pk, functools.partial(self.call_soon, self.resume))

    @property
    def _awaited(self) -> t.Any:
        """Return the node of the process being waited for."""
        return load_node(pk=self.inputs[self.PK].value)

    def _outcome(self) -> ExitCode | None:
        """Return whether what was waited for got there, so that a failure of it stops what waits on this."""
        node = self._awaited

        if node.is_finished_ok:
            return None

        return self.exit_codes.ERROR_PROCESS_DID_NOT_FINISH_OK.format(pk=node.pk, state=node.process_state.value)
