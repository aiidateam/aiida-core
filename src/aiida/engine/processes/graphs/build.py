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
    CONDITION_PORT,
    DEFINED_TASKS,
    BranchTask,
    Dependency,
    Endpoint,
    GraphSpec,
    GraphTask,
    LoopTask,
    MapTask,
    ProcessTask,
    SubgraphTask,
    TaskSpec,
    port_names,
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
    'ProcessHandle',
    'TaskHandle',
    'TaskOutput',
    'TaskOutputs',
    'branch',
    'each',
    'graph',
    'loop',
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
    """References to the outputs that a task placed in a graph will produce.

    A namespace among them is another of these, so an output inside one is reached the way it is written, one
    name at a time, and what comes out at the end is a reference to that one port.
    """

    _output_class: t.ClassVar[type[TaskOutput]] = TaskOutput

    def __init__(self, task: str, ports: t.Mapping[str, t.Any], prefix: str = '') -> None:
        self.task = task
        self.ports = ports
        self.prefix = prefix

    def __getattr__(self, name: str) -> t.Any:
        # Only called for names that are not real attributes, so the ports cannot shadow ``task`` or ``ports``.
        ports = self.__dict__.get('ports', {})

        if name not in ports:
            raise AttributeError(f'`{self.__dict__.get("task")}` has no output `{self._path(name)}`.')

        return self._reference(name)

    def _path(self, name: str) -> str:
        """Return the full name of one of these outputs, which for one in a namespace names the way to it."""
        return f'{self.__dict__.get("prefix", "")}{name}'

    def _reference(self, name: str) -> t.Any:
        """Return the reference to one of these outputs, which for a namespace is the outputs under it."""
        task, under = self.__dict__['task'], self.__dict__['ports'][name]

        if under is None:
            return self._output_class(task=task, port=self._path(name))

        return type(self)(task=task, ports=under, prefix=f'{self._path(name)}.')

    def sole(self) -> TaskOutput:
        """Return the only output of the task.

        :raises ValueError: if the task does not declare exactly one output, or if the one it declares is a
            namespace, since in neither case is there a single port to take.
        """
        if len(self.ports) != 1:
            named = f'{self.task}.{self._path(next(iter(self.ports)))}' if self.ports else f'{self.task}....'
            raise ValueError(
                f'`{self.task}` declares {len(self.ports)} outputs {list(self.ports)}, so one of them has to be '
                f'named, for example `{named}`.'
            )

        (name,) = self.ports
        only = self._reference(name)

        if isinstance(only, TaskOutputs):
            raise ValueError(
                f'`{self.task}` declares `{self._path(name)}`, which is a namespace, so a port inside it has to '
                f'be named, for example `{self.task}.{only._path(next(iter(only.ports), "..."))}`.'
            )

        return only


class MappedOutputs(TaskOutputs):
    """References to the outputs of a task that runs once per item, each of them a result per item."""

    _output_class: t.ClassVar[type[TaskOutput]] = MappedOutput


def _arguments(function: t.Callable[..., t.Any], *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
    """Return the arguments of a call, by the name of the parameter each is bound to."""
    bound = inspect.signature(function).bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


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

    def __init__(self, parameters: t.Sequence[str] = ()) -> None:
        self._tasks: list[GraphTask] = []
        self._dependencies: list[Dependency] = []
        self._inputs: dict[str, list[tuple[str, str]]] = {name: [] for name in parameters}
        self._used: Counter[str] = Counter()

    @property
    def _placed(self) -> set[str]:
        """Return the names of the tasks placed in the graph so far."""
        return {task.name for task in self._tasks}

    def add_task(self, handle: TaskHandle, arguments: dict[str, t.Any]) -> TaskOutputs:
        """Place a task in the graph, and record where each of its inputs comes from.

        :param handle: the task being placed.
        :param arguments: the arguments of the call, by parameter name.
        :return: references to the outputs the task will produce.
        :raises ValueError: if more than one input is marked with :func:`each`.
        """
        name = self._unique_name(handle.task_spec.identifier)
        item_ports = [key for key, argument in arguments.items() if isinstance(argument, Each)]
        values = {
            key: argument.collection if isinstance(argument, Each) else argument for key, argument in arguments.items()
        }

        task = self._task(name, handle, self._wire(name, values), item_ports)
        self._tasks.append(task)
        outputs_class = MappedOutputs if isinstance(task, MapTask) else TaskOutputs

        return outputs_class(task=name, ports=port_names(handle.task_spec.outputs))

    def add_graph(self, handle: GraphHandle, arguments: dict[str, t.Any]) -> TaskOutputs:
        """Place a graph inside the graph being built, and record where each of its inputs comes from.

        The body is built here, so what is placed is the declaration of that graph, and the inputs and outputs it
        declares are the ports the graph around it wires to.

        :param handle: the graph being placed.
        :param arguments: the arguments of the call, by parameter name.
        :return: references to the outputs the graph will produce.
        :raises ValueError: if the call marks one of the inputs with :func:`each`.
        """
        self._refuse_each(handle.identifier, 'graph', arguments)

        body = handle.build()
        name = self._unique_name(handle.identifier)
        self._tasks.append(SubgraphTask(name=name, inputs=self._wire(name, arguments), body=body))

        return TaskOutputs(task=name, ports=dict.fromkeys(body.outputs))

    def add_branch(
        self,
        condition: t.Any,
        *,
        then: GraphHandle,
        otherwise: GraphHandle | None,
        arguments: dict[str, t.Any],
    ) -> TaskOutputs:
        """Place a branch in the graph being built, and record where its condition and inputs come from.

        Both branches are built here, so the declaration still describes every run and the only thing left to a
        run is which of the two it takes.

        :param condition: what decides between the branches, from a task or an input of the graph.
        :param then: the graph to run when the condition holds.
        :param otherwise: the graph to run when it does not, if there is one.
        :param arguments: the inputs of the branches, by parameter name.
        :return: references to the outputs the branch will produce.
        :raises ValueError: if the call marks the condition or one of the inputs with :func:`each`.
        """
        wired = {**arguments, CONDITION_PORT: condition}
        self._refuse_each(then.identifier, 'branch', wired)

        body = then.build()
        other = None if otherwise is None else otherwise.build()
        name = self._unique_name(f'branch_{then.identifier}')

        self._tasks.append(BranchTask(name=name, inputs=self._wire(name, wired), body=body, otherwise=other))

        return TaskOutputs(task=name, ports=dict.fromkeys(body.outputs))

    def add_loop(
        self,
        body: GraphHandle,
        *,
        condition: str,
        max_iterations: int,
        arguments: dict[str, t.Any],
    ) -> TaskOutputs:
        """Place a loop in the graph being built, and record where the values it starts from come from.

        :param body: the graph to run again and again.
        :param condition: name of the value deciding whether to go round again.
        :param max_iterations: how many times the body may run before the loop gives up.
        :param arguments: the values the loop starts from, by the name the body declares.
        :return: references to the outputs the loop will produce.
        :raises ValueError: if the call marks one of the values with :func:`each`.
        """
        self._refuse_each(body.identifier, 'loop', arguments)

        name = self._unique_name(f'loop_{body.identifier}')
        task = LoopTask(
            name=name,
            inputs=self._wire(name, arguments),
            body=body.build(),
            condition_port=condition,
            max_iterations=max_iterations,
        )
        self._tasks.append(task)

        return TaskOutputs(task=name, ports=dict.fromkeys(task.body.outputs))

    @staticmethod
    def _refuse_each(identifier: str, kind: str, arguments: dict[str, t.Any]) -> None:
        """Raise if a call that cannot fan out marks one of its inputs with :func:`each`."""
        mapped = sorted(key for key, argument in arguments.items() if isinstance(argument, Each))

        if mapped:
            raise ValueError(
                f'`{identifier}` is a {kind} and {mapped} marks it to run once per item. Running a {kind} once '
                f'per item is not supported yet; place a task that fans out inside it.'
            )

    def _wire(self, name: str, arguments: dict[str, t.Any], prefix: str = '') -> dict[str, t.Any]:
        """Return the arguments that are plain values, recording where each of the others comes from.

        An argument that stands for an output of another task, or for an input of the graph, records a dependency
        rather than a value, which is what wires the graph together. A dictionary holding one of those is a
        namespace being filled in, so it is walked into and its entries are wired under their own names.

        :param name: the name the task is placed under, which the dependencies are recorded against.
        :param prefix: the namespace the arguments sit in, which their names are recorded under.
        :raises ValueError: if an argument comes from outside this graph, comes from a task that fans out, or
            carries either of those inside something that is not a namespace.
        """
        inputs = {}

        for key, value in arguments.items():
            port = f'{prefix}{key}'

            if isinstance(value, GraphInput):
                if value.name not in self._inputs:
                    self._refuse_foreign(name, port, value.name)

                self._inputs[value.name].append((name, port))
                continue

            reference = _as_reference(value)

            if isinstance(reference, MappedOutput):
                raise ValueError(
                    f'`{name}` takes `{port}` from `{reference.task}`, which runs once per item and so has a '
                    f'result per item, where `{port}` takes one value. Taking the results of a fan-out into '
                    f'another task is not supported yet; a graph can return them.'
                )

            if reference is not None:
                if reference.task not in self._placed:
                    self._refuse_foreign(name, port, reference.task)

                self._dependencies.append(
                    Dependency(source=reference.task, source_port=reference.port, target=name, target_port=port)
                )
                continue

            if isinstance(value, dict) and _holds_reference(value):
                inputs[key] = self._wire(name, value, prefix=f'{port}.')
                continue

            if _holds_reference(value):
                raise ValueError(
                    f'`{name}` takes `{port}` with the output of another task inside a '
                    f'{type(value).__name__}, which would be stored as a value and leave that task unwaited for. '
                    f'Pass the output itself, or take the collection from a task that produces one.'
                )

            inputs[key] = value

        return inputs

    @staticmethod
    def _refuse_foreign(name: str, key: str, origin: str) -> t.NoReturn:
        """Raise for an argument standing for something that belongs to a graph around this one."""
        raise ValueError(
            f'`{name}` takes `{key}` from `{origin}`, which is not part of this graph. A graph written inside '
            f'another reaches nothing outside itself, so take `{origin}` as a parameter of this graph and pass '
            f'it in where the graph is placed.'
        )

    @staticmethod
    def _task(name: str, handle: TaskHandle, inputs: dict[str, t.Any], item_ports: list[str]) -> ProcessTask:
        """Return the task for a call, which fans out when one of its inputs was marked with :func:`each`."""
        if not item_ports:
            return ProcessTask(name=name, spec=handle.task_spec, inputs=inputs)

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
        builder = ACTIVE_BUILDER.get()

        if builder is None:
            raise TypeError(
                f'`{self.identifier}` declares a graph, so it is launched rather than called. Pass it to `run` or '
                f'`submit`, as any other process, or use `.build(...)` for the declaration on its own.'
            )

        return builder.add_graph(self, _arguments(self._function, *args, **kwargs))

    def build(self) -> GraphSpec:
        """Return the graph that the function declares.

        The body is traced once with each of its parameters standing for an input of the graph, so the result is
        the same declaration for every run and the values are what a run supplies.
        """
        builder = GraphBuilder(self.parameters)
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
        return GraphProcess.launch_inputs(self.build(), _arguments(self._function, *args, **kwargs))


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


def branch(
    condition: t.Any,
    *,
    then: GraphHandle,
    otherwise: GraphHandle | None = None,
    **inputs: t.Any,
) -> TaskOutputs:
    """Run one of two graphs, depending on a value that only exists once the graph is running.

    Both branches are graphs, so what a branch takes and produces is what it declares, and the outputs of the
    whole branch are those of the graph that ran. Both branches have to return the same outputs, so that what
    comes after the branch does not depend on which side was taken.

    Example usage:

    >>> @graph
    >>> def refine(structure):
    >>>     return relax(structure=structure)
    >>>
    >>> @graph
    >>> def workflow(structure, refine_it):
    >>>     first = relax(structure=structure)
    >>>     return branch(refine_it, then=refine, structure=first.structure)

    Without an ``otherwise``, a condition that does not hold leaves the branch producing nothing, and every task
    that takes one of its outputs is left out of the run as well, as is any output of the graph that comes from
    one of them.

    :param condition: what decides between the branches, from a task or from an input of the graph.
    :param then: the graph to run when the condition holds.
    :param otherwise: the graph to run when it does not.
    :param inputs: the inputs of the branches, by the name each of them declares.
    :return: references to the outputs the branch will produce.
    :raises TypeError: if it is called outside the body of a graph, where there is nothing to place it in.
    """
    builder = ACTIVE_BUILDER.get()

    if builder is None:
        raise TypeError(
            '`branch` places a branch in a graph, so it is written in the body of a `@graph` function. To pick '
            'between two graphs outside of one, call the one you want.'
        )

    return builder.add_branch(condition, then=then, otherwise=otherwise, arguments=inputs)


def loop(
    body: GraphHandle,
    *,
    condition: str = CONDITION_PORT,
    max_iterations: int = 1000,
    **inputs: t.Any,
) -> TaskOutputs:
    """Run a graph again and again, on what the run before it produced, while a condition holds.

    Each run starts from what the one before it returned, with the values given here standing in for whatever the
    body does not produce. One of those values decides whether to go round again, so the body both takes it and
    returns it, which is what lets a loop be written without anything pointing backwards.

    Example usage:

    >>> @task(outputs=['value', 'again'])
    >>> def step(value):
    >>>     return value - 1, value - 1 > 0
    >>>
    >>> @graph
    >>> def countdown(value, again):
    >>>     stepped = step(value=value)
    >>>     return {'value': stepped.value, 'again': stepped.again}
    >>>
    >>> @graph
    >>> def count_down_to_zero(start):
    >>>     return loop(countdown, condition='again', value=start, again=True).value

    A condition that is false to begin with leaves the loop producing nothing, and every task that takes one of
    its outputs is left out of the run as well.

    :param body: the graph to run again and again.
    :param condition: name of the value deciding whether to go round again, which the body takes and returns.
    :param max_iterations: how many times the body may run before the loop gives up on the condition turning.
    :param inputs: the values the loop starts from, by the name the body declares.
    :return: references to the outputs the loop will produce, which are those of the run it stopped on.
    :raises TypeError: if it is called outside the body of a graph, where there is nothing to place it in.
    """
    builder = ACTIVE_BUILDER.get()

    if builder is None:
        raise TypeError(
            '`loop` places a loop in a graph, so it is written in the body of a `@graph` function. To run a graph '
            'once outside of one, pass it to `run` or `submit`.'
        )

    return builder.add_loop(body, condition=condition, max_iterations=max_iterations, arguments=inputs)


class ProcessHandle:
    """What :func:`task` returns for a process class: a task that can be placed in a graph.

    A process is already launchable on its own, so this adds only what a graph needs: calling it while one is
    being written places it, under the ports the process declares. Those ports are the ones it is given, without
    a signature to bind them to, since a process takes its inputs by name.
    """

    def __init__(self, process_class: type[Process], spec: TaskSpec) -> None:
        self._process_class = process_class
        self.task_spec = spec
        self.__name__ = process_class.__name__
        self.__doc__ = process_class.__doc__

    def __call__(self, **inputs: t.Any) -> TaskOutputs:
        builder = ACTIVE_BUILDER.get()

        if builder is None:
            raise TypeError(
                f'`{self.task_spec.identifier}` is a process, so on its own it is launched rather than called. '
                f'Pass it to `run` or `submit`, or call it while writing a graph to place it in one.'
            )

        return builder.add_task(self, inputs)

    @property
    def process_class(self) -> type[Process]:
        return self._process_class


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
        return _arguments(self._function, *args, **kwargs)

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

    A process class can be declared a task as well, which is how a ``CalcJob`` or a ``WorkChain`` is placed in a
    graph. It already declares its own ports, so ``outputs`` does not apply to one:

    >>> relaxed = task(PwRelaxWorkChain)
    >>>
    >>> @graph
    >>> def relax_and_report(structure):
    >>>     return report(structure=relaxed(structure=structure).output_structure)

    :param function: The function to decorate, or the process class to declare a task.
    :param outputs: Names of the output ports to declare.
    :param identifier: Name of the task, which defaults to the name of the function or class.
    :return: The decorated function, carrying its ``task_spec``, or a handle placing the process in a graph.
    :raises TypeError: if ``outputs`` is given for a process class, which declares its own.
    """

    if isinstance(function, type):
        if not issubclass(function, Process):
            raise TypeError(
                f'`{function.__name__}` is a class rather than a function, and only a process class can be a '
                f'task on its own. Decorate a function, or pass a `CalcJob` or `WorkChain`.'
            )

        if outputs is not None:
            raise TypeError(
                f'`{function.__name__}` is a process and declares its own output ports, so `outputs` does not '
                f'apply to it.'
            )

        return ProcessHandle(function, TaskSpec.from_process(function, identifier=identifier))

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
