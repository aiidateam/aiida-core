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

import contextvars
import functools
import inspect
import typing as t
from collections import Counter
from dataclasses import dataclass

from aiida.engine.processes.functions import ProcessFunctionType, process_function
from aiida.engine.processes.graphs.process import GraphProcess, TaskProcess
from aiida.engine.processes.graphs.spec import (
    DEFINED_TASKS,
    Dependency,
    Endpoint,
    GraphSpec,
    GraphTask,
    MapTask,
    TaskSpec,
)
from aiida.engine.processes.process import Process
from aiida.orm import CalcFunctionNode

__all__ = (
    'Each',
    'GraphBuilder',
    'GraphHandle',
    'GraphInput',
    'MappedOutput',
    'MappedOutputs',
    'TaskHandle',
    'TaskOutput',
    'TaskOutputs',
    'each',
    'graph',
    'task',
)

ACTIVE_BUILDER: contextvars.ContextVar[t.Any | None] = contextvars.ContextVar(
    'aiida_active_graph_builder', default=None
)
"""The graph being built, if any.

While a graph is being built, calling a task records it in that graph instead of running it. This is what lets a
graph be written as ordinary Python.
"""

P = t.ParamSpec('P')

R_co = t.TypeVar('R_co', covariant=True)


@dataclass(frozen=True)
class TaskOutput:
    """Reference to one output of a task placed in a graph.

    The task has not run, so there is no value to hold. Passing the reference to another task is what records the
    dependency between the two.
    """

    task: str
    port: str


@dataclass(frozen=True)
class MappedOutput(TaskOutput):
    """Reference to one output of a task that runs once per item, which is one result per item.

    A graph can return this, and gets a result per item under the key of the item. Passing it to another task is
    refused, since that task would take a collection of results where it declares one value.
    """


@dataclass(frozen=True)
class GraphInput:
    """Stands for one input of the graph while its body is traced.

    The body is traced once, without values, so wherever this reaches a task the graph records that the input
    feeds that port. The value itself arrives as an input of the process that runs the graph.
    """

    name: str


@dataclass(frozen=True)
class Each:
    """A collection to run a task over one item at a time, as returned by :func:`each`."""

    collection: t.Any


def each(collection: t.Any) -> Each:
    """Mark the input a task is run once per item of.

    Passing this instead of a value is what turns a call into a fan-out, so the task runs once per item of the
    collection and its results are gathered under the key of each item.

    Example usage:

    >>> @graph
    >>> def shift_all(values):
    >>>     return add(x=each(values), y=10)

    The collection can be the output of another task, in which case how many items there are is only known once
    that task has run.

    :param collection: a list or a dictionary, or the output of a task that produces one.
    """
    return Each(collection=collection)


class TaskOutputs:
    """References to the outputs that a task placed in a graph will produce."""

    _output_class: t.ClassVar[type[TaskOutput]] = TaskOutput

    def __init__(self, task: str, ports: tuple[str, ...]) -> None:
        self.task = task
        self.ports = ports

    def __getattr__(self, name: str) -> TaskOutput:
        # Only called for names that are not real attributes, so the ports cannot shadow ``task`` or ``ports``.
        if name in self.__dict__.get('ports', ()):
            return self._output_class(task=self.__dict__['task'], port=name)

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

        return self._output_class(task=self.task, port=self.ports[0])


class MappedOutputs(TaskOutputs):
    """References to the outputs of a task that runs once per item, each of them a result per item."""

    _output_class: t.ClassVar[type[TaskOutput]] = MappedOutput


def _as_reference(value: t.Any) -> TaskOutput | None:
    """Return the output reference the value stands for, or ``None`` if it is a plain value."""
    if isinstance(value, TaskOutput):
        return value

    if isinstance(value, TaskOutputs):
        return value.sole()

    return None


def _holds_reference(value: t.Any) -> bool:
    """Return whether the output of a task is buried inside a container.

    Only an argument that *is* an output records a dependency, so one inside a container would be stored as a
    plain value and the task it comes from would never be waited for.
    """
    if isinstance(value, (TaskOutput, TaskOutputs, GraphInput)):
        return True

    if isinstance(value, (list, tuple, set)):
        return any(_holds_reference(item) for item in value)

    if isinstance(value, dict):
        return any(_holds_reference(item) for item in value.values())

    return False


class GraphBuilder:
    """Collects the tasks and dependencies of a graph while its function runs."""

    def __init__(self) -> None:
        self._tasks: list[GraphTask] = []
        self._dependencies: list[Dependency] = []
        self._inputs: dict[str, list[tuple[str, str]]] = {}
        self._used: Counter[str] = Counter()

    def add_task(self, handle: TaskHandle, arguments: dict[str, t.Any]) -> TaskOutputs:
        """Place a task in the graph, and record where each of its inputs comes from.

        :param handle: the task being placed.
        :param arguments: the arguments of the call, by parameter name.
        :return: references to the outputs the task will produce.
        :raises ValueError: if more than one input is marked with :func:`each`.
        """
        name = self._unique_name(handle.task_spec.identifier)
        inputs = {}
        item_ports = []

        for key, argument in arguments.items():
            if isinstance(argument, Each):
                item_ports.append(key)

            value = argument.collection if isinstance(argument, Each) else argument

            if isinstance(value, GraphInput):
                self._inputs.setdefault(value.name, []).append((name, key))
                continue

            reference = _as_reference(value)

            if isinstance(reference, MappedOutput):
                raise ValueError(
                    f'`{name}` takes `{key}` from `{reference.task}`, which runs once per item and so has a '
                    f'result per item, where `{key}` takes one value. Taking the results of a fan-out into '
                    f'another task is not supported yet; a graph can return them.'
                )

            if reference is not None:
                self._dependencies.append(
                    Dependency(source=reference.task, source_port=reference.port, target=name, target_port=key)
                )
                continue

            if _holds_reference(value):
                raise ValueError(
                    f'`{name}` takes `{key}` with the output of another task inside a '
                    f'{type(value).__name__}, which would be stored as a value and leave that task unwaited for. '
                    f'Pass the output itself, or take the collection from a task that produces one.'
                )

            inputs[key] = value

        node = self._node(name, handle, inputs, item_ports)
        self._tasks.append(node)
        outputs_class = MappedOutputs if isinstance(node, MapTask) else TaskOutputs

        return outputs_class(task=name, ports=tuple(handle.task_spec.outputs.keys()))

    @staticmethod
    def _node(name: str, handle: TaskHandle, inputs: dict[str, t.Any], item_ports: list[str]) -> GraphTask:
        """Return the node for a call, which fans out when one of its inputs was marked with :func:`each`."""
        if not item_ports:
            return GraphTask(name=name, spec=handle.task_spec, inputs=inputs)

        if len(item_ports) > 1:
            raise ValueError(
                f'`{name}` runs once per item of {sorted(item_ports)}, and a task runs over one of its inputs. '
                f'Combine them into one input, or place a task per input.'
            )

        return MapTask(name=name, spec=handle.task_spec, inputs=inputs, item_port=item_ports[0])

    def _unique_name(self, identifier: str) -> str:
        """Return a name for a task, keeping the second use of a task distinct from the first."""
        self._used[identifier] += 1
        count = self._used[identifier]
        return identifier if count == 1 else f'{identifier}_{count}'

    def finish(self, returned: t.Any) -> GraphSpec:
        """Return the graph that was built, taking what the function returned as the graph's outputs."""
        return GraphSpec(
            tasks=tuple(self._tasks),
            dependencies=tuple(self._dependencies),
            inputs={name: tuple(targets) for name, targets in self._inputs.items()},
            outputs=self._declared_outputs(returned),
        )

    def _declared_outputs(self, returned: t.Any) -> dict[str, Endpoint]:
        """Return the outputs of the graph, from what its function returned."""
        if returned is None:
            return {}

        if isinstance(returned, dict):
            return {name: self._output_source(value, name) for name, value in returned.items()}

        source = self._as_source(returned)

        if source is None:
            raise ValueError(
                'a graph returns the outputs of its tasks, or its own inputs, so it has to return one of those, '
                'or a dictionary of them.'
            )

        return {source.port: source}

    def _output_source(self, value: t.Any, name: str) -> Endpoint:
        """Return where one named output of the graph comes from.

        :raises ValueError: if the value is neither the output of a task nor an input of the graph.
        """
        source = self._as_source(value)

        if source is None:
            raise ValueError(f'graph output `{name}` is not the output of a task, nor an input of the graph.')

        return source

    @staticmethod
    def _as_source(value: t.Any) -> Endpoint | None:
        """Return the output source a returned value stands for, or ``None`` if it stands for neither."""
        if isinstance(value, GraphInput):
            return Endpoint(task=None, port=value.name)

        reference = _as_reference(value)

        return None if reference is None else Endpoint(task=reference.task, port=reference.port)


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

    def build(self) -> GraphSpec:
        """Return the graph that the function declares.

        The body is traced once with each of its parameters standing for an input of the graph, so the result is
        the same declaration for every run and the values are what a run supplies.
        """
        builder = GraphBuilder()
        token = ACTIVE_BUILDER.set(builder)

        try:
            returned = self._function(**{name: GraphInput(name=name) for name in self.parameters})
        finally:
            ACTIVE_BUILDER.reset(token)

        return builder.finish(returned)

    @property
    def parameters(self) -> tuple[str, ...]:
        """Return the names of the inputs the graph takes, which are the parameters of its function."""
        kinds = (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        return tuple(
            name for name, parameter in inspect.signature(self._function).parameters.items() if parameter.kind in kinds
        )

    @property
    def process_class(self) -> type[GraphProcess]:
        """Return the process that runs a graph."""
        return GraphProcess

    def get_launch_inputs(self, *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
        """Return the inputs with which to launch the graph for these arguments.

        The declaration says what to run and the arguments are what to run it on, so they travel side by side and
        the same declaration serves every run.
        """
        from aiida.orm import Data, Dict
        from aiida.orm.nodes.data.base import to_aiida_type

        bound = inspect.signature(self._function).bind(*args, **kwargs)
        bound.apply_defaults()

        return {
            GraphProcess._GRAPH: Dict(dict=self.build().to_dict()),
            GraphProcess._GRAPH_INPUTS: {
                name: value if isinstance(value, Data) else to_aiida_type(value)
                for name, value in bound.arguments.items()
            },
        }


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


class TaskHandle:
    """What the :func:`task` decorator returns: a task that can be run, launched, or placed in a graph.

    Calling it runs the function, unless a graph is being built, in which case the call is recorded in that graph
    and returns a reference to the outputs the task will produce. It carries the attributes of the process function
    it wraps, so it can be passed to ``run`` and ``submit`` like any other.
    """

    is_process_function: bool = True

    def __init__(self, function: t.Any, spec: TaskSpec) -> None:
        self._function = function
        self.task_spec = spec
        functools.update_wrapper(self, function)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        builder = ACTIVE_BUILDER.get()

        if builder is None:
            return self._function(*args, **kwargs)

        return builder.add_task(self, self.bind_arguments(*args, **kwargs))

    def bind_arguments(self, *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
        """Return the arguments of a call to this task, by the name of the parameter each is bound to."""
        bound = inspect.signature(self._function).bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)

    @property
    def process_class(self) -> type[Process]:
        return self._function.process_class

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        return self._function.get_launch_inputs(**inputs)

    @property
    def node_class(self) -> t.Any:
        return self._function.node_class

    @property
    def recreate_from(self) -> t.Any:
        return self._function.recreate_from

    def spec(self) -> t.Any:
        return self._function.spec()

    def run(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.run(*args, **kwargs)

    def run_get_node(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.run_get_node(*args, **kwargs)

    def run_get_pk(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._function.run_get_pk(*args, **kwargs)


def task(
    function: t.Callable[P, R_co] | None = None,
    *,
    outputs: t.Sequence[str] | None = None,
    identifier: str | None = None,
) -> t.Any:
    """Declare a standard python function as a task.

    A task records its execution like a :func:`~aiida.engine.processes.functions.calcfunction` does, and
    additionally takes and returns plain Python values. It can be launched on its own, including by a running
    process that dispatches it as a called child, as long as the function is importable by the daemon worker.

    The declaration is available as ``task_spec``, and is what a graph places and links against.

    Example usage:

    >>> from aiida.engine import submit, task
    >>>
    >>> @task(outputs=['total', 'product'])
    >>> def sum_product(x, y):
    >>>     return x + y, x * y
    >>>
    >>> node = submit(sum_product, x=2, y=3)

    Output ports are taken from ``outputs`` when given, otherwise from the return annotation: a ``TypedDict``
    declares one port per field, any other annotation a single ``result`` port. Without either, the output
    namespace stays dynamic, as it is for a calcfunction.

    :param function: The function to decorate.
    :param outputs: Names of the output ports to declare.
    :param identifier: Name of the task, which defaults to the name of the function.
    :return: The decorated function, carrying its ``task_spec``.
    """

    def decorator(function: t.Callable[P, R_co]) -> ProcessFunctionType[P, R_co, CalcFunctionNode]:
        decorated = process_function(node_class=CalcFunctionNode, base_class=TaskProcess, outputs=outputs)(function)

        # Build the process spec eagerly, so an invalid declaration is reported where the task is defined rather
        # than when it is first launched.
        decorated.process_class.spec()  # type: ignore[attr-defined]

        spec = TaskSpec.from_process(decorated, identifier=identifier)
        DEFINED_TASKS[f'{spec.executor.module}:{spec.executor.name}'] = decorated

        return TaskHandle(decorated, spec)  # type: ignore[return-value]

    if function is not None:
        return decorator(function)

    return decorator
