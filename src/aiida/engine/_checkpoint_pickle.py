###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# in the top-level directory of this distribution.                        #
###########################################################################
"""Pickle checkpoint state without serializing the ORM backend."""

import io
import pickle
import typing as t

import cloudpickle
from typing_extensions import override

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine.processes.persistence import CheckpointPayload
from aiida.orm.utils.managers import NodeLinksManager

_Entity: t.TypeAlias = orm.Node | orm.Group | orm.Computer
_EntityKind: t.TypeAlias = t.Literal['node', 'group', 'computer']
_Reference: t.TypeAlias = tuple[_EntityKind, str] | tuple[t.Literal['links'], str, str, bool]


class _Pickler(cloudpickle.CloudPickler):
    @override
    def persistent_id(self, obj: object) -> _Reference | None:
        entity: _Entity
        if isinstance(obj, NodeLinksManager):
            entity = obj._node
            if entity.is_stored:
                return 'links', entity.uuid, obj._link_type.value, bool(obj._incoming)
        elif isinstance(obj, (orm.Node, orm.Group, orm.Computer)):
            entity = obj
            if entity.is_stored:
                if isinstance(entity, orm.Node):
                    return 'node', entity.uuid
                if isinstance(entity, orm.Group):
                    return 'group', entity.uuid
                return 'computer', entity.uuid
        else:
            return None

        msg = f'{type(entity).__name__}<{entity.uuid}> is not stored and cannot be checkpointed'
        raise pickle.PicklingError(msg)


class _Unpickler(pickle.Unpickler):
    def __init__(self, stream: io.BytesIO) -> None:
        super().__init__(stream)
        self._entities: dict[tuple[str, str], _Entity] = {}

    def _load_entity(self, kind: _EntityKind, uuid: str) -> _Entity:
        key = kind, uuid
        if key not in self._entities:
            if kind == 'node':
                self._entities[key] = orm.load_node(uuid=uuid)
            elif kind == 'group':
                self._entities[key] = orm.load_group(uuid=uuid)
            else:
                self._entities[key] = orm.Computer.collection.get(uuid=uuid)
        return self._entities[key]

    @override
    def persistent_load(self, pid: object) -> _Entity | NodeLinksManager:
        match pid:
            case ('links', str(uuid), str(link_type), bool(incoming)):
                node: _Entity = self._load_entity('node', uuid)
                assert isinstance(node, orm.Node)
                try:
                    link = LinkType(link_type)
                except ValueError:
                    msg = f'Invalid checkpoint link type: {link_type!r}'
                    raise pickle.UnpicklingError(msg) from None
                return NodeLinksManager(node=node, link_type=link, incoming=incoming)
            case (('node' | 'group' | 'computer') as kind, str(uuid)):
                return self._load_entity(kind, uuid)
            case _:
                msg = f'Invalid checkpoint reference: {pid!r}'
                raise pickle.UnpicklingError(msg)


def dumps(payload: CheckpointPayload) -> bytes:
    """Serialize the checkpoint in one pass, preserving shared Python state."""
    with io.BytesIO() as stream:
        _Pickler(stream, protocol=5).dump(payload)
        return stream.getvalue()


def loads_unsafe(data: bytes) -> CheckpointPayload:
    """Deserialize a checkpoint from trusted profile storage only."""
    with io.BytesIO(data) as stream:
        payload = _Unpickler(stream).load()
    if not isinstance(payload, CheckpointPayload):
        msg = 'Expected a process checkpoint payload'
        raise pickle.UnpicklingError(msg)
    return payload
