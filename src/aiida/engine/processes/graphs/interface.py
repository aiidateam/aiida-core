###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The handle every graph is launched through, however its body is read."""

from __future__ import annotations

import abc
import contextvars
import functools
import inspect
import typing as t
from collections.abc import Callable

from aiida.engine.processes.graphs.bindings import LAUNCH_BINDINGS, bind_declaration
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.spec import GraphSpec

__all__ = ('GraphHandle',)

ACTIVE_BUILDER: contextvars.ContextVar[t.Any | None] = contextvars.ContextVar(
    'aiida_active_graph_builder', default=None
)
"""The graph being built, if any.

While a graph is being built, calling a task records it in that graph instead of running it. This is what lets a
graph be written as ordinary Python.
"""


def _bind_arguments(function: Callable[..., t.Any], *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
    """Return the arguments of a call, by the name of the parameter each is bound to."""
    bound = inspect.signature(function).bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


class GraphHandle(abc.ABC):
    """What the :func:`graph` decorators return: a graph that can be built, run, or submitted.

    Execution graphs trace their bodies while source graphs lower their source, but both launch through this
    same handle, which is what lets the builder nest either flavour inside either.
    """

    def __init__(self, function: Callable[..., t.Any], identifier: str | None = None) -> None:
        self._function = function
        self.identifier = identifier or function.__name__
        functools.update_wrapper(self, function)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        builder = ACTIVE_BUILDER.get()

        if builder is None:
            msg = (
                f'`{self.identifier}` declares a graph, so it is launched rather than called. Pass it to `run` or '
                f'`submit`, as any other process, or use `.build(...)` for the declaration on its own.'
            )
            raise TypeError(msg)

        return builder.add_graph(self, _bind_arguments(self._function, *args, **kwargs))

    @abc.abstractmethod
    def build(self) -> GraphSpec:
        """Return the graph that the function declares."""

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
        # Omitted parameters must reach the recursive graph validator. Binding
        # still rejects duplicates and unknown arguments; nested build calls keep
        # the strict binding used by __call__.
        bound = inspect.signature(self._function).bind_partial(*args, **kwargs)
        bindings: dict[str, t.Any] = {}
        token = LAUNCH_BINDINGS.set(bindings)
        try:
            body = self.build()
        finally:
            LAUNCH_BINDINGS.reset(token)
        return GraphProcess.launch_inputs(body, dict(bound.arguments), bindings=bindings)

    def bind_tasks(self, **tasks: t.Any) -> GraphHandle:
        """Return an independently bound graph, keyed by task placement name.

        Source bodies continue to call ordinary registered process handles. This method
        supplies run-specific prepared handles without mutating those registrations.

        :param tasks: prepared process handles, keyed by names in the declaration.
        :return: a new launchable handle whose bindings are separate from its declaration.
        """
        return BoundGraphHandle(self, tasks)


class BoundGraphHandle(GraphHandle):
    """A declaration and its independently owned prepared task handles."""

    def __init__(self, graph: GraphHandle, tasks: dict[str, t.Any]) -> None:
        super().__init__(graph._function, graph.identifier)
        self._graph = graph
        self._tasks = dict(tasks)
        for name, handle in tasks.items():
            if not getattr(handle, 'is_prepared', False):
                msg = f'Binding `{name}` requires a prepared process handle.'
                raise TypeError(msg)

    def build(self) -> GraphSpec:
        return bind_declaration(self._graph.build(), self._tasks)
