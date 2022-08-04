# -*- coding: utf-8 -*-
"""Utilities to define monitor functions for ``CalcJobs``."""
from __future__ import annotations

import dataclasses
import inspect
import typing as t

from aiida.common.lang import type_check
from aiida.plugins import BaseFactory


@dataclasses.dataclass
class CalcJobMonitor:
    """Data class representing a monitor for a ``CalcJob``."""

    entry_point: str
    """Entry point in the ``aiida.calculations.monitors`` group implementing the monitor interface."""

    kwargs: dict[t.Any, t.Any] = dataclasses.field(default_factory=dict)
    """Keyword arguments that will be passed to the monitor when invoked (should be JSON serializable)."""

    def __post_init__(self):
        """Validate the attributes."""
        self.validate()

    def validate(self):
        """Validate the monitor.

        :raises EntryPointError: If the entry point does not exist or cannot be loaded.
        :raises TypeError: If any of the attributes are of the incorrect type.
        :raises ValueError: If the entry point has an incorrect function signature.
        :raises ValueError: If the kwargs specified are not recognized by the function associated with the entry point.
        """
        type_check(self.entry_point, str)
        type_check(self.kwargs, dict)

        monitor = self.load_entry_point()
        signature = inspect.signature(monitor)
        parameters = list(signature.parameters.keys())

        if any(required_parameter not in parameters for required_parameter in ('node', 'transport')):
            correct_signature = '(node: CalcJobNode, transport: Transport, **kwargs) str | None:'
            raise ValueError(
                f'The monitor `{self.entry_point}` has an invalid function signature, it should be: {correct_signature}'
            )

        unsupported_kwargs = [kwarg for kwarg in self.kwargs if kwarg not in parameters]

        if unsupported_kwargs:
            raise ValueError(f'The monitor `{self.entry_point}` does not accept the keywords: {unsupported_kwargs}.')

    def load_entry_point(self) -> type:
        """Return the function associated with the entry point of this monitor.

        :raises EntryPointError: If the entry point does not exist or cannot be loaded.
        """
        return BaseFactory('aiida.calculations.monitors', self.entry_point)
