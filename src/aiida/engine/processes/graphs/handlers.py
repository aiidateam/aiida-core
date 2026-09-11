###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Recovering from the failed runs of a task."""

from __future__ import annotations

import sys
import typing as t
from collections import Counter
from dataclasses import dataclass
from types import FunctionType

from aiida.common import AttributeDict
from aiida.engine.processes.exit_code import ExitCode
from aiida.engine.processes.generic.ports import PortNamespace
from aiida.engine.processes.process import Process
from aiida.engine.processes.workchains.outline import while_
from aiida.engine.processes.workchains.restart import BaseRestartWorkChain
from aiida.engine.processes.workchains.utils import ProcessHandlerReport, process_handler

if t.TYPE_CHECKING:
    from aiida.orm import ProcessNode

__all__ = ('TaskHandler', 'TaskWorkChain', 'handler')

HANDLED_SUFFIX = '_handled'
"""What the name of a task is extended by to name the work chain that handles it."""

HandlerFunction = t.Callable[['ProcessNode', AttributeDict], 'ProcessHandlerReport | None']
"""What a handler is written as: given the run that failed and the inputs of the next one, fix the inputs."""


@dataclass(frozen=True)
class TaskHandler:
    """One way a task recovers from a run that failed.

    The function is given the node of the run that failed and the inputs the next run will be launched with, and
    changes those inputs in place to fix what went wrong. Returning a
    :class:`~aiida.engine.processes.workchains.utils.ProcessHandlerReport` says the failure was handled, and its
    ``do_break`` stops the handlers below this one from being called for that run.
    """

    function: HandlerFunction
    priority: int = 0
    exit_codes: tuple[ExitCode, ...] = ()
    enabled: bool = True

    @property
    def name(self) -> str:
        """Return the name this handler is known by, which ``handler_overrides`` addresses it under."""
        return self.function.__name__

    def __call__(self, node: ProcessNode, inputs: AttributeDict) -> ProcessHandlerReport | None:
        """Call the handler, so that one can be tried on its own without a work chain around it."""
        return self.function(node, inputs)


def handler(
    function: HandlerFunction | None = None,
    *,
    priority: int = 0,
    exit_codes: ExitCode | t.Sequence[ExitCode] | None = None,
    enabled: bool = True,
) -> t.Any:
    """Declare a function a way for a task to recover from a run that failed.

    The function takes the node of the run that failed and the inputs the next run will be launched with, and
    changes those inputs to fix what went wrong:

    >>> from aiida.engine import ProcessHandlerReport, handler, task
    >>>
    >>> @handler(exit_codes=SomeCalculation.exit_codes.ERROR_OUT_OF_WALLTIME)
    >>> def ask_for_longer(node, inputs):
    >>>     inputs.metadata.options.max_wallclock_seconds *= 2
    >>>     return ProcessHandlerReport(do_break=True)
    >>>
    >>> converge = task(converge, handlers=[ask_for_longer])

    Handling is what a :class:`~aiida.engine.processes.workchains.restart.BaseRestartWorkChain` already does, and
    a handled task is run by one, so a work chain written by hand stays the way to reach for when the handling
    grows past what a few functions say.

    :param function: The function to declare a handler, or ``None`` when the decorator is given arguments.
    :param priority: Handlers are called from the highest priority down, and ``do_break`` stops the rest.
    :param exit_codes: Call the handler only for a run that failed with one of these, or for any failed run when
        none are given.
    :param enabled: Whether to call the handler at all, which ``handler_overrides`` can turn around per run.
    :return: The handler, which stays callable so that it can be tried on its own.
    """
    if exit_codes is None:
        codes: tuple[ExitCode, ...] = ()
    elif isinstance(exit_codes, ExitCode):
        codes = (exit_codes,)
    else:
        codes = tuple(exit_codes)

    def decorator(function: HandlerFunction) -> TaskHandler:
        return TaskHandler(function=function, priority=priority, exit_codes=codes, enabled=enabled)

    if function is not None:
        return decorator(function)

    return decorator


class TaskWorkChain(BaseRestartWorkChain):
    """Run the process of one task, and give every run that failed to the task's handlers.

    The process takes its inputs under a namespace of their own, since a work chain cannot carry the metadata a
    calculation job takes: :meth:`~aiida.engine.processes.process.Process._setup_metadata` writes only the keys
    every process has, so a ``CalcJob`` exposed at the root would make ``metadata.options`` unusable. A graph
    wires against the ports of the process itself and puts them under the namespace as it launches, so the
    namespace stays out of what a task is written with.
    """

    NAMESPACE: t.ClassVar[str] = 'task'
    """Namespace the inputs of the task are taken under."""

    @classmethod
    def define(cls, spec: t.Any) -> None:
        super().define(spec)

        if cls._process_class is None:
            # This is the base itself, which runs nothing, so it has no ports to take or produce.
            return

        spec.expose_inputs(cls._process_class, namespace=cls.NAMESPACE)
        spec.expose_outputs(cls._process_class)
        # `while_` asks for a method of `WorkChain` itself, which a method of a subclass of it is not, so the
        # class is read through a name that is not narrowed to one.
        chain: t.Any = cls

        spec.outline(
            chain.setup,
            while_(chain.should_run_process)(
                chain.run_process,
                chain.inspect_process,
            ),
            chain.results,
        )

    @classmethod
    def task_inputs(cls) -> PortNamespace:
        """Return the input ports of the task itself, without the namespace they are taken under."""
        return t.cast(PortNamespace, cls.spec().inputs[cls.NAMESPACE])

    def setup(self) -> None:
        super().setup()
        self.ctx.inputs = AttributeDict(self.exposed_inputs(self.process_class, namespace=self.NAMESPACE))


def handled(process_class: type[Process], handlers: t.Sequence[TaskHandler], reference: t.Any) -> type[TaskWorkChain]:
    """Return a work chain that runs a process and gives the runs that failed to the handlers.

    The generated class is put in the module the task is declared in, under the name of the task extended by
    ``_handled``. A run records the module and name of its process class and is read back from them, so the work
    chain needs a name of its own: sharing the one the task is declared under would make a run of the task and a
    run of the work chain around it resolve to the same thing.

    :param process_class: the process the task runs.
    :param handlers: the ways the task recovers, which become the process handlers of the work chain.
    :param reference: the importable thing the task is reached by, whose module the generated class is put in.
    :raises ValueError: if two handlers share a name, which would leave one of them unaddressable, or if the name
        the work chain needs is taken by something else in that module.
    """
    repeated = sorted(name for name, count in Counter(one.name for one in handlers).items() if count > 1)

    if repeated:
        msg = (
            f'`{reference.__name__}` declares more than one handler named {repeated}, and a handler is addressed '
            f'by its name, so each one needs a name of its own.'
        )
        raise ValueError(msg)

    name = f'{reference.__name__}{HANDLED_SUFFIX}'
    namespace: dict[str, t.Any] = {'__module__': reference.__module__, '_process_class': process_class}

    for one in handlers:
        namespace[one.name] = _as_method(one)

    generated = type(name, (TaskWorkChain,), namespace)
    module = sys.modules.get(reference.__module__)

    if module is None:
        return generated

    taken = getattr(module, name, None)

    if taken is not None and not (isinstance(taken, type) and issubclass(taken, TaskWorkChain)):
        msg = (
            f'`{reference.__module__}` already has a `{name}`, which is the name the work chain handling '
            f'`{reference.__name__}` is reached by. Rename one of the two.'
        )
        raise ValueError(msg)

    setattr(module, name, generated)

    return generated


def launch_under_namespace(inputs: dict[str, t.Any]) -> dict[str, t.Any]:
    """Return the inputs of a task as the work chain that handles it takes them.

    The metadata stays outside the namespace, so that a label or a call link label names the run that was asked
    for rather than the process inside it.
    """
    metadata = inputs.get('metadata')
    task = {key: value for key, value in inputs.items() if key != 'metadata'}
    under: dict[str, t.Any] = {TaskWorkChain.NAMESPACE: task}

    return under if metadata is None else {**under, 'metadata': metadata}


def _as_method(task_handler: TaskHandler) -> t.Any:
    """Return the handler as the instance method that a work chain registers as a process handler."""
    function = task_handler.function

    def method(self: TaskWorkChain, node: ProcessNode) -> ProcessHandlerReport | None:
        return function(node, self.ctx.inputs)

    method.__name__ = task_handler.name
    method.__qualname__ = task_handler.name
    method.__doc__ = function.__doc__

    return process_handler(
        t.cast(FunctionType, method),
        priority=task_handler.priority,
        exit_codes=list(task_handler.exit_codes) or None,
        enabled=task_handler.enabled,
    )
