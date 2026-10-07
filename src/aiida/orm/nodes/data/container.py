###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Owned data-node containers: :class:`DataList` and :class:`DataDict`.

Scaffolding iteration for the owned-container specification (``orm-container-spec.md`` §§1, 4, 5, 6):

* ``DataList`` (entry point ``core.data_list``) is an ordered container of data nodes.
* ``DataDict`` (entry point ``core.data_dict``) maps string keys to data nodes.

Contract summary:

* Contents: independent, exclusively owned copies of :class:`~aiida.orm.Data` instances. Any data subclass is
  eligible, including nested containers. Process nodes and other non-data nodes are rejected.
* Homogeneity: list elements (dictionary values) must share the exact concrete node type, compared as the stored
  ``node_type`` identifier without loading element plugins. The type is inferred from the first element and stays
  locked afterwards, including after removing every element. An empty container has unset (``None``) element type
  and may be stored.
* Copy-on-insert: insertion always clones the source; the source keeps its ownership and lifetime, repeated insertion
  creates distinct copies, and inserting a copy copies it again. Ownership is never transferred in place.
* Recursive copy: copying a container recursively copies its owned subtree. The copied root is standalone with new
  identities and no provenance links or source-tracking metadata. Metadata handling (attributes, repository content,
  extras, label, description, user/computer) follows :meth:`~aiida.orm.Data.clone`; mutable metadata is independent
  between copies.
* Pre-storage mutation: insertion, replacement, removal and reordering are allowed while unstored. A removed child is
  detached as a standalone, unstored, editable node (for nested containers only the root is detached); removal neither
  stores nor invalidates anything. Reinserting a detached node copies it again.
* Freeze-on-store: storing the ownership root validates the complete subtree, prepares repository content first
  (repo-first), then persists every node in one database transaction joining an enclosing transaction when present.
  Success freezes the whole subtree (immutable modulo extras); failure leaves no partial graph and the retained
  objects stay unstored, editable and retryable.
* Ordering/keys: positions are persisted explicitly; database row order is meaningless. ORM iteration follows
  persisted position order after reloading. Dictionary keys are strings only (rejected, never coerced) with Python
  insertion-order semantics: replacement preserves position, remove-plus-reinsert moves the key to the end.
* Python behavior: sequence/mapping scaffolding exposes length, indexing/key lookup and iteration. Slicing is not
  supported. Equality and hashing follow base :class:`~aiida.orm.Node` identity (UUID) behavior; independent copies
  are unequal even when their content matches.

Storage representation (relational, ``orm-container-spec.md`` §§2-3):

* Containment lives in the dedicated membership table (one row per owned
  child: immediate owner, child, integer ``position``, nullable string
  ``key``), not in node attributes or provenance links.
* Each owned child carries an indexed ``owner_id`` reference to its
  immediate owner (NULL means standalone); every membership row agrees
  with the child's reference and both are written atomically via
  ``backend.create_container_membership``.
* The locked element-type identifier lives in the dedicated relational
  container metadata (``container_element_type``, NULL when unset), never
  in node attributes. Comparisons use exact stored ``node_type`` strings
  without loading element plugins.
"""

from __future__ import annotations

import contextlib
import copy
import io
import typing as t
from collections.abc import Iterator, Mapping

from aiida.common import exceptions
from aiida.common.lang import override
from aiida.orm.nodes.caching import NodeCaching
from aiida.orm.nodes.data.data import Data

if t.TYPE_CHECKING:
    from typing_extensions import Self

    from aiida.orm.nodes.node import Node

__all__ = ('DataDict', 'DataList')


def is_container_node(node: t.Any) -> bool:
    """Return whether ``node`` is an owned-data container (``DataList``/``DataDict``)."""
    return isinstance(node, _ContainerBase)


@contextlib.contextmanager
def _joined_transaction(backend: t.Any) -> Iterator[None]:
    """Join the ambient backend transaction, opening one for reads if none is active.

    Read-only ownership lookups must not leave an autobegun session
    transaction behind: on SQLite it holds a SHARED lock that blocks later
    writes (e.g. storage reset in tests). Mirrors the ``QueryBuilder``
    pattern of wrapping reads in ``backend.transaction()``.
    """
    in_transaction = getattr(backend, 'in_transaction', False)
    begin = getattr(backend, 'transaction', None)
    if in_transaction or begin is None:
        yield
    else:
        with begin():
            yield


def stored_owner_id(node: Node) -> int | None:
    """Return the stored ``owner_id`` of ``node`` or ``None`` if standalone/unavailable.

    Unstored nodes are always standalone. Nodes on backends without the
    ownership schema report ``None`` (no ownership rows can exist there).
    """
    if not node.is_stored:
        return None
    get_models = getattr(node.backend, '_ownership_models', None)
    get_session = getattr(node.backend, 'get_session', None)
    if get_models is None or get_session is None:
        return None
    try:
        node_model, _ = get_models()
        with _joined_transaction(node.backend):
            row = get_session().query(node_model).filter(node_model.id == node.pk).one_or_none()
    except Exception:
        return None
    return getattr(row, 'owner_id', None) if row is not None else None


def is_owned(node: Node) -> bool:
    """Return whether ``node`` is an owned container child (in memory or stored).

    Checks both the in-memory single-owner flag (unstored subtrees, freshly
    materialized handles) and the stored ``owner_id`` reference (freshly
    loaded handles of owned children, which carry no in-memory flag).
    """
    if getattr(node, '_container_owner', None) is not None:
        return True
    return stored_owner_id(node) is not None


def ownership_root(node: Node) -> Node:
    """Return the outermost in-memory owner of ``node`` (itself if standalone)."""
    root = _owned_root(t.cast(Data, node))
    return root if root is not None else node


def stored_ownership_root_pk(backend: t.Any, pk: int) -> int:
    """Return the pk of the ownership root of the stored node ``pk`` (itself if standalone).

    Follows stored ``owner_id`` references upward. Backends without the
    ownership schema return ``pk`` unchanged.
    """
    get_models = getattr(backend, '_ownership_models', None)
    get_session = getattr(backend, 'get_session', None)
    if get_models is None or get_session is None:
        return pk
    node_model, _ = get_models()
    try:
        with _joined_transaction(backend):
            session = get_session()
            cursor = pk
            seen: set[int] = set()
            while cursor not in seen:
                seen.add(cursor)
                row = session.query(node_model).filter(node_model.id == cursor).one_or_none()
                if row is None:
                    break
                parent = getattr(row, 'owner_id', None)
                if parent is None:
                    break
                cursor = parent
            return cursor
    except Exception:
        return pk


def ensure_standalone(node: Data) -> Data:
    """Return ``node`` itself if standalone, else an independent standalone copy.

    Copying an owned child creates a standalone node with a new identity and
    no inherited ownership or provenance links (recursive for nested
    containers); the original stays in its container. Standalone nodes
    (including standalone containers, whose descendants remain owned by
    them) are returned unchanged.
    """
    if is_owned(node):
        return node.clone()
    return node


def detach_owned_inputs(value: t.Any) -> t.Any:
    """Recursively replace owned container children with standalone copies.

    Process-boundary helper (spec §7): when an owned child is supplied as a
    process input, the process must execute with an independent standalone
    copy (recursive for nested containers) and record that same copy as its
    provenance input. Standalone nodes — including standalone containers,
    whose descendants remain owned by them — pass through untouched, as do
    non-data values. Containers that are rebuilt only when a replacement
    occurred, so unaffected input structures keep their identity. See also
    :func:`detach_owned_inputs_and_copies`.
    """
    return detach_owned_inputs_and_copies(value)[0]


def detach_owned_inputs_and_copies(value: t.Any) -> tuple[t.Any, list[Data]]:
    """Replace owned children like :func:`detach_owned_inputs` and report the copies.

    :returns: ``(new_value, copies)`` where ``copies`` lists every
        standalone copy created during the replacement (in walk order).
    """
    copies: list[Data] = []

    def walk(entry: t.Any) -> t.Any:
        if isinstance(entry, Data):
            if is_owned(entry):
                candidate = entry.clone()
                copies.append(candidate)
                return candidate
            return entry
        if isinstance(entry, dict):
            replaced = False
            rebuilt: dict[t.Any, t.Any] = {}
            for key, item in entry.items():
                new_item = walk(item)
                replaced = replaced or new_item is not item
                rebuilt[key] = new_item
            return rebuilt if replaced else entry
        if isinstance(entry, list):
            rebuilt_list = [walk(item) for item in entry]
            if all(new is old for new, old in zip(rebuilt_list, entry, strict=True)):
                return entry
            return rebuilt_list
        if isinstance(entry, tuple):
            rebuilt_tuple = tuple(walk(item) for item in entry)
            if all(new is old for new, old in zip(rebuilt_tuple, entry, strict=True)):
                return entry
            return rebuilt_tuple
        return entry

    return walk(value), copies


def expand_ownership_unit(backend: t.Any, pks: t.Iterable[int]) -> set[int]:
    """Expand node pks to their complete ownership unit (roots plus all descendants).

    Follows stored ``owner_id`` references upward to the ownership root(s),
    then collects every owned descendant through membership rows. Backends
    without the ownership schema cannot hold containers and return the
    input unchanged.
    """
    targets = set(pks)
    get_models = getattr(backend, '_ownership_models', None)
    get_session = getattr(backend, 'get_session', None)
    if not targets or get_models is None or get_session is None:
        return set(targets)
    try:
        from aiida.storage import ownership as ownership_contract

        node_model, membership_model = get_models()
        with _joined_transaction(backend):
            expanded = ownership_contract.expand_ownership_closure(get_session(), node_model, membership_model, targets)
        return set(expanded)
    except Exception:
        return set(targets)


class ContainerCaching(NodeCaching):
    """Content-based recursive caching hash for owned data containers (spec §10).

    The hash incorporates child content recursively, excluding owner IDs and
    child UUIDs, so equivalent independent copies hash equally:

    * lists contribute the ordered sequence of child content hashes
      (element order matters; plain ``list`` hashing is order-sensitive);
    * dictionaries contribute the ``{key: child hash}`` mapping (insertion
      order ignored; ``make_hash`` sorts mappings by hashed key);
    * the persisted element-type identifier contributes, including its NULL
      (unset) state, so differently typed empty containers hash differently.

    Child hashes are content hashes (class, attributes, repository content,
    computer) that never embed UUIDs or owner references. Cache *reuse*
    remains disabled (``_cachable = False``): reusing a cached container
    would have to materialize an independent ownership subtree, which the
    generic ``_store_from_cache`` root-only clone cannot provide without
    introducing shared ownership. Disabling reuse is explicit safe rejection
    under the staging guard, not silent bypass: no container is ever served
    from, or stored into, the process cache.
    """

    @override
    def get_objects_to_hash(self) -> dict[str, t.Any]:
        """Return the content objects contributing to the container hash."""
        objects = super().get_objects_to_hash()
        node = self._node
        assert isinstance(node, _ContainerBase)
        node._ensure_materialized()
        objects['container_element_type'] = node._container_element_type
        objects['members'] = node._hashable_members()
        return objects


def _owned_root(node: Data) -> Data | None:
    """Return the outermost in-memory owner of ``node`` or ``None`` if standalone."""
    seen: set[int] = set()
    current = node
    while True:
        owner = getattr(current, '_container_owner', None)
        if owner is None:
            return None if current is node else current
        if id(owner) in seen:  # defensive: ownership must be acyclic
            msg = 'container ownership cycle detected'
            raise exceptions.InvalidOperation(msg)
        seen.add(id(owner))
        current = owner


class _ContainerBase(Data):
    """Internal base class for owned data-node containers.

    This class is intentionally internal: only :class:`DataList` and :class:`DataDict` are public. It implements
    copy-on-insert, single ownership, pre-storage mutation and atomic freeze-on-store on top of the existing backend
    interfaces. The persisted representation goes through the narrow internal ``_storage_*`` helpers so the storage
    backend can take them over with relational records later.
    """

    _cachable = False  # cache reuse explicitly disabled: generic `_store_from_cache` cannot provide
    # independent ownership subtrees (see `ContainerCaching`); content hashing itself is implemented.
    _CLS_NODE_CACHING = ContainerCaching

    def initialize(self) -> None:
        """Initialize the in-memory container state (unmaterialized, standalone, typeless)."""
        super().initialize()
        self._container_owner: _ContainerBase | None = None
        self._container_materialized = False
        self._container_element_type: str | None = None
        self._container_guard_armed = False
        self._container_recovery_snapshot: dict[str, dict[str, t.Any]] | None = None

    # -- in-memory membership primitives (implemented by subclasses) --

    def _owned_children(self) -> list[Data]:
        """Return the owned children in persisted position order."""
        raise NotImplementedError

    def _attach_owned(self, child: Data) -> None:
        """Record an already-copied child as owned by this container."""
        raise NotImplementedError

    def _materialize_child(self, key: str | None, child: Data) -> None:
        """Record a child reconstructed from persisted membership (``key`` is ``None`` for lists)."""
        self._attach_owned(child)

    def _detach_owned(self, child: Data) -> None:
        """Forget a child without touching its stored state (standalone, usable)."""
        raise NotImplementedError

    def _hashable_members(self) -> t.Any:
        """Return the child-content structure contributing to the caching hash.

        Lists return the ordered sequence of child content hashes;
        dictionaries return the ``{key: child hash}`` mapping. Child hashes
        exclude owner IDs and UUIDs; recursion through nested containers is
        content-based as well.
        """
        raise NotImplementedError

    def _iter_containers(self) -> Iterator[_ContainerBase]:
        """Yield this container and every nested owned container."""
        yield self
        for child in self._owned_children():
            if isinstance(child, _ContainerBase):
                yield from child._iter_containers()

    # -- loading / materialization --

    def _read_storage_records(self) -> tuple[str | None, list[tuple[int, str | None, int, str]]] | None:
        """Read persisted ``(element_type, membership)`` records for this stored container.

        Returns ``(element_type, edges)`` where ``edges`` is a list of
        ``(position, key, child_id, child_node_type)`` ordered by persisted
        position (record order itself is meaningless). Returns ``None`` on
        backends without the ownership schema, where no containers can exist.
        """
        get_models = getattr(self.backend, '_ownership_models', None)
        get_session = getattr(self.backend, 'get_session', None)
        if get_models is None or get_session is None:
            return None
        node_model, membership_model = get_models()
        with _joined_transaction(self.backend):
            session = get_session()
            owner_row = session.query(node_model).filter(node_model.id == self.pk).one_or_none()
            if owner_row is None:
                msg = f'container node with pk {self.pk} has no stored row'
                raise exceptions.NotExistent(msg)
            element_type = getattr(owner_row, 'container_element_type', None)
            edge_rows = (
                session.query(membership_model)
                .filter(membership_model.owner_id == self.pk)
                .order_by(membership_model.position)
                .all()
            )
            child_ids = [edge.child_id for edge in edge_rows]
            child_rows = session.query(node_model).filter(node_model.id.in_(child_ids)).all() if child_ids else []
        by_id = {row.id: row for row in child_rows}
        edges: list[tuple[int, str | None, int, str]] = []
        for edge in edge_rows:
            child_row = by_id.get(edge.child_id)
            if child_row is None:
                msg = f'membership edge of container {self.pk} references missing child {edge.child_id}'
                raise exceptions.IntegrityError(msg)
            edges.append((edge.position, edge.key, edge.child_id, child_row.node_type))
        return element_type, edges

    @staticmethod
    def _require_element_plugin(child_node_type: str) -> None:
        """Raise if the element plugin for ``child_node_type`` is missing.

        Typed element access requires the real plugin and reports its
        absence; a genuine base ``Data`` element (``data.Data.``) remains
        valid and is never mistaken for a missing-plugin fallback. Structural
        operations use storage records directly and never call this.
        """
        from aiida.orm.nodes.data.data import Data as BaseData

        if child_node_type == BaseData.class_node_type:
            return
        base_path, _, _ = child_node_type.rpartition('.')
        base_path = base_path.rpartition('.')[0]
        if not base_path.startswith('data.'):
            return
        from aiida.common.exceptions import MissingEntryPointError
        from aiida.plugins.entry_point import load_entry_point

        try:
            load_entry_point('aiida.data', base_path.removeprefix('data.'))
        except MissingEntryPointError as exc:
            msg = (
                f'cannot load container element of type `{child_node_type}`: '
                f'the corresponding data plugin is not available: {exc}'
            )
            raise MissingEntryPointError(msg) from exc

    def _load_stored_child(self, child_id: int, child_node_type: str) -> Data:
        """Load a stored owned child by pk on this container's backend (typed access)."""
        self._require_element_plugin(child_node_type)
        from aiida.orm import QueryBuilder

        builder = QueryBuilder(backend=self.backend).append(Data, filters={'id': child_id}, tag='child')
        try:
            child = builder.first(flat=True)
        except Exception as exc:
            msg = f'persisted container child id {child_id} could not be loaded: {exc}'
            raise exceptions.IntegrityError(msg) from exc
        if child is None or not isinstance(child, Data):
            msg = f'persisted container child id {child_id} is not a Data node'
            raise exceptions.IntegrityError(msg)
        return child

    def _ensure_materialized(self) -> None:
        """Load owned children and element-type metadata for stored containers.

        Fresh (unstored) containers start empty. Stored containers reconstruct
        their in-memory subtree from the relational owner reference,
        membership rows and element-type metadata, ordered by persisted
        position. Loaded children are marked as owned in memory. Typed child
        loading requires the real element plugins and reports missing ones;
        structural inspection without element plugins uses
        :meth:`_iter_storage_edges` instead.
        """
        if getattr(self, '_container_materialized', False):
            return
        self._container_materialized = True
        if not self.is_stored:
            return
        records = self._read_storage_records()
        if records is None:
            return
        element_type, edges = records
        self._container_element_type = element_type
        for _position, key, child_id, child_node_type in edges:
            child = self._load_stored_child(child_id, child_node_type)
            child._container_owner = self  # type: ignore[attr-defined]
            self._materialize_child(key, child)

    def _iter_storage_edges(self) -> Iterator[tuple[int, str | None, int, str]]:
        """Yield ``(position, key, child_id, child_node_type)`` from storage records.

        Structural inspection that works through storage records without
        element plugins (positions, keys, stored type identifiers). Requires
        a stored container on an ownership-capable backend.
        """
        if not self.is_stored:
            msg = 'structural storage inspection requires a stored container'
            raise exceptions.InvalidOperation(msg)
        records = self._read_storage_records()
        if records is None:
            msg = 'structural storage inspection requires a backend with ownership support'
            raise exceptions.InvalidOperation(msg)
        yield from records[1]

    def _container_root(self) -> _ContainerBase:
        """Return the outermost in-memory owner of this container (itself if standalone)."""
        root = _owned_root(self)
        return root if isinstance(root, _ContainerBase) else self

    @property
    @override
    def is_stored(self) -> bool:
        """Return whether the node is stored, recovering from an enclosing-transaction rollback if needed.

        If this subtree was stored while an outer transaction was open, the database row may have been rolled back
        after :meth:`store` returned. The first status check outside any transaction verifies the root row still
        exists and otherwise restores the retained objects to an unstored, editable, retryable state.
        """
        owner = getattr(self, '_container_owner', None)
        if getattr(self, '_container_guard_armed', False) or owner is not None:
            self._container_root()._verify_outer_persisted()
        return super().is_stored

    def _verify_outer_persisted(self) -> None:
        """Disarm the enclosing-transaction guard, recovering the subtree if its rows are gone."""
        if not getattr(self, '_container_guard_armed', False):
            return
        if self.backend.in_transaction:
            return
        if not self.backend_entity.is_stored:
            self._container_guard_armed = False
            self._container_recovery_snapshot = None
            return
        try:
            with _joined_transaction(self.backend):
                self.backend.nodes.get(pk=self.backend_entity.id)
        except exceptions.NotExistent:
            subtree = self._collect_subtree()
            snapshot = self._container_recovery_snapshot
            if snapshot is not None:
                self._recover_subtree(subtree, snapshot)
            self._container_guard_armed = False
            self._container_recovery_snapshot = None
        else:
            self._container_guard_armed = False
            self._container_recovery_snapshot = None

    @property
    def element_type(self) -> str | None:
        """Return the locked element ``node_type`` identifier, or ``None`` if no element was ever inserted."""
        self._ensure_materialized()
        return self._container_element_type

    # -- insertion / copy --

    def _require_mutable(self) -> None:
        """Raise if the stored (frozen) subtree may no longer be mutated."""
        self._ensure_materialized()
        if self.is_stored:
            msg = f'{self.__class__.__name__} with pk {self.pk} is stored and its membership is immutable'
            raise exceptions.ModificationNotAllowed(msg)

    def _clone_for_insert(self, source: Data) -> Data:
        """Validate ``source`` and return an independent owned copy ready for attachment.

        :raises TypeError: if ``source`` is not a data node or violates the locked element type.
        """
        if not isinstance(source, Data):
            msg = f'container elements must be Data nodes, got {type(source).__name__}'  # type: ignore[unreachable]
            raise TypeError(msg)
        self._ensure_materialized()
        element_type = self._container_element_type
        if element_type is not None and source.node_type != element_type:
            msg = f'container element type is locked to {element_type}, cannot insert node of type {source.node_type}'
            raise TypeError(msg)
        child: Data = source.clone()
        if element_type is None:
            self._container_element_type = source.node_type
        child._container_owner = self  # type: ignore[attr-defined]
        return child

    def _finalize_remove(self, child: Data) -> Data:
        """Detach ``child`` as a standalone, unstored, editable node and return it.

        Only the removed root is detached: descendants of a removed nested container stay owned by it. Removal never
        stores or invalidates anything; reinserting the returned node copies it again.
        """
        self._detach_owned(child)
        if getattr(child, '_container_owner', None) is self:
            child._container_owner = None  # type: ignore[attr-defined]
        return child

    @override
    def clone(self) -> Self:
        """Create a standalone recursive copy of this container and its complete owned subtree.

        Metadata handling follows :meth:`~aiida.orm.Data.clone` (attributes, repository content, extras, label,
        description, user/computer); mutable metadata is independent between the copies. The copied root is
        standalone, descendants belong to the new subtree with new identities, and no source-copy relationship,
        provenance link or source UUID metadata is recorded.
        """
        self._ensure_materialized()
        cloned = super().clone()
        cloned._container_owner = None
        cloned._container_element_type = self._container_element_type
        cloned._container_materialized = True
        cloned._container_guard_armed = False
        cloned._container_recovery_snapshot = None
        for key, child in self._iter_positioned():
            child_copy: Data = child.clone()
            child_copy._container_owner = cloned  # type: ignore[attr-defined]
            cloned._materialize_child(key, child_copy)
        return cloned

    # -- validation --

    @override
    def _validate(self) -> bool:
        """Validate the complete owned subtree before storage."""
        super()._validate()
        self._ensure_materialized()
        element_type = self._container_element_type
        for child in self._owned_children():
            if not isinstance(child, Data):
                msg = f'container elements must be Data nodes, got {type(child).__name__}'  # type: ignore[unreachable]
                raise exceptions.ValidationError(msg)
            if element_type is not None and child.node_type != element_type:
                msg = f'container element type is locked to {element_type}, found node of type {child.node_type}'
                raise exceptions.ValidationError(msg)
            if child.is_stored:
                msg = 'owned container children cannot be stored independently of their ownership root'
                raise exceptions.ValidationError(msg)
            if child.base.links.incoming_cache:
                msg = 'provenance links targeting owned container children are not supported'
                raise exceptions.ValidationError(msg)
            if child.backend.profile.uuid != self.backend.profile.uuid:
                msg = 'all nodes of a container subtree must share the same storage backend'
                raise exceptions.ValidationError(msg)
            if isinstance(child, _ContainerBase):
                child._validate()
        return True

    # -- subtree storage --

    def _collect_subtree(self) -> list[Data]:
        """Return every node of the owned subtree, children before their owner (post-order)."""
        ordered: list[Data] = []
        visiting: set[int] = set()
        visited: set[int] = set()

        def visit(node: Data) -> None:
            if id(node) in visited:
                return
            if id(node) in visiting:
                msg = 'container ownership cycle detected'
                raise exceptions.InvalidOperation(msg)
            visiting.add(id(node))
            if isinstance(node, _ContainerBase):
                node._ensure_materialized()
                for child in node._owned_children():
                    visit(child)
            visiting.remove(id(node))
            visited.add(id(node))
            ordered.append(node)

        visit(self)
        return ordered

    def _snapshot_subtree(self, subtree: list[Data]) -> dict[str, dict[str, t.Any]]:
        """Capture the recoverable in-memory/database state of every subtree node."""
        snapshot: dict[str, dict[str, t.Any]] = {}
        for node in subtree:
            bare_model = t.cast(t.Any, node.backend_entity).bare_model
            snapshot[node.uuid] = {
                'attributes': copy.deepcopy(node.base.attributes.all),
                'extras': copy.deepcopy(node.base.extras.all),
                'repository_metadata': copy.deepcopy(node.backend_entity.repository_metadata),
                'repository_content': node.base.repository.serialize_content(),
                'label': node.label,
                'description': node.description,
                'owner_id': getattr(bare_model, 'owner_id', None),
                'container_element_type': getattr(bare_model, 'container_element_type', None),
            }
        return snapshot

    def _iter_positioned(self) -> Iterator[tuple[str | None, Data]]:
        """Yield ``(key, child)`` pairs in persisted position order (``key`` is ``None`` for lists)."""
        raise NotImplementedError

    def _membership_specs(self) -> list[dict[str, t.Any]]:
        """Return the backend membership specs of this container in persisted position order.

        Each spec is ``{'child_id': int, 'child_node_type': str, 'position': int,
        'key': str | None}``. Positions are explicit integers; consumers must
        order by ``position`` because database row order is meaningless.
        Requires stored nodes (called during :meth:`store` after the subtree
        rows exist).
        """
        self._ensure_materialized()
        return [
            {'child_id': child.pk, 'child_node_type': child.node_type, 'position': position, 'key': key}
            for position, (key, child) in enumerate(self._iter_positioned())
        ]

    def _attach_storage_membership(self) -> None:
        """Persist owner references, membership rows and element-type metadata relationally.

        Calls ``backend.create_container_membership`` for every container of
        the subtree (nested containers first so parent edges reference
        already-owned children) so backend-contract validation
        (eligibility/homogeneity/exclusivity/acyclicity) runs at the backend
        level, joining the enclosing transaction. The resolved (possibly
        newly locked) element type is stored back in memory.
        """
        create = getattr(self.backend, 'create_container_membership', None)
        if create is None:
            msg = 'this storage backend does not support owned data containers'
            raise exceptions.InvalidOperation(msg)
        ordered: list[_ContainerBase] = []
        seen: set[int] = set()

        def visit(node: Data) -> None:
            if id(node) in seen:
                return
            seen.add(id(node))
            if isinstance(node, _ContainerBase):
                node._ensure_materialized()
                for child in node._owned_children():
                    visit(child)
                ordered.append(node)

        visit(self)
        for container in ordered:
            resolved = create(container.pk, container._membership_specs(), container._container_element_type)
            container._container_element_type = resolved

    def _recover_subtree(self, subtree: list[Data], snapshot: dict[str, dict[str, t.Any]]) -> None:
        """Restore retained objects to an unstored, editable, retryable state after a storage failure.

        Database rollback does not reverse repository writes; unreferenced repository objects may remain pending
        safe cleanup through normal storage maintenance. The retained objects instead receive a fresh sandbox
        repository reseeded with their snapshotted content, so content, membership, ordering and established
        element-type metadata survive and storage can be retried without fresh objects.
        """
        from aiida.manage import get_config_option
        from aiida.repository import Repository
        from aiida.repository.backend import SandboxRepositoryBackend

        get_session = getattr(self.backend, 'get_session', None)
        try:
            session = get_session() if callable(get_session) else None
        except Exception:
            session = None

        for node in subtree:
            state = snapshot.get(node.uuid)
            if state is None:
                continue
            bare_model = t.cast(t.Any, node.backend_entity).bare_model
            if session is not None:
                try:
                    session.expunge(bare_model)
                except Exception:
                    pass
            try:
                bare_model.id = None
                # Ownership columns are set in memory by `create_container_membership`; a rolled-back
                # attach leaves them populated on the retained models, so restore the snapshotted
                # (pre-store, standalone) references to keep the subtree retryable.
                if hasattr(bare_model, 'owner_id'):
                    bare_model.owner_id = state.get('owner_id')
                if hasattr(bare_model, 'container_element_type'):
                    bare_model.container_element_type = state.get('container_element_type')
            except Exception:
                pass
            node.base.attributes.reset(copy.deepcopy(state['attributes']))
            node.base.extras.reset(copy.deepcopy(state['extras']))
            try:
                node.backend_entity.repository_metadata = copy.deepcopy(state['repository_metadata'])
            except Exception:
                pass
            sandbox = get_config_option('storage.sandbox') or None
            repository = Repository(backend=SandboxRepositoryBackend(sandbox))
            for filepath, content in state['repository_content'].items():
                repository.put_object_from_filelike(io.BytesIO(content), str(filepath))
            node.base.repository._repository = repository
            node.label = state['label']
            node.description = state['description']

    @override
    def store(self) -> Self:
        """Freeze and persist the entire owned subtree atomically (repo-first, one database transaction).

        Children cannot be frozen while their parent remains mutable: owned children are rejected on independent
        storage (see :meth:`~aiida.orm.nodes.node.Node.store`). On success the subtree is immutable modulo extras.
        On failure no partial graph remains and the retained objects stay unstored, editable and retryable,
        including after the rollback of an enclosing transaction or savepoint.
        """
        if self.is_stored:
            return self
        if getattr(self, '_container_owner', None) is not None:
            msg = 'owned container children cannot be stored independently; store the ownership root instead'
            raise exceptions.ModificationNotAllowed(msg)
        self._validate_storability()
        self._validate()
        self._verify_are_parents_stored()

        subtree = self._collect_subtree()
        snapshot = self._snapshot_subtree(subtree)
        joined_outer = self.backend.in_transaction
        try:
            for node in subtree:
                node.base.repository._store()
            with self.backend.transaction():
                for node in subtree:
                    links = node.base.links.incoming_cache if node is self else []
                    node.backend_entity.store(links, clean=True)
                # Relational freeze: owner references, membership rows and
                # element-type metadata are validated and written atomically
                # with the node rows via the backend contract, joining the
                # enclosing transaction when present.
                self._attach_storage_membership()
        except Exception:
            self._recover_subtree(subtree, snapshot)
            raise

        self.base.links.incoming_cache = []
        self.base.caching.rehash()
        if joined_outer:
            # The rows may still be rolled back with the enclosing transaction; arm lazy verification (see
            # `is_stored`) and retain the snapshot for recovery.
            self._container_guard_armed = True
            self._container_recovery_snapshot = snapshot
        else:
            self._container_guard_armed = False
            self._container_recovery_snapshot = None

        if self.backend.autogroup.is_to_be_grouped(self):
            group = self.backend.autogroup.get_or_create_group()
            group.add_nodes(self)

        return self


class DataList(_ContainerBase):
    """Ordered container of data nodes (entry point ``core.data_list``).

    Elements are independent, exclusively owned copies of :class:`~aiida.orm.Data` instances sharing one exact
    concrete node type (see the module contract). Sequence scaffolding exposes length, integer indexing and
    iteration in persisted position order; slicing is not supported. Positions are persisted explicitly. Equality
    and hashing are UUID identity based: independent copies are unequal even when their content matches.
    """

    def __init__(self, value: t.Iterable[Data] | None = None, **kwargs: t.Any) -> None:
        """Initialize the node, copying each element of ``value`` as an owned child."""
        super().__init__(**kwargs)
        if value is not None:
            for element in value:
                self.append(element)

    def initialize(self) -> None:
        """Initialize the in-memory ordered membership."""
        super().initialize()
        self._container_entries: list[Data] = []

    def _owned_children(self) -> list[Data]:
        self._ensure_materialized()
        return list(self._container_entries)

    def _attach_owned(self, child: Data) -> None:
        self._container_entries.append(child)

    def _detach_owned(self, child: Data) -> None:
        self._container_entries = [entry for entry in self._container_entries if entry is not child]

    def _iter_positioned(self) -> Iterator[tuple[None, Data]]:
        self._ensure_materialized()
        for child in self._container_entries:
            yield None, child

    def _hashable_members(self) -> list[str | None]:
        self._ensure_materialized()
        return [child.base.caching._compute_hash() for child in self._container_entries]

    def __len__(self) -> int:
        self._ensure_materialized()
        return len(self._container_entries)

    def __iter__(self) -> Iterator[Data]:
        self._ensure_materialized()
        return iter(list(self._container_entries))

    def _normalize_index(self, index: int) -> int:
        """Normalize ``index`` (including negative values) or raise ``IndexError``/``TypeError``."""
        if isinstance(index, bool) or not isinstance(index, int):
            msg = f'list indices must be integers, got {type(index).__name__}'
            raise TypeError(msg)
        self._ensure_materialized()
        normalized = index + len(self._container_entries) if index < 0 else index
        if normalized < 0 or normalized >= len(self._container_entries):
            raise IndexError('list index out of range')
        return normalized

    def __getitem__(self, index: int | slice) -> Data:
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        return self._container_entries[self._normalize_index(index)]

    def __setitem__(self, index: int | slice, source: Data) -> None:
        """Replace the element at ``index`` with an independent copy of ``source`` (position preserved)."""
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        self._require_mutable()
        position = self._normalize_index(index)
        child = self._clone_for_insert(source)
        replaced = self._container_entries[position]
        self._container_entries[position] = child
        self._finalize_remove(replaced)

    def __delitem__(self, index: int | slice) -> None:
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        self._require_mutable()
        position = self._normalize_index(index)
        removed = self._container_entries.pop(position)
        self._finalize_remove(removed)

    def append(self, source: Data) -> None:
        """Append an independent copy of ``source`` as a new owned element."""
        self._require_mutable()
        self._attach_owned(self._clone_for_insert(source))

    def insert(self, index: int, source: Data) -> None:
        """Insert an independent copy of ``source`` before ``index`` (clamped like :meth:`list.insert`)."""
        if isinstance(index, bool) or not isinstance(index, int):
            msg = f'list indices must be integers, got {type(index).__name__}'
            raise TypeError(msg)
        self._require_mutable()
        child = self._clone_for_insert(source)
        size = len(self._container_entries)
        position = max(0, min(index + size if index < 0 else index, size))
        self._container_entries.insert(position, child)

    def pop(self, index: int = -1) -> Data:
        """Remove the element at ``index`` and return it detached (standalone, unstored, editable)."""
        self._require_mutable()
        removed = self._container_entries.pop(self._normalize_index(index))
        return self._finalize_remove(removed)

    def move(self, index: int, new_index: int) -> None:
        """Move the element at ``index`` to ``new_index``, shifting the elements in between."""
        self._require_mutable()
        old = self._normalize_index(index)
        child = self._container_entries.pop(old)
        size = len(self._container_entries)
        if isinstance(new_index, bool) or not isinstance(new_index, int):
            msg = f'list indices must be integers, got {type(new_index).__name__}'
            raise TypeError(msg)
        target = new_index + size + 1 if new_index < 0 else new_index
        target = max(0, min(target, size))
        self._container_entries.insert(target, child)

    def clear(self) -> None:
        """Remove all elements, detaching each as standalone (established element type stays locked)."""
        self._require_mutable()
        removed, self._container_entries = self._container_entries, []
        for child in removed:
            self._finalize_remove(child)


class DataDict(_ContainerBase):
    """String-keyed container of data nodes (entry point ``core.data_dict``).

    Values are independent, exclusively owned copies of :class:`~aiida.orm.Data` instances sharing one exact
    concrete node type (see the module contract). Keys must be strings and are never coerced. Insertion order is
    preserved and persisted via explicit positions: replacing a value keeps its position, while removing and
    reinserting a key moves it to the end. Mapping scaffolding exposes length, key lookup and iteration in
    persisted position order. Equality and hashing are UUID identity based: independent copies are unequal even
    when their content matches.
    """

    def __init__(self, value: Mapping[str, Data] | t.Iterable[tuple[str, Data]] | None = None, **kwargs: t.Any) -> None:
        """Initialize the node, copying each entry of ``value`` as an owned child."""
        super().__init__(**kwargs)
        if value is not None:
            items = value.items() if isinstance(value, Mapping) else value
            for key, element in items:
                self[key] = element

    def initialize(self) -> None:
        """Initialize the in-memory insertion-ordered membership."""
        super().initialize()
        self._container_entries: dict[str, Data] = {}

    @staticmethod
    def _check_key(key: object) -> str:
        """Validate a dictionary key (strings only, never coerced)."""
        if not isinstance(key, str):
            msg = f'dictionary keys must be strings, got {type(key).__name__}'
            raise TypeError(msg)
        return key

    def _owned_children(self) -> list[Data]:
        self._ensure_materialized()
        return list(self._container_entries.values())

    def _attach_owned(self, child: Data) -> None:
        msg = 'dictionary insertion requires an explicit key; use __setitem__'
        raise exceptions.InvalidOperation(msg)

    def _materialize_child(self, key: str | None, child: Data) -> None:
        assert key is not None
        self._container_entries[key] = child

    def _detach_owned(self, child: Data) -> None:
        for key, entry in list(self._container_entries.items()):
            if entry is child:
                del self._container_entries[key]
                return

    def _iter_positioned(self) -> Iterator[tuple[str, Data]]:
        self._ensure_materialized()
        yield from self._container_entries.items()

    def _hashable_members(self) -> dict[str, str | None]:
        self._ensure_materialized()
        return {key: child.base.caching._compute_hash() for key, child in self._container_entries.items()}

    def __len__(self) -> int:
        self._ensure_materialized()
        return len(self._container_entries)

    def __iter__(self) -> Iterator[str]:
        self._ensure_materialized()
        return iter(list(self._container_entries.keys()))

    def __contains__(self, key: object) -> bool:
        self._check_key(key)
        self._ensure_materialized()
        return key in self._container_entries

    def __getitem__(self, key: str) -> Data:
        self._check_key(key)
        self._ensure_materialized()
        try:
            return self._container_entries[key]
        except KeyError:
            raise KeyError(key) from None

    def __setitem__(self, key: str, source: Data) -> None:
        """Map ``key`` to an independent copy of ``source`` (replacement preserves position)."""
        self._check_key(key)
        self._require_mutable()
        child = self._clone_for_insert(source)
        replaced = self._container_entries.get(key)
        self._container_entries[key] = child
        if replaced is not None:
            self._finalize_remove(replaced)

    def __delitem__(self, key: str) -> None:
        self._check_key(key)
        self._require_mutable()
        try:
            removed = self._container_entries.pop(key)
        except KeyError:
            raise KeyError(key) from None
        self._finalize_remove(removed)

    def pop(self, key: str) -> Data:
        """Remove ``key`` and return its value detached (standalone, unstored, editable)."""
        self._check_key(key)
        self._require_mutable()
        try:
            removed = self._container_entries.pop(key)
        except KeyError:
            raise KeyError(key) from None
        return self._finalize_remove(removed)

    def clear(self) -> None:
        """Remove all entries, detaching each value as standalone (established element type stays locked)."""
        self._require_mutable()
        removed = list(self._container_entries.values())
        self._container_entries.clear()
        for child in removed:
            self._finalize_remove(child)

    def get(self, key: str, default: t.Any | None = None) -> t.Any:  # type: ignore[override]
        """Return the owned child for ``key`` or ``default`` if the key is absent."""
        self._check_key(key)
        self._ensure_materialized()
        return self._container_entries.get(key, default)

    def keys(self) -> Iterator[str]:
        """Iterate over keys in persisted position order."""
        self._ensure_materialized()
        yield from list(self._container_entries.keys())

    def values(self) -> Iterator[Data]:
        """Iterate over owned values in persisted position order."""
        self._ensure_materialized()
        yield from list(self._container_entries.values())

    def items(self) -> Iterator[tuple[str, Data]]:
        """Iterate over ``(key, value)`` pairs in persisted position order."""
        self._ensure_materialized()
        yield from list(self._container_entries.items())
