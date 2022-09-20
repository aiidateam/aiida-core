# -*- coding: utf-8 -*-
"""Utilities to define monitor functions for ``CalcJobs``."""
from __future__ import annotations

import collections
import dataclasses
from datetime import datetime, timedelta
import inspect
import typing as t

from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.orm import CalcJobNode, Dict
from aiida.plugins import BaseFactory
from aiida.transports import Transport

LOGGER = AIIDA_LOGGER.getChild(__name__)


@dataclasses.dataclass
class CalcJobMonitor:
    """Data class representing a monitor for a ``CalcJob``."""

    entry_point: str
    """Entry point in the ``aiida.calculations.monitors`` group implementing the monitor interface."""

    kwargs: dict[t.Any, t.Any] = dataclasses.field(default_factory=dict)
    """Keyword arguments that will be passed to the monitor when invoked (should be JSON serializable)."""

    priority: int = 0
    """Determines the order in which monitors should be executed in the case of multiple monitors."""

    minimum_poll_interval: int | None = None
    """Optional minimum poll interval. If set, subsequent calls should be at least this many seconds apart."""

    call_timestamp: datetime | None = None
    """Optional datetime representing the last time this monitor was called."""

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
        type_check(self.priority, int)
        type_check(self.minimum_poll_interval, int, allow_none=True)

        if self.minimum_poll_interval is not None and self.minimum_poll_interval <= 0:
            raise ValueError('The `minimum_poll_interval` must be a positive integer greater than zero.')

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


class CalcJobMonitors:
    """Collection of ``CalcJobMonitor`` instances.

    The collection is initialized from a dictionary where the values are the parameters for initializing an instance of
    :class:`~aiida.engine.processes.calcjobs.monitors.CalcJobMonitor`, which are stored as an ordered dictionary. The
    monitors are sorted according to the priority set for the monitors (reversed, i.e., from high to low) and second
    alphabetically on their key.

    The :meth:`~aiida.engine.processes.calcjobs.monitors.CalcJobMonitors.process` method can be called providing an
    instance of a ``CalcJobNode`` and a ``Transport`` and it will iterate over the collection of monitors, executing
    each monitor in order, and stopping on the first to return a ``CalcJobMonitorResult`` to pass it up to its caller.
    """

    def __init__(self, monitors: dict[str, Dict]):
        type_check(monitors, dict)

        if any(not isinstance(monitor, Dict) for monitor in monitors.values()):
            raise TypeError('at least one value of `monitors` is not a `Dict` node.')

        monitors = {key: CalcJobMonitor(**node.get_dict()) for key, node in monitors.items()}
        self._monitors = collections.OrderedDict(sorted(monitors.items(), key=lambda x: (-x[1].priority, x[0])))

    @property
    def monitors(self) -> collections.OrderedDict:
        """Return an ordered dictionary of the monitor collection.

        Monitors are first sorted on their priority (reversed, i.e., from high to low) and second on their key.

        :returns: Ordered dictionary of monitors..
        """
        return self._monitors

    def process(self, node: CalcJobNode, transport: Transport) -> str | None:
        """Call all monitors in order and return the result as one returns anything other than ``None``.

        :param node: The node to pass to the monitor invocation.
        :param transport: The transport to pass to the monitor invocation.
        :returns: ``None`` or a monitor result.
        """
        for key, monitor in self.monitors.items():

            if (
                monitor.minimum_poll_interval and monitor.call_timestamp and
                datetime.now() - monitor.call_timestamp < timedelta(seconds=monitor.minimum_poll_interval)
            ):
                LOGGER.debug(f'skipping monitor `{key}` because minimum poll interval has not expired yet.')
                continue

            monitor_function = monitor.load_entry_point()

            LOGGER.debug(f'calling monitor `{key}`')
            monitor.call_timestamp = datetime.now()
            monitor_result = monitor_function(node, transport, **monitor.kwargs)

            if monitor_result is not None:
                LOGGER.warning(monitor_result)
                return f'Monitor `{monitor.entry_point}` killed job with message: {monitor_result}'
