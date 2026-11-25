###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fan-out maps over owned containers with provenance-safe aggregation.

A ``@graph`` body calls :func:`par_map` with a unary task or graph and a
:class:`~aiida.orm.DataList` or :class:`~aiida.orm.DataDict` wire. The lowering
expands the call to a static map placement; the scheduler dispatches one child
per element and then a collector calculation that *creates* the result
container. Graphs only ever return that existing container, so they never
create result containers themselves.
"""

from __future__ import annotations

import typing as t
from collections.abc import Callable

from aiida.common.exceptions import GraphLanguageError
from aiida.engine.processes.functions import process_function
from aiida.engine.processes.graphs.tasks import TaskProcess
from aiida.orm import DataDict, DataList, Node, TaskNode
from aiida.orm.nodes.data.datanode import DataNode

__all__ = (
    '_collect_dict',
    '_collect_list',
    'par_map',
)

T = t.TypeVar('T')
R = t.TypeVar('R')
_InputNode = t.TypeVar('_InputNode', bound=Node)
_OutputNode = t.TypeVar('_OutputNode', bound=Node)


@t.overload
def par_map(func: Callable[[_InputNode], _OutputNode], values: DataList[_InputNode]) -> DataList[_OutputNode]: ...


@t.overload
def par_map(func: Callable[[T], R], values: DataList) -> DataList: ...


@t.overload
def par_map(func: Callable[[T], R], values: DataDict) -> DataDict: ...


def par_map(func: t.Any, values: t.Any) -> t.Any:
    """Map a unary task or graph over an owned container.

    This is an authoring operation, not a runtime function: call it inside a
    ``@graph`` body and the graph compiler expands it to a fan-out placement.
    Calling it anywhere else fails loudly.

    :param func: a unary ``@task`` or ``@graph`` with exactly one input and one output.
    :param values: a :class:`~aiida.orm.DataList` or :class:`~aiida.orm.DataDict` wire;
        lists iterate elements in order, mappings iterate values keeping keys.
    :return: a container of the same kind holding one child output per element.
    """
    msg = (
        '`par_map` declares a fan-out inside a `@graph` body and never runs directly; '
        'call it with a unary `@task` or `@graph` and a `DataList`/`DataDict` wire on one line, '
        'for example `mapped = par_map(increment, values)`.'
    )
    raise GraphLanguageError(msg)


# Use checkpointable task processes so daemon workers can submit these collectors.
@process_function(node_class=TaskNode, base_class=TaskProcess)
def _collect_list(**items: DataNode) -> DataList:
    """Create the result list from one child output per element, in order."""
    return DataList([items[f'item_{index}'] for index in range(len(items))])


@process_function(node_class=TaskNode, base_class=TaskProcess)
def _collect_dict(keys: list[str], **items: DataNode) -> DataDict:
    """Create the result mapping from one child output per value, keeping keys."""
    return DataDict(dict(zip(keys, [items[f'item_{index}'] for index in range(len(keys))], strict=True)))
