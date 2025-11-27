"""Utilities to define monitor functions for ``CalcJobs``."""

from __future__ import annotations

import collections
import dataclasses
import enum
import inspect
import typing as t
from datetime import datetime, timedelta

from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.orm import CalcJobNode, Dict
from aiida.plugins import BaseFactory

if t.TYPE_CHECKING:
    from aiida.transports import Transport

LOGGER = AIIDA_LOGGER.getChild(__name__)


class CalcJobMonitorAction(enum.Enum):
    """The action a engine should undertake as a result of a monitor."""

    KILL = 'kill'  # The job should be killed and no other monitors should be called.
    DISABLE_ALL = 'disable-all'  # All monitors should be disabled for the continued duration of the current job
    DISABLE_SELF = 'disable-self'  # Disable the monitor that returns a result with this action.


@dataclasses.dataclass
class CalcJobMonitorResult:
    """Data class representing the result of a monitor."""

    key: str | None = None
    """Key of the monitor in the ``monitors`` input namespace. Will be set automatically by the engine."""

    message: str | None = None
    """Human readable message: could be a warning or an error message."""

    action: CalcJobMonitorAction = CalcJobMonitorAction.KILL
    """The action the engine should take."""

    retrieve: bool = True
    """If set to ``False``, the engine will skip retrieving the output files."""

    parse: bool = True
    """If set to ``False``, the engine will skip the parsing of the retrieved files, if one was specified in inputs."""

    override_exit_code: bool = True
    """If set to ``False``, the engine will keep the exit code returned by the parser."""

    outputs: dict[str, t.Any] | None = None
    """Optional dictionary of output nodes to be attached to the process."""

    def __post_init__(self):
        """Validate the attributes."""
        self.validate()

    def validate(self):
        """Validate the instance.

        :raises TypeError: If any of the attributes are of the incorrect type.
        :raises ValueError: If ``parse == True`` and ``retrieve == False``.
        """
        type_check(self.key, str, allow_none=True)
        type_check(self.message, str, allow_none=True)
        type_check(self.action, CalcJobMonitorAction)
        type_check(self.retrieve, bool)
        type_check(self.parse, bool)
        type_check(self.override_exit_code, bool)

        if self.retrieve is False and self.parse is True:
            raise ValueError('`parse` cannot be `True` if `retrieve` is `False`.')


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

    disabled: bool = False
    """If this attribute is set to ``True`` the monitor should not be called when monitors are processed."""

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
        type_check(self.disabled, bool)

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

    def load_entry_point(self):
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
        """Construct a new instance."""
        type_check(monitors, dict)

        if any(not isinstance(monitor, Dict) for monitor in monitors.values()):
            raise TypeError('at least one value of `monitors` is not a `Dict` node.')

        calcjob_monitors = {key: CalcJobMonitor(**node.get_dict()) for key, node in monitors.items()}
        self._monitors = collections.OrderedDict(sorted(calcjob_monitors.items(), key=lambda x: (-x[1].priority, x[0])))

    @property
    def monitors(self) -> collections.OrderedDict:
        """Return an ordered dictionary of the monitor collection.

        Monitors are first sorted on their priority (reversed, i.e., from high to low) and second on their key.

        :returns: Ordered dictionary of monitors..
        """
        return self._monitors

    def process(
        self,
        node: CalcJobNode,
        transport: Transport,
    ) -> CalcJobMonitorResult | None:
        """Call all monitors in order and return the result as one returns anything other than ``None``.

        :param node: The node to pass to the monitor invocation.
        :param transport: The transport to pass to the monitor invocation.
        :returns: ``None`` or a monitor result.
        """
        for key, monitor in self.monitors.items():
            if monitor.disabled:
                LOGGER.debug(f'monitor`{key}` is disabled, skipping')
                continue

            if (
                monitor.minimum_poll_interval
                and monitor.call_timestamp
                and datetime.now() - monitor.call_timestamp < timedelta(seconds=monitor.minimum_poll_interval)
            ):
                LOGGER.debug(f'skipping monitor `{key}` because minimum poll interval has not expired yet.')
                continue

            monitor_function = monitor.load_entry_point()

            LOGGER.debug(f'calling monitor `{key}`')
            monitor.call_timestamp = datetime.now()
            monitor_result = monitor_function(node, transport, **monitor.kwargs)

            if isinstance(monitor_result, str):
                monitor_result = CalcJobMonitorResult(message=monitor_result)

            if isinstance(monitor_result, CalcJobMonitorResult):
                monitor_result.key = key

            if monitor_result:
                LOGGER.info(f'Monitor `{key}` returned: {monitor_result}')
                return monitor_result
        return None
