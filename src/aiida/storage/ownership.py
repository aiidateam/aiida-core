###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend-contract ownership validation for owned data containers.

This module enforces the relational storage invariants of
``orm-container-spec.md`` sections 2 and 3 at the storage-backend level,
not in the ORM. Both SQL backends (``psql_dos`` and ``sqlite_dos``) share
these helpers; the SQLite models are converted copies of the PostgreSQL
models, so the same table/column layout applies to both.

Relational layout:

- ``db_dbnode.owner_id``: indexed, nullable foreign key to ``db_dbnode.id``.
  Null means a standalone node; non-null means an exclusively owned node.
  No separate ownership-mode flag exists.
- ``db_dbmembership``: dedicated membership table. Each row references its
  immediate owner container (``owner_id`` FK to ``db_dbnode.id``) and
  child (``child_id`` FK to ``db_dbnode.id``) and persists ``position``
  (persisted iteration ordinal for both kinds — semantic order for lists,
  explicit insertion order for dicts) and, for keyed kinds only, a string
  ``key`` (NULL for lists, NOT NULL for dicts). Database row order is not
  meaningful; ORM iteration follows persisted positions after reloading.

There are no container marker tables. The membership kind (``'list'`` /
``'dict'``) is authoritative via :func:`container_kind_for` applied to
the owner's stored ``node_type``; an explicit ``kind`` argument, when
given, must agree with it (wrong-kind access fails atomically instead of
returning an ambiguously-interpreted row).

Conventions and tolerances:

- Quantities: node primary keys (integers), ``node_type`` identifiers
  (exact strings, e.g. ``data.core.float.Float.``), positions (integers
  ``>= 0``), dictionary keys (strings or NULL). No floating-point
  quantities are involved, so there are no dtype tolerances; comparisons
  are exact string/integer equality.
- Members may have different types; each type lives on its child node row.
- Membership rows are containment edges, not computational provenance.
  They are never duplicated as provenance links and CREATE/RETURN/INPUT
  links are never repurposed for containment.
- Structural safeguards (foreign keys, uniqueness) are complemented by
  transactional Python validation here. Database triggers are not used.
  Transactions alone do not provide complete concurrency safety; the
  uniqueness constraints make concurrent double-ownership attempts fail,
  while cycle/acyclicity checks are best-effort under concurrent writes
  and must be re-validated by the caller where strict serialisation
  matters (e.g. advisory locking around subtree stores).
- SQLite note: foreign-key enforcement depends on the connection ``PRAGMA
  foreign_keys`` setting, so the Python validation in this module is the
  authoritative enforcement boundary on both backends, not the database
  engine alone.

What this module does NOT do (deferred to later iterations):

- Full ORM API, QueryBuilder support, deletion approval UX, group/archive
  integration, and caching hashes. Callers performing deletion, group
  updates, or archive import must use :func:`expand_ownership_closure` and
  :func:`validate_deletion_set` so later integrations preserve these
  invariants.
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from aiida.common.exceptions import IntegrityError

__all__ = (
    'CONTAINER_KINDS',
    'CONTAINER_NODE_TYPES',
    'DICT_NODE_TYPE',
    'LIST_NODE_TYPE',
    'OWNERSHIP_INTEGRATION_NOTES',
    'OwnedContainerSpec',
    'OwnedMemberSpec',
    'assert_no_provenance_link_to_owned',
    'attach_dict_membership',
    'attach_list_membership',
    'attach_membership',
    'container_kind_for',
    'default_bulk_node_rows',
    'expand_ownership_closure',
    'is_container_node_type',
    'is_data_node_type',
    'is_ownable_node_type',
    'store_container_subtree',
    'validate_bulk_node_insert',
    'validate_bulk_node_update',
    'validate_deletion_set',
    'validate_link_rows',
    'validate_membership_spec',
    'validate_ownership_graph',
)

#: Exact ``node_type`` identifiers eligible to own nodes. This is the single source of truth for the
#: supported container set, which is finite and closed: only ``DataList`` and ``DataDict`` (no
#: third-party containers). The shared container base stays internal and owns nothing. These must equal
#: ``DataList.class_node_type`` / ``DataDict.class_node_type`` (entry-point preserving underscore, e.g.
#: ``data.core.data_list.DataList.``); comparison is always exact string equality, never plugin
#: loading (storage must not import the ORM). Backend dispatch, class loading and QueryBuilder all
#: consult this mapping instead of duplicating the identifiers.
CONTAINER_NODE_TYPES: frozenset[str] = frozenset(
    {
        'data.core.data_list.DataList.',
        'data.core.data_dict.DataDict.',
    }
)

#: Exact ``node_type`` of the ordered container.
LIST_NODE_TYPE: str = 'data.core.data_list.DataList.'
#: Exact ``node_type`` of the keyed container.
DICT_NODE_TYPE: str = 'data.core.data_dict.DataDict.'
#: Mapping of container ``node_type`` to its membership kind (``'list'``/``'dict'``).
CONTAINER_KINDS: dict[str, str] = {LIST_NODE_TYPE: 'list', DICT_NODE_TYPE: 'dict'}

#: Membership kind: ``'list'`` (ordered, ``key IS NULL``) or ``'dict'`` (keyed, ``key IS NOT NULL``).
ContainerKind = t.Literal['list', 'dict']

#: Integration work that must preserve these invariants but is deferred
#: past the storage-first iteration. Recorded here so backend callers do
#: not silently bypass ownership enforcement.
OWNERSHIP_INTEGRATION_NOTES: str = (
    'Deletion approval UX, group-membership expansion, archive import closure, '
    'process-boundary copying, and QueryBuilder joins are deferred integrations. '
    'Each exposed affected operation must preserve the invariants enforced here '
    'or explicitly reject container/owned-child operations until integrated.'
)


def is_data_node_type(node_type: str | None) -> bool:
    """Return whether a ``node_type`` string is leaf data (owned-child eligible, not a container).

    Containers share the ``data.`` type-string prefix (common node identity)
    but are decoupled from ``Data`` semantics: they are identified by
    :data:`CONTAINER_NODE_TYPES` and excluded here. Use
    :func:`is_ownable_node_type` for owned-child eligibility (leaf data or
    nested containers). The check is a string test so no plugin is loaded.

    :param node_type: the stored ``node_type`` identifier.
    """
    return isinstance(node_type, str) and node_type.startswith('data.') and node_type not in CONTAINER_NODE_TYPES


def is_ownable_node_type(node_type: str | None) -> bool:
    """Return whether a ``node_type`` string is eligible as an owned child.

    Any leaf data subclass is eligible, plus nested containers (which share
    node identity but not ``Data`` semantics). Process nodes and other
    non-data nodes are rejected. String test only, no plugin loading.

    :param node_type: the stored ``node_type`` identifier.
    """
    return is_data_node_type(node_type) or is_container_node_type(node_type)


def is_container_node_type(node_type: str | None) -> bool:
    """Return whether a ``node_type`` string is eligible to own nodes.

    Only the reserved container identifiers in :data:`CONTAINER_NODE_TYPES`
    qualify. Comparison is exact, without loading plugins.

    :param node_type: the stored ``node_type`` identifier.
    """
    return node_type in CONTAINER_NODE_TYPES


def container_kind_for(owner_node_type: str | None) -> ContainerKind | None:
    """Return the membership kind (``'list'``/``'dict'``) for a container ``node_type``.

    Returns ``None`` for non-container types. Comparison is exact string
    equality, never plugin loading. This is the single authoritative source
    of the container kind: callers pass the owner's stored ``node_type``
    here instead of consulting marker tables (there are none).
    """
    if owner_node_type is None:
        return None
    kind = CONTAINER_KINDS.get(owner_node_type)
    return t.cast('ContainerKind | None', kind)


def validate_membership_spec(
    *,
    owner_node_type: str | None,
    child_node_type: str | None,
    position: t.Any,
    key: t.Any,
) -> None:
    """Validate a single membership row's field-level invariants.

    ``position`` and ``key`` are typed as ``Any`` because this is a validation boundary: callers may
    pass arbitrary values (e.g. from archive rows) and violations are reported as ``IntegrityError``.

    Checks owner and child eligibility, position and key. Cross-row agreement is checked by
    :func:`validate_ownership_graph`.

    :raises IntegrityError: on any violation.
    """
    if not is_container_node_type(owner_node_type):
        msg = f'Ineligible owner node type: {owner_node_type!r}. Only containers may own nodes.'
        raise IntegrityError(msg)
    if not is_ownable_node_type(child_node_type):
        msg = f'Ineligible child node type: {child_node_type!r}. Only data nodes and containers may be owned.'
        raise IntegrityError(msg)
    if not isinstance(position, int) or isinstance(position, bool) or position < 0:
        msg = f'Invalid membership position: {position!r}. Position must be an integer >= 0.'
        raise IntegrityError(msg)
    # SQLite can coerce non-string values to text. Reject them before that loses the original key type.
    if key is not None and not isinstance(key, str):
        msg = f'Invalid membership key: {key!r}. Dictionary keys must be strings, never coerced.'
        raise IntegrityError(msg)


def _node_rows_by_id(session, node_model, ids: set[int]) -> dict[int, t.Any]:
    """Return ``{id: row}`` for stored node rows (``id``, ``node_type``, ``owner_id``)."""
    if not ids:
        return {}
    rows = session.query(node_model).filter(node_model.id.in_(sorted(ids))).all()
    return {row.id: row for row in rows}


def validate_ownership_graph(
    session,
    node_model,
    membership_model,
    *,
    owner_id: int,
    owner_node_type: str | None,
    members: list[dict],
    kind: ContainerKind | None = None,
) -> None:
    """Validate a complete ownership insertion for one container.

    ``members`` is a list of ``{'child_id': int, 'child_node_type': str,
    'position': int, 'key': str | None}`` describing every membership row.
    An optional ``reference=True`` leaves the standalone child's ``owner_id`` unset. All rows are
    validated transactionally against live database state before anything
    is written by the caller:

    - one membership row per owned child, agreeing with the child's
      ``owner_id`` reference (children must currently be standalone);
    - owners eligible (container), children eligible (data or containers);
    - list-vs-dict key discipline: ``key IS NULL`` for every list member,
      ``key IS NOT NULL`` for every dict member (``kind`` defaults to the
      owner's ``node_type`` via :func:`container_kind_for` when omitted; an
      explicit ``kind`` that disagrees with the owner type is rejected);
    - exclusive ownership: a child already owned by anyone is rejected;
    - acyclicity: self-ownership and cycles through already-stored
      membership edges are rejected (transitive closure walk);
    - no duplicate positions, no duplicate non-null keys within the insert;
    - positions/keys do not collide with already-stored rows of the owner
      (stored membership is immutable, so any overlap is an error);
    - stored ownership/membership immutability: this function only
      validates inserts for currently standalone children; repurposing it
      for already-owned children raises.

    Provenance links are never consulted or created here: membership rows
    are containment edges, not provenance.

    :param session: the active SQLAlchemy session (caller owns commit).
    :param node_model: the backend's ``DbNode`` model class.
    :param membership_model: the backend's ``DbMembership`` model class.
    :param kind: ``'list'``/``'dict'``; inferred from ``owner_node_type`` when omitted.
    :raises IntegrityError: on any invariant violation.
    """
    if not is_container_node_type(owner_node_type):
        msg = f'Ineligible owner node type: {owner_node_type!r}. Only containers may own nodes.'
        raise IntegrityError(msg)
    resolved_kind = kind if kind is not None else container_kind_for(owner_node_type)
    if resolved_kind not in ('list', 'dict'):
        msg = f'Unknown container kind for owner node type {owner_node_type!r} (kind={kind!r}).'
        raise IntegrityError(msg)
    if (
        kind is not None
        and container_kind_for(owner_node_type) is not None
        and kind != container_kind_for(owner_node_type)
    ):
        msg = (
            f'Container-kind mismatch: owner node type {owner_node_type!r} is a '
            f'{container_kind_for(owner_node_type)} container but accessed as {kind}.'
        )
        raise IntegrityError(msg)

    seen_positions: set[int] = set()
    seen_keys: set[str] = set()
    child_ids: list[int] = []
    for spec in members:
        try:
            child_id = spec['child_id']
            child_node_type = spec['child_node_type']
            position = spec['position']
            key = spec.get('key')
        except KeyError as exc:
            msg = f'Membership spec missing field: {exc}.'
            raise IntegrityError(msg) from exc
        if child_id == owner_id:
            msg = f'Ownership cycle: node {owner_id} cannot own itself.'
            raise IntegrityError(msg)
        validate_membership_spec(
            owner_node_type=owner_node_type,
            child_node_type=child_node_type,
            position=position,
            key=key,
        )
        # List-vs-dict key discipline: list members carry key NULL (position is the
        # semantic order); dict members carry a NOT NULL string key (position is insertion order,
        # ORDER BY-only, never a lookup).
        if resolved_kind == 'list' and key is not None:
            msg = (
                f'Container-kind violation: list container {owner_id} member at position {position} '
                f'carries key {key!r}; list entries must have key NULL.'
            )
            raise IntegrityError(msg)
        if resolved_kind == 'dict' and key is None:
            msg = (
                f'Container-kind violation: dict container {owner_id} member at position {position} '
                'has no key; dict entries must have a NOT NULL string key.'
            )
            raise IntegrityError(msg)
        if position in seen_positions:
            msg = f'Duplicate membership position {position} for owner {owner_id}.'
            raise IntegrityError(msg)
        seen_positions.add(position)
        if key is not None:
            if key in seen_keys:
                msg = f'Duplicate membership key {key!r} for owner {owner_id}.'
                raise IntegrityError(msg)
            seen_keys.add(key)
        if spec.get('reference', False) and not is_data_node_type(child_node_type):
            msg = f'Reference target {child_id} must be a standalone data node, not a container.'
            raise IntegrityError(msg)
        child_ids.append(child_id)

    if len(set(child_ids)) != len(child_ids):
        msg = f'Exclusive ownership violation: duplicate child in membership insert for owner {owner_id}.'
        raise IntegrityError(msg)

    # Cross-check live database state: children must exist, be data nodes
    # matching the spec types, and currently be standalone (owner_id NULL)
    # with no pre-existing membership row.
    rows = _node_rows_by_id(session, node_model, set(child_ids) | {owner_id})
    if owner_id not in rows:
        msg = f'Owner node {owner_id} does not exist.'
        raise IntegrityError(msg)
    for spec in members:
        child_id = spec['child_id']
        row = rows.get(child_id)
        if row is None:
            msg = f'Child node {child_id} does not exist.'
            raise IntegrityError(msg)
        if getattr(row, 'node_type') != spec['child_node_type']:
            msg = (
                f'Child node {child_id} type {getattr(row, "node_type")!r} disagrees with '
                f'spec type {spec["child_node_type"]!r}.'
            )
            raise IntegrityError(msg)
        if getattr(row, 'owner_id') is not None:
            msg = (
                f'Exclusive ownership violation: child {child_id} is already owned '
                f'by node {getattr(row, "owner_id")}. Ownership cannot be transferred in place.'
            )
            raise IntegrityError(msg)
        existing = session.query(membership_model).filter(membership_model.child_id == child_id).one_or_none()
        if existing is not None:
            msg = (
                f'Agreement violation: child {child_id} already has a membership row '
                f'from owner {existing.owner_id}. One membership row per owned child.'
            )
            raise IntegrityError(msg)

    # Stored membership is immutable: reject overlap with existing rows.
    if members:
        clashes = session.query(membership_model).filter(membership_model.owner_id == owner_id).all()
        if clashes:
            msg = (
                f'Stored membership is immutable: owner {owner_id} already has '
                f'{len(clashes)} stored membership row(s); cannot add more in place.'
            )
            raise IntegrityError(msg)

    # Acyclicity: walk stored ownership edges upward from the owner; no
    # candidate child may be an ancestor of the owner.
    ancestors: set[int] = set()
    cursor: int | None = owner_id
    while cursor is not None:
        cursor_row = rows.get(cursor)
        if cursor_row is None:
            cursor_row = session.query(node_model).filter(node_model.id == cursor).one_or_none()
            if cursor_row is None:
                break
        parent = getattr(cursor_row, 'owner_id')
        if parent is None:
            break
        if parent in ancestors:
            msg = f'Ownership cycle detected above node {owner_id}.'
            raise IntegrityError(msg)
        ancestors.add(parent)
        if parent in child_ids:
            msg = f'Ownership cycle: child {parent} is an ancestor of owner {owner_id}.'
            raise IntegrityError(msg)
        rows[parent] = rows.get(parent) or cursor_row
        cursor = parent


def expand_ownership_closure(session, node_model, membership_model, pks: t.Iterable[int]) -> set[int]:
    """Expand node pks to their complete ownership unit.

    Follows ``owner_id`` upward to the ownership root, then collects the
    full owned subtree downward through the child nodes' ``owner_id`` values. Deleting,
    grouping, or exporting a container must operate on this whole unit.

    :param session: the active SQLAlchemy session.
    :returns: the expanded set of node ids (roots plus all descendants).
    """
    targets = set(pks)
    if not targets:
        return set()
    rows = _node_rows_by_id(session, node_model, set(targets))
    roots: set[int] = set()
    for pk in targets:
        cursor = pk
        seen: set[int] = set()
        while True:
            if cursor in seen:
                break
            seen.add(cursor)
            row = rows.get(cursor)
            if row is None:
                row = session.query(node_model).filter(node_model.id == cursor).one_or_none()
                if row is None:
                    break
                rows[cursor] = row
            parent = getattr(row, 'owner_id')
            if parent is None:
                break
            cursor = parent
        roots.add(cursor)

    expanded = set(roots)
    frontier = list(roots)
    while frontier:
        current = frontier.pop()
        children = session.query(membership_model.child_id).join(node_model, node_model.id == membership_model.child_id)
        for (child_id,) in children.filter(membership_model.owner_id == current, node_model.owner_id == current):
            if child_id not in expanded:
                expanded.add(child_id)
                frontier.append(child_id)
    return expanded


def validate_deletion_set(session, node_model, membership_model, pks: t.Iterable[int]) -> None:
    """Validate that a deletion set is ownership-closed.

    A deletion set must contain complete ownership units: targeting an
    owned child without its root, or a container without its full
    subtree, is rejected so the caller expands the set explicitly and
    revalidates instead of relying on database cascades alone. Owned
    children can never be deleted independently.

    :raises IntegrityError: if the set is not ownership-closed.
    """
    targets = set(pks)
    if not targets:
        return
    expanded = expand_ownership_closure(session, node_model, membership_model, targets)
    if not expanded.issubset(targets):
        missing = sorted(expanded - targets)
        msg = (
            'Deletion set is not ownership-closed: ownership expansion requires '
            f'nodes {missing}. Expand the request to the full ownership unit(s) '
            'and revalidate with explicit approval; database cascades alone are not sufficient.'
        )
        raise IntegrityError(msg)
    edge = (
        session.query(membership_model)
        .filter(membership_model.child_id.in_(targets), membership_model.owner_id.not_in(targets))
        .first()
    )
    if edge is not None:
        msg = f'Cannot delete node {edge.child_id}: container {edge.owner_id} still references it.'
        raise IntegrityError(msg)


def default_bulk_node_rows(rows: list[dict]) -> None:
    """Default ownership columns of bulk node rows to standalone.

    Rows predating the ownership schema (old archives, existing callers) carry no ownership keys;
    existing standalone nodes remain standalone through migration. Mutates rows in place, before the
    backend's strict key check. Membership edges are never bulk-inserted: they are written
    atomically with owner references via :func:`attach_membership`.
    """
    for row in rows:
        row.setdefault('owner_id', None)


def validate_bulk_node_insert(rows: list[dict]) -> None:
    """Reject bulk node rows that would violate stored ownership invariants.

    Owned children can only be written atomically with their membership rows
    via :func:`attach_membership`; standalone bulk insertion of an owned child would break
    owner/membership agreement.

    :raises IntegrityError: on any violation.
    """
    for row in rows:
        if row.get('owner_id') is not None:
            msg = (
                'Cannot bulk-insert an owned node: owner references must be created atomically '
                'with membership rows via `create_container_membership`.'
            )
            raise IntegrityError(msg)


def validate_bulk_node_update(rows: list[dict]) -> None:
    """Reject bulk node updates touching stored ownership.

    Stored ownership and membership cannot be changed in place (no triggers; the backend contract is
    the enforcement boundary).

    :raises IntegrityError: on any violation.
    """
    for row in rows:
        if 'owner_id' in row:
            msg = 'Cannot update stored ownership: `owner_id` is immutable once stored.'
            raise IntegrityError(msg)


def validate_link_rows(session, node_model, rows: list[dict]) -> None:
    """Reject low-level provenance link rows touching owned nodes.

    Direct provenance links to owned children are rejected; automatic copying belongs at the process
    input/calculation-output boundary (deferred integration).

    :raises IntegrityError: on any violation.
    """
    endpoints: set[int] = set()
    for row in rows:
        endpoints.add(row['input_id'])
        endpoints.add(row['output_id'])
    for endpoint_id in endpoints:
        assert_no_provenance_link_to_owned(session, node_model, endpoint_id=endpoint_id)


def attach_membership(
    backend,
    owner_id: int,
    members: list[dict],
    *,
    kind: ContainerKind | None = None,
) -> None:
    """Atomically persist ownership edges for one container on any SQL backend.

    Validates the complete ownership graph transactionally (eligibility, list-vs-dict key
    discipline, exclusivity, acyclicity, owner/membership agreement) and then, in a
    single transaction (joining an enclosing transaction when present), sets owned children's
    ``owner_id`` values and inserts the membership rows. The membership kind is
    authoritative via :func:`container_kind_for` on the owner's ``node_type``; an explicit
    ``kind`` that disagrees with it fails atomically. No provenance links are created or
    consulted: membership rows are containment edges, not provenance.

    The backend must provide ``get_session()``, ``transaction()``, ``in_transaction`` and
    ``_ownership_models()`` returning ``(DbNode, DbMembership)`` model classes.

    :param backend: the storage backend (``psql_dos``, ``sqlite_dos``, or ``sqlite_temp``).
    :param owner_id: pk of the stored owner container.
    :param members: list of ``{'child_id': int, 'child_node_type': str, 'position': int,
        'key': str | None}`` (``key`` NULL for lists, NOT NULL string for dicts).
    :param kind: ``'list'``/``'dict'``; inferred from the owner's ``node_type`` when omitted.
    :raises IntegrityError: on any ownership-invariant violation.
    """
    from contextlib import nullcontext

    node_model, membership_model = backend._ownership_models()
    session = backend.get_session()
    with nullcontext() if backend.in_transaction else backend.transaction():
        owner = session.query(node_model).filter(node_model.id == owner_id).one_or_none()
        if owner is None:
            msg = f'Owner node {owner_id} does not exist.'
            raise IntegrityError(msg)
        if not is_container_node_type(owner.node_type):
            msg = f'Ineligible owner node type: {owner.node_type!r}. Only containers may own nodes.'
            raise IntegrityError(msg)
        if kind is not None:
            resolved_kind = kind
        else:
            inferred = container_kind_for(owner.node_type)
            if inferred is None:
                msg = f'Unknown container kind for owner {owner_id} (node_type={owner.node_type!r}).'
                raise IntegrityError(msg)
            resolved_kind = inferred
        validate_ownership_graph(
            session,
            node_model,
            membership_model,
            owner_id=owner_id,
            owner_node_type=owner.node_type,
            members=members,
            kind=resolved_kind,
        )
        sqlite = session.get_bind().dialect.name == 'sqlite'
        for spec in members:
            key = spec.get('key')
            # SQLite ignores the VARCHAR length and accepts embedded NULs. PostgreSQL already rejects both.
            if sqlite and key is not None:
                if len(key) > 255:
                    msg = 'Membership keys cannot exceed 255 characters.'
                    raise IntegrityError(msg)
                if '\x00' in key:
                    msg = 'Membership keys cannot contain NUL characters.'
                    raise IntegrityError(msg)
            if not spec.get('reference', False):
                child = session.query(node_model).filter(node_model.id == spec['child_id']).one()
                child.owner_id = owner_id
            session.add(
                membership_model(
                    owner_id=owner_id,
                    child_id=spec['child_id'],
                    position=spec['position'],
                    key=key,
                )
            )
        session.flush()


def attach_list_membership(backend, owner_id: int, members: list[dict]) -> None:
    """Attach ordered members to a list container (every ``key`` must be NULL).

    Cross-kind access fails instead of returning an ambiguously-interpreted row. See
    :func:`attach_membership`.
    """
    attach_membership(backend, owner_id, members, kind='list')


def attach_dict_membership(backend, owner_id: int, members: list[dict]) -> None:
    """Attach keyed members to a dict container (every ``key`` must be a NOT NULL string).

    Cross-kind access fails instead of returning an ambiguously-interpreted row. See
    :func:`attach_membership`.
    """
    attach_membership(backend, owner_id, members, kind='dict')


@dataclass
class OwnedMemberSpec:
    """Narrow storage input describing one owned-child edge.

    References the child by backend entity (pk/``node_type`` are read after
    the node rows exist) so the storage layer never depends on ORM container
    objects or callbacks. ``position``/``key`` carry the persisted iteration
    order (``key`` is ``None`` for lists, a string for dicts).
    """

    entity: t.Any
    position: int
    key: str | None = None
    reference: bool = False


@dataclass
class OwnedContainerSpec:
    """Narrow storage input describing one container's membership edges.

    ``members`` must be in persisted position order; ``kind`` follows
    :func:`attach_membership` (inferred from the owner's ``node_type`` when omitted).
    There is no layout: membership rows are always row-per-element.
    """

    owner: t.Any
    members: list[OwnedMemberSpec] = field(default_factory=list)
    kind: ContainerKind | None = None


def store_container_subtree(
    backend,
    entities: t.Sequence[t.Any],
    containers: t.Sequence[OwnedContainerSpec],
    root_links: t.Sequence[t.Any] | None = None,
    *,
    clean: bool = True,
) -> None:
    """Persist a complete owned-container subtree atomically.

    Stores every node row (``entities`` in post-order, children before their
    owner, ownership root last) and then freezes every container edge in
    ``containers`` (nested containers first) inside a single backend
    transaction that joins an enclosing transaction when present. Only the
    ownership root receives ``root_links`` (opaque link triples in the format
    accepted by the backend entity store methods; forwarded without inspection).
    Repository content must already be prepared by the caller (repo-first).

    Leaf data rows go through :meth:`BackendNode.store
    <aiida.orm.implementation.nodes.BackendNode.store>`; container rows go
    through :meth:`BackendContainer.store_container
    <aiida.orm.implementation.containers.BackendContainer.store_container>`
    (never ``BackendNode.store``), and membership edges through
    :meth:`backend.create_container_membership
    <aiida.storage.psql_dos.backend.PsqlDosBackend.create_container_membership>`.
    Backend-contract validation runs at the storage level. On failure the
    transaction rolls back and nothing is written; in-memory entity state is
    left to the caller for recovery.

    :param backend: the storage backend (owns the transaction).
    :param entities: backend entities in post-order (root last), non-empty.
    :param containers: per-container membership specs, nested containers first.
    :param root_links: incoming links applied to the ownership root only.
    """
    if not entities:
        msg = 'Cannot store an empty container subtree: at least the ownership root is required.'
        raise IntegrityError(msg)
    root = entities[-1]
    with backend.transaction():
        for entity in entities:
            links = root_links if entity is root else None
            store_container = getattr(entity, 'store_container', None)
            if callable(store_container):
                store_container(links, clean=clean)
            else:
                entity.store(links, clean=clean)
        for spec in containers:
            members = [
                {
                    'child_id': member.entity.pk,
                    'child_node_type': member.entity.node_type,
                    'position': member.position,
                    'key': member.key,
                    'reference': member.reference,
                }
                for member in spec.members
            ]
            backend.create_container_membership(spec.owner.pk, members, kind=spec.kind)


def assert_no_provenance_link_to_owned(session, node_model, *, endpoint_id: int, role: str = 'endpoint') -> None:
    """Reject low-level provenance links touching an owned node.

    Direct provenance links to owned children are rejected; automatic
    copying belongs at the process input/calculation-output boundary
    (deferred integration). Either link endpoint being owned raises.

    :param session: the active SQLAlchemy session.
    :param endpoint_id: pk of the link endpoint to check.
    :param role: label used in the error message (``'source'``/``'target'``).
    :raises IntegrityError: if the endpoint node is owned.
    """
    row = session.query(node_model).filter(node_model.id == endpoint_id).one_or_none()
    if row is not None and getattr(row, 'owner_id') is not None:
        msg = (
            f'Rejected provenance link to owned {role} node {endpoint_id} '
            f'(owned by {getattr(row, "owner_id")}). Owned children cannot appear in provenance links.'
        )
        raise IntegrityError(msg)
