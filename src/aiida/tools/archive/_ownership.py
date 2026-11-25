###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Read and validate relational ownership at archive boundaries."""

from collections import defaultdict
from collections.abc import Iterable
from contextlib import nullcontext
from dataclasses import dataclass, field

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from aiida.common.exceptions import IntegrityError
from aiida.common.utils import batch_iter
from aiida.orm.implementation.storage_backend import StorageBackend
from aiida.storage.ownership import (
    CONTAINER_NODE_TYPES,
    ContainerKind,
    container_kind_for,
    is_data_node_type,
    validate_membership_spec,
)


@dataclass(frozen=True)
class Member:
    """One ordered membership edge, in the local node ID space."""

    child_id: int
    position: int
    key: str | None
    reference_type: str | None = None


@dataclass(frozen=True)
class ContainerState:
    """The kind and ordered members of a container, possibly empty.

    The kind is derived from the container's ``db_dbnode.node_type``; empty containers have no
    membership rows and are still recorded here.
    """

    kind: ContainerKind
    members: tuple[Member, ...]


@dataclass
class Ownership:
    """Ownership state of a closed selection, excluding standalone non-container nodes."""

    containers: dict[int, ContainerState] = field(default_factory=dict)
    parents: dict[int, int] = field(default_factory=dict)
    types: dict[int, str] = field(default_factory=dict)

    omitted_members: set[int] = field(default_factory=set)

    @property
    def changed_containers(self) -> set[int]:
        """Containers whose content hashes cannot be reused in the projected archive."""
        changed = self.omitted_members.copy()
        for container in self.omitted_members:
            owner = container
            while owner in self.parents:
                owner = self.parents[owner]
                if owner in changed:
                    break
                changed.add(owner)
        return changed


def read_ownership(
    backend: StorageBackend, ids: Iterable[int] | None = None, *, project_selection: bool = False
) -> Ownership:
    """Read and validate all ownership rows touching the selection.

    With ``project_selection``, keep only edges with both endpoints selected and track
    containers whose contents changed. Otherwise require every recorded edge to
    agree with the node rows.
    """
    if ids is not None:
        ids = set(ids)
        if not ids:
            return Ownership()

    get_models = getattr(backend, '_ownership_models', None)
    get_session = getattr(backend, 'get_session', None)
    if get_models is None or get_session is None:
        from aiida import orm

        filters = {} if ids is None else {'id': {'in': ids}}
        if orm.QueryBuilder(backend=backend).append(orm.Container, filters=filters).first():
            msg = 'Storage does not expose ownership records for its container nodes.'
            raise IntegrityError(msg)
        return Ownership()

    node, membership = get_models()

    try:
        with nullcontext() if backend.in_transaction else backend.transaction():
            session = get_session()

            def selected(query, condition):
                if ids is None:
                    return session.execute(query).all()
                # Keep bind counts bounded. An edge may touch two different
                # batches, so select its PK and deduplicate by the entire row.
                return {
                    row for _, batch in batch_iter(ids, 1000) for row in session.execute(query.where(condition(batch)))
                }

            nodes = selected(
                select(node.id, node.node_type, node.owner_id).where(
                    or_(node.owner_id.is_not(None), node.node_type.in_(CONTAINER_NODE_TYPES))
                ),
                node.id.in_,
            )
            edges = selected(
                select(
                    membership.id,
                    membership.owner_id,
                    membership.child_id,
                    membership.position,
                    membership.key,
                    node.node_type,
                    node.owner_id,
                ).outerjoin(node, node.id == membership.child_id),
                lambda batch: or_(
                    membership.owner_id.in_(batch), and_(node.owner_id.is_not(None), membership.child_id.in_(batch))
                ),
            )
    except SQLAlchemyError as exc:
        msg = 'Could not read archive ownership state.'
        raise IntegrityError(msg) from exc

    source_parents = {node_id: owner_id for node_id, _, owner_id in nodes if owner_id is not None}
    parents = {
        child: owner for child, owner in source_parents.items() if not project_selection or ids is None or owner in ids
    }
    state = Ownership(
        parents=parents,
        types={
            node_id: node_type
            for node_id, node_type, _ in nodes
            if node_id in parents or node_type in CONTAINER_NODE_TYPES
        },
    )
    kinds = {node_id: container_kind_for(node_type) for node_id, node_type in state.types.items()}

    members: dict[int, list[Member]] = defaultdict(list)
    seen_children: set[int] = set()
    for _, owner, child, position, key, child_type, parent in edges:
        if project_selection and ids is not None and owner not in ids and parent == owner and child in ids:
            seen_children.add(child)
            continue
        reference = parent is None
        if (
            kinds.get(owner) is None
            or child in seen_children
            or (not is_data_node_type(child_type) if reference else parent != owner)
        ):
            msg = f'Incomplete or inconsistent ownership edge {owner} -> {child}.'
            raise IntegrityError(msg)
        validate_membership_spec(
            owner_node_type=state.types[owner], child_node_type=child_type, position=position, key=key
        )
        seen_children.add(child)
        if ids is not None and child not in ids:
            if not project_selection:
                msg = f'Incomplete ownership edge {owner} -> {child}.'
                raise IntegrityError(msg)
            state.omitted_members.add(owner)
            continue
        members[owner].append(Member(child, position, key, child_type if reference else None))
    if source_parents.keys() - seen_children:
        msg = 'Owned nodes are missing membership rows.'
        raise IntegrityError(msg)

    for owner, kind in kinds.items():
        if kind is None:
            continue
        ordered = tuple(sorted(members.get(owner, []), key=lambda member: member.position))
        keys = {member.key for member in ordered}
        if (
            len({member.position for member in ordered}) != len(ordered)
            or (kind == 'list' and bool(keys - {None}))
            or (kind == 'dict' and (None in keys or len(keys) != len(ordered)))
        ):
            msg = f'Invalid positions or keys for {kind} container {owner}.'
            raise IntegrityError(msg)
        state.containers[owner] = ContainerState(kind, ordered)

    # Every owned node must lead to a root. Cache completed paths to keep this linear.
    checked: set[int] = set()
    for start in state.parents:
        path: set[int] = set()
        current = start
        while current in state.parents and current not in checked:
            if current in path:
                msg = f'Ownership cycle involving node {current}.'
                raise IntegrityError(msg)
            path.add(current)
            current = state.parents[current]
        checked.update(path)
    return state
