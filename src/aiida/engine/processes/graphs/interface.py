###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The launch contract of a source-declared graph."""

from __future__ import annotations

import abc
import functools
import inspect
import typing as t
from collections.abc import Callable

from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.spec import GraphSpec

__all__ = ('GraphHandle',)


class GraphHandle(abc.ABC):
    """An importable source declaration that builds without executing its body."""

    def __init__(self, function: Callable[..., t.Any], identifier: str | None = None) -> None:
        self._function = function
        self.identifier = identifier or function.__name__
        functools.update_wrapper(self, function)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.NoReturn:
        msg = f'`{self.identifier}` declares a graph; launch it with `run` or `submit`, or inspect `.build()`.'
        raise TypeError(msg)

    @abc.abstractmethod
    def build(self) -> GraphSpec:
        """Lower the graph source without executing the function."""

    @property
    def process_class(self) -> type[GraphProcess]:
        return GraphProcess

    def get_launch_inputs(self, *args: t.Any, **kwargs: t.Any) -> dict[str, t.Any]:
        """Validate graph arguments and prepare the declaration and provenance inputs."""
        bound = inspect.signature(self._function).bind_partial(*args, **kwargs)
        return GraphProcess.launch_inputs(self.build(), dict(bound.arguments))
