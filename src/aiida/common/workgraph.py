###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Adapter module for optional aiida-workgraph integration.

Provides helpers for detecting WorkGraph instances and preparing their inputs
for launch through the standard ``aiida.engine`` launch functions.
"""

# mypy: disable-error-code="unused-ignore"
# aiida-workgraph is an optional dependency: mypy raises import-not-found when
# it is absent and import-untyped when it is present.  Both codes are needed in
# type-ignore comments, but one will always be unused, so we suppress that check.
from __future__ import annotations

import typing as t

from aiida.common.exceptions import InvalidOperation
from aiida.engine.utils import prepare_inputs

try:
    import aiida_workgraph  # type: ignore[import-not-found,import-untyped]  # noqa: F401

    WORKGRAPH_AVAILABLE = True
except ImportError:
    WORKGRAPH_AVAILABLE = False

_KEY_METADATA = 'metadata'

_WORKGRAPH_RUN_RESERVED_KEYS = {_KEY_METADATA}
_WORKGRAPH_SUBMIT_RESERVED_KEYS = {_KEY_METADATA}


def is_workgraph_instance(obj: t.Any) -> bool:
    """Check if an object is a WorkGraph instance.

    Returns False if aiida-workgraph is not installed.

    :param obj: The object to check.
    :return: True if obj is a WorkGraph instance, False otherwise.
    """
    if not WORKGRAPH_AVAILABLE:
        return False
    from aiida_workgraph import WorkGraph  # type: ignore[import-not-found,import-untyped]

    return isinstance(obj, WorkGraph)


def prepare_workgraph_inputs(
    workgraph: t.Any,
    inputs: dict[str, t.Any] | None,
    kwargs: dict[str, t.Any],
    reserved_keys: set[str],
) -> tuple[dict[str, t.Any], dict[str, t.Any]]:
    """Merge and validate inputs for a WorkGraph launch, popping reserved keys.

    Reserved keys (e.g. ``metadata``) are separated from task inputs so they can
    be forwarded to ``WorkGraph.prepare_for_launch`` independently.

    :param workgraph: the WorkGraph instance
    :param inputs: the input dictionary
    :param kwargs: additional keyword arguments to be merged with inputs
    :param reserved_keys: set of keys to pop from inputs and return separately
    :raises ValueError: if both ``inputs`` and ``kwargs`` are specified
    :raises InvalidOperation: if reserved keys collide with task names
    :return: tuple of (task inputs, popped reserved key values)
    """
    merged = prepare_inputs(inputs, **kwargs).copy()  # copy: reserved keys are popped below
    popped: dict[str, t.Any] = {}
    for key in reserved_keys:
        value = merged.pop(key, None)
        if value is not None:
            popped[key] = value

    collisions = set(popped) & set(workgraph.get_task_names())
    if collisions:
        msg = (
            f'Keys {collisions} are reserved execution parameters but also match task names '
            f'on this WorkGraph. Rename the tasks to avoid colliding with reserved keys: {reserved_keys}.'
        )
        raise InvalidOperation(msg)

    return merged, popped
