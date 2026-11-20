###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Bind and apply versioned placement recovery policies."""

from __future__ import annotations

import typing as t
from collections.abc import Mapping

from aiida.common.exceptions import GraphValidationError
from aiida.engine.execution import IncreaseMemory, RetryPolicy, SchedulerFailure
from aiida.engine.processes.calcjobs.calcjob import CalcJob
from aiida.engine.processes.graphs.runtime_config import _merge_runtime_inputs, _runtime_placements

if t.TYPE_CHECKING:
    from aiida.engine.processes.graphs.ir import GraphIR
    from aiida.orm import Computer

_OOM = SchedulerFailure.OUT_OF_MEMORY
_POLICY_VERSION = 1


def _at_placement(mapping: Mapping[str, t.Any], path: tuple[str, ...]) -> t.Any:
    for name in path:
        mapping = mapping.get(name, {})
    return mapping


def _policy_error(path: tuple[str, ...], reason: str) -> GraphValidationError:
    return GraphValidationError(f'execution_policy placement `{".".join(path)}`: {reason}')


def _decode_policy(value: object) -> RetryPolicy:
    """Load a constrained policy from the internal, versioned launch envelope."""
    if isinstance(value, Mapping) and value.keys() == {'version', 'max_attempts', 'on'}:
        if (
            value['version'] == _POLICY_VERSION
            and isinstance(value['on'], Mapping)
            and value['on'].keys() == {_OOM.value}
        ):
            action = value['on'][_OOM.value]
            if isinstance(action, Mapping) and action.keys() == {'action', 'factor', 'maximum_kb'}:
                if action['action'] == 'increase_memory':
                    return RetryPolicy(
                        max_attempts=value['max_attempts'],
                        on={_OOM: IncreaseMemory(factor=action['factor'], maximum_kb=action['maximum_kb'])},
                    )
    msg = 'expected a RetryPolicy snapshot with a supported version and action.'
    raise ValueError(msg)


def _encode_policy(policy: RetryPolicy) -> dict[str, t.Any]:
    action = policy.on[_OOM]
    return {
        'version': _POLICY_VERSION,
        'max_attempts': policy.max_attempts,
        'on': {_OOM.value: {'action': 'increase_memory', 'factor': action.factor, 'maximum_kb': action.maximum_kb}},
    }


def _bind_execution_policy(
    graph: GraphIR, config: Mapping[str, t.Any], provided: object, *, from_snapshot: bool = False
) -> dict[str, t.Any]:
    """Validate and snapshot a policy tree using the same addresses as runtime configuration."""
    if not isinstance(provided, Mapping):
        msg = '`execution_policy` must be a mapping keyed by placement path.'
        raise GraphValidationError(msg)
    if not provided:
        return {}
    placements = list(_runtime_placements(graph))
    addresses = {address for address, _, _ in placements}

    def visit(values: Mapping[str, t.Any], prefix: tuple[str, ...] = ()) -> dict[str, t.Any]:
        result = {}
        for name, value in values.items():
            if not isinstance(name, str):
                raise _policy_error(prefix, 'placement names must be strings.')
            path = (*prefix, name)
            nested = any(other[: len(path)] == path and len(other) > len(path) for other in addresses)
            if path in addresses:
                if nested:
                    raise _policy_error(path, 'ambiguous process and nested graph placement.')
                if from_snapshot:
                    try:
                        policy = _decode_policy(value)
                    except ValueError as exc:
                        raise _policy_error(path, str(exc)) from exc
                elif type(value) is RetryPolicy:
                    policy = value
                else:
                    raise _policy_error(path, 'expected a RetryPolicy.')
                result[name] = _encode_policy(policy)
            elif nested:
                if not isinstance(value, Mapping):
                    raise _policy_error(path, 'expected a mapping of nested placements.')
                result[name] = visit(value, path)
            else:
                raise _policy_error(path, 'unknown placement path.')
        return result

    snapshot = visit(provided)
    for path, task, _ in placements:
        if not (value := _at_placement(snapshot, path)):
            continue
        if not issubclass(task.spec.process_class, CalcJob):
            raise _policy_error(path, 'only scheduler-backed CalcJob placements support memory recovery.')
        configured = _at_placement(config, path)
        memory = configured.get('metadata', {}).get('options', {}).get('max_memory_kb')
        if type(memory) is not int or memory < 1:
            raise _policy_error(path, 'set a positive explicit metadata.options.max_memory_kb in runtime_config.')
        # Full inputs can depend on upstream results. Validate what is known now, then
        # check actual options (including defaults) before dispatching each attempt.
        inputs = _merge_runtime_inputs(task, configured, task.inputs)
        try:
            _validate_memory(inputs, _decode_policy(value).on[_OOM], require_computer=False)
        except ValueError as exc:
            raise _policy_error(path, str(exc)) from exc
    return snapshot


def _computer(inputs: Mapping[str, t.Any]) -> Computer | None:
    code = inputs.get('code')
    return (code.computer if code is not None else None) or inputs.get('metadata', {}).get('computer')


def _validate_memory(
    inputs: Mapping[str, t.Any], action: IncreaseMemory, *, require_computer: bool = True
) -> int | None:
    """Return the effective scheduler request after checking limits and target capabilities."""
    metadata = inputs.get('metadata', {})
    if inputs.get('remote_folder') is not None or metadata.get('dry_run'):
        msg = 'memory recovery requires a submitted calculation, not a dry run or import.'
        raise ValueError(msg)
    options = metadata.get('options', {})
    request = options.get('max_memory_kb')
    if type(request) is not int or not 0 < request <= action.maximum_kb:
        msg = 'metadata.options.max_memory_kb must be positive and no larger than the policy maximum_kb.'
        raise ValueError(msg)
    computer = _computer(inputs)
    if computer is not None:
        return computer.get_scheduler().get_effective_memory_request(options)
    if require_computer:
        msg = 'memory recovery requires a computer with a supported scheduler.'
        raise ValueError(msg)
    return None


def _validate_attempt(process_class: type[CalcJob], inputs: dict[str, t.Any], policy: RetryPolicy) -> int:
    """Validate the complete child launch with the ordinary CalcJob ports."""
    ports = process_class.spec().inputs
    prepared = ports.prepare(ports.pre_process(ports.serialize(inputs) or {})).runtime
    assert isinstance(prepared, Mapping)
    error = ports.validate(prepared)
    if error:
        raise ValueError(str(error))
    effective = _validate_memory(prepared, policy.on[_OOM])
    assert effective is not None
    return effective
