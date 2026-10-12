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

import functools
import inspect
import typing as t
from collections.abc import Callable
from dataclasses import replace

from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.spec import GraphSpec

__all__ = ('GraphHandle',)


class GraphHandle:
    """An importable source declaration that builds without executing its body."""

    def __init__(self, function: Callable[..., t.Any], identifier: str | None = None) -> None:
        self._function = function
        self.identifier = identifier or function.__name__
        functools.update_wrapper(self, function)

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.NoReturn:
        msg = f'`{self.identifier}` declares a graph; launch it with `run` or `submit`, or inspect `.build()`.'
        raise TypeError(msg)

    @property
    def function(self) -> Callable[..., t.Any]:
        """Return the declared function for the lowering pipeline."""
        return self._function

    def build(self) -> GraphSpec:
        """Return the graph that the function declares, lowered from its registered source."""
        # Deferred: that module imports this one at top level.
        from aiida.engine.processes.graphs.build_source import build_from_source

        return replace(build_from_source(self.function), identifier=self.identifier)

    @property
    def process_class(self) -> type[GraphProcess]:
        """Return the process class executing lowered graphs."""
        return GraphProcess

    def get_launch_inputs(self, **inputs: t.Any) -> dict[str, t.Any]:
        """Validate graph arguments and prepare the declaration and provenance inputs."""
        parameters = [
            parameter.replace(kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
            if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.KEYWORD_ONLY)
            else parameter
            for parameter in inspect.signature(self._function).parameters.values()
        ]
        bound = inspect.Signature(parameters).bind_partial(**inputs)
        return GraphProcess.launch_inputs(self.build(), dict(bound.arguments))
