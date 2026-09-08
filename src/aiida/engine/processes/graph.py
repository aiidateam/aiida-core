###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Writing a graph of tasks as ordinary Python."""

from __future__ import annotations

import functools
import typing as t
from collections import Counter
from dataclasses import dataclass

from aiida.engine.processes.dag import Dependency, GraphProcess, GraphSpec, GraphTask
from aiida.engine.processes.task import ACTIVE_BUILDER, TaskHandle

__all__ = ('GraphBuilder', 'GraphHandle', 'TaskOutput', 'TaskOutputs', 'graph')


@dataclass(frozen=True)
class TaskOutput:
    """Reference to one output of a task placed in a graph.

    The task has not run, so there is no value to hold. Passing the reference to another task is what records the
    dependency between the two.
    """

    task: str
    port: str


class TaskOutputs:
    """References to the outputs that a task placed in a graph will produce."""

    def __init__(self, task: str, ports: tuple[str, ...]) -> None:
        self.task = task
        self.ports = ports

    def __getattr__(self, name: str) -> TaskOutput:
        # Only called for names that are not real attributes, so the ports cannot shadow ``task`` or ``ports``.
        if name in self.__dict__.get('ports', ()):
            return TaskOutput(task=self.__dict__['task'], port=name)

        raise AttributeError(f'`{self.__dict__.get("task")}` has no output `{name}`.')

    def sole(self) -> TaskOutput:
        """Return the only output of the task.

        :raises ValueError: if the task does not declare exactly one output, since then there is nothing to pick.
        """
        if len(self.ports) != 1:
            raise ValueError(
                f'`{self.task}` declares {len(self.ports)} outputs {list(self.ports)}, so one of them has to be '
                f'named, for example `{self.task}.{self.ports[0] if self.ports else "..."}`.'
            )

        return TaskOutput(task=self.task, port=self.ports[0])


def _as_reference(value: t.Any) -> TaskOutput | None:
    """Return the output reference the value stands for, or ``None`` if it is a plain value."""
    if isinstance(value, TaskOutput):
        return value

    if isinstance(value, TaskOutputs):
        return value.sole()

    return None


class GraphBuilder:
    """Collects the tasks and dependencies of a graph while its function runs."""

    def __init__(self) -> None:
        self._tasks: list[GraphTask] = []
        self._links: list[Dependency] = []
        self._used: Counter[str] = Counter()

    def add_task(self, handle: TaskHandle, arguments: dict[str, t.Any]) -> TaskOutputs:
        """Place a task in the graph, and record where each of its inputs comes from.

        :param handle: the task being placed.
        :param arguments: the arguments of the call, by parameter name.
        :return: references to the outputs the task will produce.
        """
        name = self._unique_name(handle.task_spec.identifier)
        inputs = {}

        for key, value in arguments.items():
            reference = _as_reference(value)

            if reference is None:
                inputs[key] = value
            else:
                self._links.append(
                    Dependency(source=reference.task, source_port=reference.port, target=name, target_port=key)
                )

        self._tasks.append(GraphTask(name=name, spec=handle.task_spec, inputs=inputs))

        return TaskOutputs(task=name, ports=tuple(handle.task_spec.outputs.keys()))

    def _unique_name(self, identifier: str) -> str:
        """Return a name for a task, keeping the second use of a task distinct from the first."""
        self._used[identifier] += 1
        count = self._used[identifier]
        return identifier if count == 1 else f'{identifier}_{count}'

    def finish(self, returned: t.Any) -> GraphSpec:
        """Return the graph that was built, taking what the function returned as the graph's outputs."""
        return GraphSpec(tasks=tuple(self._tasks), links=tuple(self._links), outputs=self._declared_outputs(returned))

    def _declared_outputs(self, returned: t.Any) -> dict[str, tuple[str, str]]:
        """Return the outputs of the graph, from what its function returned."""
        if returned is None:
            return {}

        if isinstance(returned, dict):
            references = {}

            for name, value in returned.items():
                reference = _as_reference(value)

                if reference is None:
                    raise ValueError(f'graph output `{name}` is not the output of a task.')

                references[name] = (reference.task, reference.port)

            return references

        reference = _as_reference(returned)

        if reference is None:
            raise ValueError(
                'a graph returns the outputs of its tasks, so it has to return an output, or a dictionary of them.'
            )

        return {reference.port: (reference.task, reference.port)}


class GraphHandle:
    """What the :func:`graph` decorator returns: a graph that can be built, run, or submitted."""

    def __init__(self, function: t.Callable[..., t.Any], identifier: str | None = None) -> None:
        self._function = function
        self.identifier = identifier or function.__name__
        functools.update_wrapper(self, function)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        raise TypeError(
            f'`{self.identifier}` declares a graph, so it is launched rather than called. Pass it to `run` or '
            f'`submit`, as any other process, or use `.build(...)` for the declaration on its own.'
        )

    def build(self, *args: t.Any, **kwargs: t.Any) -> GraphSpec:
        """Return the graph that the function declares for these arguments."""
        builder = GraphBuilder()
        token = ACTIVE_BUILDER.set(builder)

        try:
            returned = self._function(*args, **kwargs)
        finally:
            ACTIVE_BUILDER.reset(token)

        return builder.finish(returned)

    def get_inputs(self, *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
        """Return the inputs with which to launch the graph declared for these arguments."""
        from aiida.orm import Dict

        return {GraphProcess._DAG: Dict(dict=self.build(*args, **kwargs).to_dict())}


def graph(function: t.Callable[..., t.Any] | None = None, *, identifier: str | None = None) -> t.Any:
    """Declare a function as a graph of tasks.

    The body is not executed: it is run once with the tasks recording themselves instead of running, which turns
    ordinary Python into a declaration. Passing the outputs of one task to another is what records the dependency
    between them, and what the function returns becomes the outputs of the graph.

    Example usage:

    >>> from aiida.engine import graph, run_get_node, task
    >>>
    >>> @task(outputs=['total'])
    >>> def add(x, y):
    >>>     return x + y
    >>>
    >>> @graph
    >>> def add_twice(x, y):
    >>>     return add(x=add(x=x, y=y).total, y=y)
    >>>
    >>> results, node = run_get_node(add_twice, x=1, y=2)

    A graph is launched like any other process, by passing it to ``run`` or ``submit``. Use ``build`` to get the
    declaration on its own, without running anything.

    :param function: The function to decorate.
    :param identifier: Name of the graph, which defaults to the name of the function.
    :return: A handle that can build, run, or submit the graph.
    """

    def decorator(function: t.Callable[..., t.Any]) -> GraphHandle:
        return GraphHandle(function, identifier=identifier)

    if function is not None:
        return decorator(function)

    return decorator
