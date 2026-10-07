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

Relational layout (see ``aiida.storage.psql_dos.models.node``):

- ``db_dbnode.owner_id``: indexed, nullable foreign key to ``db_dbnode.id``.
  Null means a standalone node; non-null means an exclusively owned node.
  No separate ownership-mode flag exists.
- ``db_dbmembership``: dedicated membership table. Each row references its
  immediate owner (``owner_id``) and child (``child_id``) through foreign
  keys and persists ``position`` (integer, both lists and dicts) and, for
  dictionary entries, a nullable string ``key``. Database row order is not
  meaningful; ORM iteration follows persisted positions after reloading.
- ``db_dbnode.container_element_type``: nullable stored ``node_type``
  identifier of the container's element type. NULL means unset (a container
  that never held an element, which may still be stored). Once established
  by the first element it remains locked, including after removing every
  element.

Conventions and tolerances:

- Quantities: node primary keys (integers), ``node_type`` identifiers
  (exact strings, e.g. ``data.core.float.Float.``), positions (integers
  ``>= 0``), dictionary keys (strings or NULL). No floating-point
  quantities are involved, so there are no dtype tolerances; comparisons
  are exact string/integer equality.
- Homogeneity compares stored ``node_type`` identifier strings exactly,
  without loading element plugins. For nested containers only the outer
  container ``node_type`` is compared, never inner element-type metadata.
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

from aiida.common.exceptions import IntegrityError

__all__ = (
    'CONTAINER_NODE_TYPES',
    'OWNERSHIP_INTEGRATION_NOTES',
    'assert_no_provenance_link_to_owned',
    'attach_membership',
    'default_bulk_node_rows',
    'expand_ownership_closure',
    'is_container_node_type',
    'is_data_node_type',
    'resolve_element_type',
    'validate_bulk_node_insert',
    'validate_bulk_node_update',
    'validate_deletion_set',
    'validate_link_rows',
    'validate_membership_spec',
    'validate_ownership_graph',
)

#: Exact ``node_type`` identifiers eligible to own nodes. Only the new
#: container types may own nodes; the shared container base (if any) stays
#: internal. These must equal ``DataList.class_node_type`` /
#: ``DataDict.class_node_type`` (entry-point preserving underscore, e.g.
#: ``data.core.data_list.DataList.``); comparison is always exact string
#: equality, never plugin loading (storage must not import the ORM).
CONTAINER_NODE_TYPES: frozenset[str] = frozenset(
    {
        'data.core.data_list.DataList.',
        'data.core.data_dict.DataDict.',
    }
)

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
    """Return whether a ``node_type`` string is eligible as an owned child.

    Any data subclass is eligible, including nested containers (which are
    themselves data nodes). Process nodes and other non-data nodes are
    rejected. The check is a string-prefix test so no plugin is loaded.

    :param node_type: the stored ``node_type`` identifier.
    """
    return isinstance(node_type, str) and node_type.startswith('data.')


def is_container_node_type(node_type: str | None) -> bool:
    """Return whether a ``node_type`` string is eligible to own nodes.

    Only the reserved container identifiers in :data:`CONTAINER_NODE_TYPES`
    qualify. Comparison is exact, without loading plugins.

    :param node_type: the stored ``node_type`` identifier.
    """
    return node_type in CONTAINER_NODE_TYPES


def resolve_element_type(stored: str | None, child_node_type: str) -> str:
    """Resolve a container's element type against a candidate child.

    - ``stored is None`` (unset, never held an element): the child's exact
      ``node_type`` becomes the locked type and is returned.
    - Otherwise the child must match exactly; nested containers compare
      only their outer ``node_type``, never inner metadata.

    :param stored: the container's persisted ``container_element_type``
        (NULL/None means unset, not the Python type ``NoneType``).
    :param child_node_type: the candidate child's ``node_type`` identifier.
    :raises IntegrityError: if the child type does not match the locked type.
    """
    if stored is None:
        return child_node_type
    if stored != child_node_type:
        msg = f'Homogeneity violation: container element type is {stored!r} but child node type is {child_node_type!r}.'
        raise IntegrityError(msg)
    return stored


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

    Checks eligibility (owner must be a container, child must be data),
    position (integer ``>= 0``), and key (string or NULL; no coercion of
    non-string keys). Homogeneity against the container's locked type is
    checked by :func:`resolve_element_type`, and cross-row agreement by
    :func:`validate_ownership_graph`.

    :raises IntegrityError: on any violation.
    """
    if not is_container_node_type(owner_node_type):
        msg = f'Ineligible owner node type: {owner_node_type!r}. Only containers may own nodes.'
        raise IntegrityError(msg)
    if not is_data_node_type(child_node_type):
        msg = f'Ineligible child node type: {child_node_type!r}. Only data nodes may be owned.'
        raise IntegrityError(msg)
    if not isinstance(position, int) or isinstance(position, bool) or position < 0:
        msg = f'Invalid membership position: {position!r}. Position must be an integer >= 0.'
        raise IntegrityError(msg)
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
    owner_element_type: t.Any,
    members: list[dict],
    assert_element_type: t.Any = None,
) -> str | None:
    """Validate a complete ownership insertion for one container.

    ``members`` is a list of ``{'child_id': int, 'child_node_type': str,
    'position': int, 'key': str | None}`` describing every membership row
    to create together with the owner's reference updates. All rows are
    validated transactionally against live database state before anything
    is written by the caller:

    - one membership row per owned child, agreeing with the child's
      ``owner_id`` reference (children must currently be standalone);
    - owners eligible (container), children eligible (data-only);
    - homogeneity: every child matches the resolved element type; the
      resolved type is returned so the caller can persist it atomically
      with the rows. ``assert_element_type`` carries a pre-locked type
      established before storage (a container that held an element and was
      then emptied keeps its lock): it must agree with the stored lock and
      every child, and is persisted even when ``members`` is empty.
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
    :returns: the resolved (possibly newly locked) element type.
    :raises IntegrityError: on any invariant violation.

    ``owner_element_type`` is typed as ``Any`` because it is read back from stored rows: besides the
    valid ``node_type`` string or NULL it defensively rejects any other stored value. ``assert_element_type``
    is ``Any`` for the same reason: besides the valid string-or-NULL it defensively rejects mistyped input.
    """
    if not is_container_node_type(owner_node_type):
        msg = f'Ineligible owner node type: {owner_node_type!r}. Only containers may own nodes.'
        raise IntegrityError(msg)
    if owner_element_type is not None and not isinstance(owner_element_type, str):
        msg = f'Invalid container element type: {owner_element_type!r}. Must be a node_type string or NULL.'
        raise IntegrityError(msg)
    if assert_element_type is not None and not isinstance(assert_element_type, str):
        msg = f'Invalid asserted element type: {assert_element_type!r}. Must be a node_type string or NULL.'
        raise IntegrityError(msg)
    if assert_element_type is not None and owner_element_type is not None and assert_element_type != owner_element_type:
        msg = (
            f'Element-type lock disagreement: stored lock is {owner_element_type!r} but asserted '
            f'type is {assert_element_type!r}. Stored locks cannot be changed in place.'
        )
        raise IntegrityError(msg)

    seen_positions: set[int] = set()
    seen_keys: set[str] = set()
    child_ids: list[int] = []
    resolved = assert_element_type if assert_element_type is not None else owner_element_type
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
        if position in seen_positions:
            msg = f'Duplicate membership position {position} for owner {owner_id}.'
            raise IntegrityError(msg)
        seen_positions.add(position)
        if key is not None:
            if key in seen_keys:
                msg = f'Duplicate membership key {key!r} for owner {owner_id}.'
                raise IntegrityError(msg)
            seen_keys.add(key)
        child_ids.append(child_id)
        assert child_node_type is not None
        resolved = resolve_element_type(resolved, child_node_type)

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

    return resolved


def expand_ownership_closure(session, node_model, membership_model, pks: t.Iterable[int]) -> set[int]:
    """Expand node pks to their complete ownership unit.

    Follows ``owner_id`` upward to the ownership root, then collects the
    full owned subtree downward through membership rows. Deleting,
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
        child_rows = session.query(membership_model).filter(membership_model.owner_id == current).all()
        for edge in child_rows:
            if edge.child_id not in expanded:
                expanded.add(edge.child_id)
                frontier.append(edge.child_id)
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
    # Every membership edge internal to the set must have both endpoints
    # present; edges crossing the boundary would orphan agreement.
    edges = session.query(membership_model).filter(membership_model.owner_id.in_(sorted(targets))).all()
    for edge in edges:
        if edge.child_id not in targets:
            msg = (
                f'Deletion set cuts membership edge owner {edge.owner_id} -> child {edge.child_id}. '
                'Include the complete owned subtree.'
            )
            raise IntegrityError(msg)


def default_bulk_node_rows(rows: list[dict]) -> None:
    """Default ownership columns of bulk node rows to standalone.

    Rows predating the ownership schema (old archives, existing callers) carry no ownership keys;
    existing standalone nodes remain standalone through migration. Mutates rows in place, before the
    backend's strict key check.
    """
    for row in rows:
        row.setdefault('owner_id', None)
        row.setdefault('container_element_type', None)


def validate_bulk_node_insert(rows: list[dict]) -> None:
    """Reject bulk node rows that would violate stored ownership invariants.

    Owned children and locked element types can only be written atomically with their membership rows
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
        if row.get('container_element_type') is not None:
            msg = (
                'Cannot bulk-insert a locked element type: container element-type metadata must be '
                'written atomically with membership rows via `create_container_membership`.'
            )
            raise IntegrityError(msg)


def validate_bulk_node_update(rows: list[dict]) -> None:
    """Reject bulk node updates touching stored ownership.

    Stored ownership and membership cannot be changed in place (no triggers; the backend contract is
    the enforcement boundary).

    :raises IntegrityError: on any violation.
    """
    for row in rows:
        if 'owner_id' in row or 'container_element_type' in row:
            msg = 'Cannot update stored ownership: `owner_id` and `container_element_type` are immutable once stored.'
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
    backend, owner_id: int, members: list[dict], assert_element_type: str | None = None
) -> str | None:
    """Atomically persist ownership edges for one container on any SQL backend.

    Validates the complete ownership graph transactionally (eligibility, homogeneity, exclusivity,
    acyclicity, owner/membership agreement) and then, in a single transaction (joining an enclosing
    transaction when present), sets the children's ``owner_id`` references, locks the owner's
    ``container_element_type``, and inserts the membership rows. No provenance links are created or
    consulted: membership rows are containment edges, not provenance.

    The backend must provide ``get_session()``, ``transaction()``, ``in_transaction``, and
    ``_ownership_models()`` returning ``(DbNode, DbMembership)`` model classes.

    :param backend: the storage backend (``psql_dos``, ``sqlite_dos``, or ``sqlite_temp``).
    :param owner_id: pk of the stored owner container.
    :param members: list of ``{'child_id': int, 'child_node_type': str, 'position': int,
        'key': str | None}``.
    :param assert_element_type: pre-locked element type established before storage (kept across
        emptying); must agree with the stored lock and every child, persisted even for empty members.
    :returns: the resolved (possibly newly locked) element type.
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
        resolved = validate_ownership_graph(
            session,
            node_model,
            membership_model,
            owner_id=owner_id,
            owner_node_type=owner.node_type,
            owner_element_type=owner.container_element_type,
            members=members,
            assert_element_type=assert_element_type,
        )
        owner.container_element_type = resolved
        for spec in members:
            child = session.query(node_model).filter(node_model.id == spec['child_id']).one()
            child.owner_id = owner_id
            session.add(
                membership_model(
                    owner_id=owner_id,
                    child_id=spec['child_id'],
                    position=spec['position'],
                    key=spec.get('key'),
                )
            )
        session.flush()
    return resolved


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
