###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Launch descriptions for graph execution and plugin-prepared runs."""

from __future__ import annotations

import math
import typing as t
from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType

from aiida.common.datastructures import SchedulerFailure

__all__ = ('ExecutionEnvironment', 'IncreaseMemory', 'PreparedRun', 'RetryPolicy', 'SchedulerFailure')


@t.final
@dataclass(frozen=True, slots=True, kw_only=True)
class IncreaseMemory:
    """Grow an explicit memory request without exceeding the configured ceiling.

    :param factor: Finite multiplier greater than one.
    :param maximum_kb: Positive ceiling in kB, including any applicable queue limit.
    """

    factor: float
    maximum_kb: int

    def __post_init__(self) -> None:
        try:
            valid = type(self.factor) in (float, int) and math.isfinite(self.factor) and self.factor > 1
        except OverflowError:
            valid = False
        if not valid:
            msg = 'memory growth factor must be finite and greater than one.'
            raise ValueError(msg)
        if type(self.maximum_kb) is not int or self.maximum_kb < 1:
            msg = 'maximum_kb must be a positive integer.'
            raise ValueError(msg)

    def _next_request(self, previous: int) -> int:
        """Round up to kB without floating point overflow or exceeding the ceiling."""
        return min(self.maximum_kb, math.ceil(previous * Fraction(str(self.factor))))


@t.final
@dataclass(frozen=True, slots=True, kw_only=True)
class RetryPolicy:
    """Retry a logical placement when a supported scheduler failure is confirmed.

    :param max_attempts: Positive total launch budget, including the original attempt.
    :param on: Recovery actions keyed by normalized scheduler failure.
    """

    max_attempts: int
    on: Mapping[SchedulerFailure, IncreaseMemory]

    def __post_init__(self) -> None:
        if type(self.max_attempts) is not int or self.max_attempts < 1:
            msg = 'max_attempts must be a positive integer including the original attempt.'
            raise ValueError(msg)
        if (
            list(self.on) != [SchedulerFailure.OUT_OF_MEMORY]
            or type(self.on[SchedulerFailure.OUT_OF_MEMORY]) is not IncreaseMemory
        ):
            msg = 'on must map SchedulerFailure.OUT_OF_MEMORY to IncreaseMemory.'
            raise ValueError(msg)
        object.__setattr__(self, 'on', MappingProxyType(dict(self.on)))


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionEnvironment:
    """Package both graph execution channels; launching snapshots their contents.

    :param runtime_config: Execution inputs keyed by static placement address.
    :param execution_policy: Recovery policies keyed by the same placement address.
    """

    runtime_config: Mapping[str, t.Any] = field(default_factory=dict)
    execution_policy: Mapping[str, t.Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedRun:
    """Inputs and environment resolved by a plugin-owned scientific protocol.

    Pass this to a graph using ``prepared_run=``, instead of separate launch inputs.
    Plugin resolvers own role-to-placement mapping and any provenance-producing preparation steps.

    :param inputs: Explicit scientific inputs for the graph.
    :param execution_environment: Resolved execution settings and policies.
    :param protocol: Protocol identifier (ideally qualified by plugin).
    :param version: Version identifying the protocol definition.
    :param overrides: Explicit JSON-compatible overrides to record on the graph node.
    """

    inputs: Mapping[str, t.Any]
    execution_environment: ExecutionEnvironment
    protocol: str
    version: str
    overrides: Mapping[str, t.Any] = field(default_factory=dict)
