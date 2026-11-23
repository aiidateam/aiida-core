###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# in the top-level directory of this distribution.                        #
###########################################################################
"""Transfer checkpoint-only child outputs using files owned by the root graph."""

import typing as t

from aiida.common.exceptions import GraphRuntimeError
from aiida.engine._checkpoint_pickle import dumps, loads_unsafe
from aiida.engine.processes.persistence import CheckpointPayload
from aiida.orm import CalcFunctionNode, GraphNode, ProcessNode
from aiida.orm.implementation.checkpoint_store import CheckpointBytes

_OUTPUT_DIGEST = CalcFunctionNode.CHECKPOINT_OUTPUT_DIGEST


def _is_active(owner: GraphNode) -> bool:
    return not owner.is_terminated


def publish_outputs(node: ProcessNode, outputs: dict[str, t.Any]) -> None:
    """Save the result before the child announces completion."""
    owner = node.caller
    if not isinstance(owner, GraphNode) or not _is_active(owner):
        msg = 'cannot publish checkpoint-only results without an active calling graph'
        raise GraphRuntimeError(msg)
    store = owner.backend.checkpoint_store
    payload = CheckpointBytes(dumps(CheckpointPayload(outputs)))
    store.write(node_uuid=owner.uuid, data=payload)
    try:
        node.base.attributes.set(_OUTPUT_DIGEST, payload.digest)
        if not _is_active(owner):
            msg = 'calling graph terminated before checkpoint-only results were published'
            raise GraphRuntimeError(msg)
    finally:
        if not _is_active(owner):
            store.discard_one(node_uuid=owner.uuid, digest=payload.digest)


def read_outputs(node: ProcessNode) -> dict[str, t.Any]:
    """Restore a finished child's result without opening its process checkpoint."""
    digest = node.base.attributes.get(_OUTPUT_DIGEST, None)
    owner = node.caller
    if digest is None or not isinstance(owner, GraphNode):
        msg = f'checkpoint-only results for task {node.pk} were not published'
        raise GraphRuntimeError(msg)
    store = owner.backend.checkpoint_store
    try:
        with store.retain_files():
            return dict(loads_unsafe(store.read(node_uuid=owner.uuid, digest=digest)))
    except (OSError, ValueError) as exc:
        msg = f'cannot read checkpoint-only results for task {node.pk}: {exc}'
        raise GraphRuntimeError(msg) from exc
