###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapter module for optional aiida-workgraph integration.

This module provides a centralized location for checking availability
of aiida-workgraph components. It allows aiida-core to optionally support WorkGraph
processes without requiring aiida-workgraph as a dependency.

Usage:
    from aiida.common.workgraph import WORKGRAPH_AVAILABLE, is_workgraph_instance

    if is_workgraph_instance(process):
        # WorkGraph-specific code
        ...
"""

from __future__ import annotations

import typing as t

from aiida.common.exceptions import InvalidOperation
from aiida.common.log import AIIDA_LOGGER

# Check if aiida-workgraph is available
try:
    import aiida_workgraph  # type: ignore[import-not-found]  # noqa: F401

    WORKGRAPH_AVAILABLE = True
except ImportError:
    WORKGRAPH_AVAILABLE = False


def is_workgraph_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraph instance.

    This helper function safely checks if an object is a WorkGraph instance,
    returning False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraph instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph import WorkGraph

    return isinstance(obj, WorkGraph)


def is_workgraph_node_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraphNode instance.

    This helper function safely checks if an object is a WorkGraphNode instance,
    returning False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraphNode instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph.orm.workgraph import WorkGraphNode  # type: ignore[import-not-found]

    return isinstance(obj, WorkGraphNode)


LOGGER = AIIDA_LOGGER.getChild('engine.launch')

_WORKGRAPH_RUN_RESERVED_KEYS = {'metadata'}
_WORKGRAPH_SUBMIT_RESERVED_KEYS = {'metadata', 'timeout'}


def _merge_workgraph_inputs(
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
) -> dict[str, t.Any]:
    """Validate and return WorkGraph inputs from either ``inputs`` or ``kwargs``.

    Follows the same mutual exclusivity rule as :func:`aiida.engine.utils.prepare_inputs`:
    only one of ``inputs`` or ``kwargs`` may be provided.

    :param inputs: the input dictionary
    :param kwargs: additional keyword arguments as an alternative to ``inputs``
    :raises ValueError: if both ``inputs`` and ``kwargs`` are specified
    :return: inputs dictionary
    """
    if inputs is not None and kwargs:
        raise ValueError('Cannot specify both `inputs` and `kwargs`.')
    if inputs:
        return dict(inputs)
    if kwargs:
        return dict(kwargs)
    return {}


def _warn_reserved_key_collisions(process: t.Any, reserved_keys: set[str], popped_keys: set[str]) -> None:
    """Warn if any popped reserved keys also match a task name on the WorkGraph.

    :param process: the WorkGraph instance
    :param reserved_keys: the set of reserved key names
    :param popped_keys: the reserved keys that were actually present in the inputs
    """
    try:
        task_names = set(process.get_task_names())
    except (AttributeError, TypeError):
        return
    collisions = popped_keys & task_names
    if collisions:
        LOGGER.warning(
            f'Keys {collisions} were interpreted as execution parameters, but they also match task names '
            f'on this WorkGraph. If you intended to pass task inputs, rename the tasks to avoid '
            f'colliding with reserved keys: {reserved_keys}.'
        )


def engine_run_workgraph(
    process: t.Any,
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
) -> dict[str, t.Any]:
    """Run a WorkGraph process, returning its outputs.

    :param process: the WorkGraph instance
    :param inputs: the input dictionary
    :param kwargs: additional keyword arguments to be merged with inputs
    :raises ValueError: if the same key appears in both ``inputs`` and ``kwargs``
    :return: the outputs of the process
    """
    wg_inputs = _merge_workgraph_inputs(inputs, kwargs)
    popped_keys: set[str] = set()
    metadata = wg_inputs.pop('metadata', None)
    if metadata is not None:
        popped_keys.add('metadata')
    _warn_reserved_key_collisions(process, _WORKGRAPH_RUN_RESERVED_KEYS, popped_keys)
    result: dict[str, t.Any] = process.run(
        inputs=wg_inputs or None,
        metadata=metadata,
    )
    return result


def engine_submit_workgraph(
    process: t.Any,
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
    *,
    wait: bool,
    wait_interval: int,
) -> t.Any:
    """Submit a WorkGraph process, returning its process node.

    :param process: the WorkGraph instance
    :param inputs: the input dictionary
    :param kwargs: additional keyword arguments to be merged with inputs
    :param wait: whether to block until the process completes
    :param wait_interval: seconds between status checks when ``wait=True``
    :raises ValueError: if the same key appears in both ``inputs`` and ``kwargs``
    :raises InvalidOperation: if ``dry_run`` is requested (not supported by WorkGraph)
    :return: the process node
    """
    wg_inputs = _merge_workgraph_inputs(inputs, kwargs)
    popped_keys: set[str] = set()
    metadata = wg_inputs.pop('metadata', None)
    if metadata is not None:
        popped_keys.add('metadata')
    timeout = wg_inputs.pop('timeout', None)
    if timeout is not None:
        popped_keys.add('timeout')
    _warn_reserved_key_collisions(process, _WORKGRAPH_SUBMIT_RESERVED_KEYS, popped_keys)

    if metadata and metadata.get('dry_run', False):
        raise InvalidOperation('WorkGraph does not support `dry_run`.')

    # Warn if execution option names are found in task inputs (likely user error)
    if wg_inputs:
        suspicious_keys = [k for k in ('wait', 'interval') if k in wg_inputs]
        if suspicious_keys:
            LOGGER.warning(
                f'Found {suspicious_keys} in inputs dict. If these are meant as execution options, '
                f'pass them as function arguments: submit(wg, wait=..., wait_interval=...)'
            )

    submit_kwargs: dict[str, t.Any] = {
        'inputs': wg_inputs or None,
        'wait': wait,
        'interval': wait_interval,
        'metadata': metadata,
    }
    if timeout is not None:
        submit_kwargs['timeout'] = timeout
    return process.submit(**submit_kwargs)
