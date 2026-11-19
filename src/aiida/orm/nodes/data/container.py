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
* :class:`Container` is the public base class of both and, together with
  :class:`~aiida.orm.Data`, subclasses the shared :class:`~aiida.orm.DataNode` base.

Contract summary:

* Contents: independent, exclusively owned copies of ownable nodes — any :class:`~aiida.orm.Data` subclass or
  nested container. Process nodes and other non-ownable nodes are rejected. Containers themselves are not
  :class:`~aiida.orm.Data`: they subclass :class:`~aiida.orm.DataNode` via
  :class:`~aiida.orm.nodes.data.container.Container` and persist through the dedicated ``BackendContainer``
  storage entity, while sharing node identity (``DbNode`` row, ``node_type`` string, provenance links).
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

Storage representation (relational, ``orm-container-spec.md`` §§2-3, ``orm-container-adr-01.md`` §3):

* Containment lives in the dedicated membership table (one row per owned
  child: immediate owner container, child, integer ``position``, nullable string
  ``key``), not in node attributes or provenance links. ``owner_id`` FKs point at the
  container row (``db_dbcontainer``), not the node subtype.
* Each owned child carries an indexed ``owner_id`` reference to its
  immediate owner (NULL means standalone); every membership row agrees
  with the child's reference and container, subtype and membership rows are written
  atomically via ``backend.create_container_membership``.
* The locked element-type identifier and layout discriminator live in the dedicated
  relational container row (``db_dbcontainer.element_type``/``layout``, NULL element type when
  unset), never in node attributes. Comparisons use exact stored ``node_type`` strings
  without loading element plugins. List reads join ``db_dblistcontainer`` and dict reads join
  ``db_dbdictcontainer`` so cross-kind access fails instead of returning ambiguously-interpreted
  rows.
"""

from __future__ import annotations

import contextlib
import copy
import io
import typing as t
from collections.abc import Iterator, Mapping

from typing_extensions import TypeVar

from aiida.common import exceptions
from aiida.common.lang import override
from aiida.orm.nodes.caching import NodeCaching
from aiida.orm.nodes.data.data import Data
from aiida.orm.nodes.data.datanode import DataNode
from aiida.orm.nodes.node import Node

if t.TYPE_CHECKING:
    from typing_extensions import Self

__all__ = ('Container', 'DataDict', 'DataList')

#: Nodes eligible as owned container children: leaf data or nested containers.
#: Containers share node identity but not ``Data`` semantics (see :class:`Container`).
OwnableNode = t.Union['Data', 'Container']

_Element = TypeVar('_Element', bound=Node, default=Node)


def is_container_node(node: t.Any) -> bool:
    """Return whether ``node`` is an owned-data container (``DataList``/``DataDict``)."""
    return isinstance(node, Container)


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
    root = _owned_root(node)
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


def ensure_standalone(node: Node) -> Node:
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


def detach_owned_inputs_and_copies(value: t.Any) -> tuple[t.Any, list[Node]]:
    """Replace owned children like :func:`detach_owned_inputs` and report the copies.

    Owned children are either leaf data or nested containers; both are
    standalone-copied via :meth:`~aiida.orm.nodes.node.Node.clone` without
    requiring ``Data`` semantics.

    :returns: ``(new_value, copies)`` where ``copies`` lists every
        standalone copy created during the replacement (in walk order).
    """
    copies: list[Node] = []

    def walk(entry: t.Any) -> t.Any:
        if isinstance(entry, DataNode):
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
        assert isinstance(node, Container)
        node._ensure_materialized()
        objects['container_element_type'] = node._container_element_type
        objects['container_layout'] = node._container_layout
        objects['members'] = node._hashable_members()
        return objects


def _owned_root(node: Node) -> Node | None:
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


class Container(DataNode):
    """Public base class for owned containers of data nodes.

    Containers share node identity (``DbNode`` row, ``node_type`` string,
    provenance links) but are decoupled from :class:`~aiida.orm.Data`:
    they subclass :class:`~aiida.orm.DataNode` directly and persist
    through the dedicated :class:`~aiida.orm.implementation.containers.BackendContainer`
    storage entity (``store_container``), never ``BackendNode.store``.
    Only the concrete :class:`DataList` and :class:`DataDict` subclasses are
    registered as entry points (``aiida.container`` group). This base implements
    copy-on-insert, single ownership, pre-storage mutation and atomic freeze-on-store.
    Persistence orchestration (the single storage transaction over node rows
    plus membership edges) lives in
    :meth:`aiida.storage.psql_dos.backend.PsqlDosBackend.store_container_subtree`, fed by the narrow
    :meth:`_container_store_specs` inputs; the ORM only prepares repository content first and recovers the
    retained objects on failure.
    """

    # Containers are storable nodes (like data) but through their own entry-point group and storage entity.
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'

    _cachable = False  # cache reuse explicitly disabled: generic `_store_from_cache` cannot provide
    # independent ownership subtrees (see `ContainerCaching`); content hashing itself is implemented.
    _CLS_NODE_CACHING = ContainerCaching

    def initialize(self) -> None:
        """Initialize the in-memory container state (unmaterialized, standalone, typeless)."""
        super().initialize()
        self._container_owner: Container | None = None
        self._container_materialized = False
        self._container_element_type: str | None = None
        self._container_layout: str = 'row'
        self._container_guard_armed = False
        self._container_recovery_snapshot: dict[str, dict[str, t.Any]] | None = None

    @property
    def _container_kind(self) -> t.Literal['list', 'dict']:
        """Return the membership kind of this container (``'list'``/``'dict'``)."""
        raise NotImplementedError

    # -- in-memory membership primitives (implemented by subclasses) --

    def _owned_children(self) -> list[Node]:
        """Return the owned children in persisted position order."""
        raise NotImplementedError

    def _attach_owned(self, child: Node) -> None:
        """Record an already-copied child as owned by this container."""
        raise NotImplementedError

    def _materialize_child(self, key: str | None, child: Node) -> None:
        """Record a child reconstructed from persisted membership (``key`` is ``None`` for lists)."""
        self._attach_owned(child)

    def _detach_owned(self, child: Node) -> None:
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

    def _iter_containers(self) -> Iterator[Container]:
        """Yield this container and every nested owned container."""
        yield self
        for child in self._owned_children():
            if isinstance(child, Container):
                yield from child._iter_containers()

    # -- loading / materialization --

    def _read_storage_records(self) -> tuple[str | None, str, list[tuple[int, str | None, int, str]]] | None:
        """Read persisted ``(element_type, layout, membership)`` records for this stored container.

        Kind-scoped: list containers join ``DbListContainer`` and dict containers join
        ``DbDictContainer``, so cross-kind access raises instead of returning an
        ambiguously-interpreted row. Dict ``position`` is ``ORDER BY``-only, never a lookup.

        Returns ``(element_type, layout, edges)`` where ``edges`` is a list of
        ``(position, key, child_id, child_node_type)`` ordered by persisted
        position (record order itself is meaningless). Returns ``None`` on
        backends without the ownership schema, where no containers can exist.
        """
        get_models = getattr(self.backend, '_ownership_models', None)
        get_containers = getattr(self.backend, '_container_models', None)
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
            if get_containers is None:
                msg = 'structural storage inspection requires a backend with container support'
                raise exceptions.InvalidOperation(msg)
            from aiida.storage import ownership as ownership_contract

            assert self.pk is not None  # stored containers have a pk; `_ensure_materialized` guards `is_stored`
            element_type, layout = ownership_contract.require_container_kind(
                session, get_containers(), self.pk, self._container_kind
            )
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
        return element_type, layout, edges

    @staticmethod
    def _require_container_plugin(child_node_type: str) -> None:
        """Raise if the nested-container plugin for ``child_node_type`` is missing.

        Nested containers resolve through the ``aiida.container`` entry-point
        group (decoupled from ``aiida.data``); structural operations use
        storage records directly and never call this.
        """
        from aiida.common.exceptions import MissingEntryPointError
        from aiida.plugins.entry_point import load_entry_point

        base_path, _, _ = child_node_type.rpartition('.')
        base_path = base_path.rpartition('.')[0]
        entry_point_name = base_path.removeprefix('data.')
        try:
            load_entry_point('aiida.container', entry_point_name)
        except MissingEntryPointError as exc:
            msg = (
                f'cannot load container element of type `{child_node_type}`: '
                f'the corresponding container plugin is not available: {exc}'
            )
            raise MissingEntryPointError(msg) from exc

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

    def _load_stored_child(self, child_id: int, child_node_type: str) -> Node:
        """Load a stored owned child by pk on this container's backend (typed access).

        Children are leaf data or nested containers (both share node
        identity); the query targets :class:`Node` so decoupled containers
        are found, then validated as ownable.
        """
        from aiida.storage import ownership as ownership_contract

        if ownership_contract.is_container_node_type(child_node_type):
            self._require_container_plugin(child_node_type)
        else:
            self._require_element_plugin(child_node_type)
        from aiida.orm import QueryBuilder
        from aiida.orm.nodes.node import Node as OrmNode

        builder = QueryBuilder(backend=self.backend).append(OrmNode, filters={'id': child_id}, tag='child')
        try:
            child = builder.first(flat=True)
        except Exception as exc:
            msg = f'persisted container child id {child_id} could not be loaded: {exc}'
            raise exceptions.IntegrityError(msg) from exc
        if child is None or not isinstance(child, DataNode):
            msg = f'persisted container child id {child_id} is not an ownable node'
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
        element_type, layout, edges = records
        self._container_element_type = element_type
        self._container_layout = layout
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
        yield from records[2]

    def _container_root(self) -> Container:
        """Return the outermost in-memory owner of this container (itself if standalone)."""
        root = _owned_root(self)
        return root if isinstance(root, Container) else self

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

    def _register_rollback_recovery(self, subtree: list[Node], snapshot: dict[str, dict[str, t.Any]]) -> None:
        """Register eager subtree recovery if the enclosing backend transaction rolls back.

        Uses the general storage rollback hook (a plain callable carrying no ORM assumptions for
        storage), so the same retained objects are restored to an unstored, editable, retryable state
        at rollback time regardless of whether a retained leaf child or the ownership root is inspected
        first afterwards. Backends without hook support keep the lazy verification fallback below.
        """
        add_hook = getattr(self.backend, 'add_rollback_callback', None)
        if add_hook is None or not self.backend.in_transaction:
            return

        def _recover_on_rollback() -> None:
            # Disarm before recovering: recovery mutates attributes, whose mutability checks consult
            # `is_stored`, which would otherwise re-enter lazy verification and recurse on nested subtrees.
            self._container_guard_armed = False
            self._container_recovery_snapshot = None
            self._recover_subtree(subtree, snapshot)

        add_hook(_recover_on_rollback)

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
            # Disarm before recovering: recovery mutates attributes, whose mutability checks consult
            # `is_stored`, which would otherwise re-enter this verification and recurse on nested subtrees.
            self._container_guard_armed = False
            self._container_recovery_snapshot = None
            if snapshot is not None:
                self._recover_subtree(subtree, snapshot)
        else:
            self._container_guard_armed = False
            self._container_recovery_snapshot = None

    @property
    def element_type(self) -> str | None:
        """Return the locked element ``node_type`` identifier, or ``None`` if no element was ever inserted."""
        self._ensure_materialized()
        return self._container_element_type

    @property
    def layout(self) -> str:
        """Return the locked storage-layout discriminator (``'row'`` in this iteration)."""
        self._ensure_materialized()
        return self._container_layout

    # -- insertion / copy --

    def _require_mutable(self) -> None:
        """Raise if the stored (frozen) subtree may no longer be mutated."""
        self._ensure_materialized()
        if self.is_stored:
            msg = f'{self.__class__.__name__} with pk {self.pk} is stored and its membership is immutable'
            raise exceptions.ModificationNotAllowed(msg)

    def _clone_for_insert(self, source: Node) -> Node:
        """Validate ``source`` and return an independent owned copy ready for attachment.

        Elements are leaf data or nested containers (both share node
        identity); process nodes and other non-ownable nodes are rejected.

        :raises TypeError: if ``source`` is not an ownable node or violates the locked element type.
        """
        if not isinstance(source, DataNode):
            msg = f'container elements must be data nodes or containers, got {type(source).__name__}'
            raise TypeError(msg)
        self._ensure_materialized()
        element_type = self._container_element_type
        if element_type is not None and source.node_type != element_type:
            msg = f'container element type is locked to {element_type}, cannot insert node of type {source.node_type}'
            raise TypeError(msg)
        child: Node = source.clone()
        if element_type is None:
            self._container_element_type = source.node_type
        child._container_owner = self  # type: ignore[attr-defined]
        return child

    def _finalize_remove(self, child: Node) -> Node:
        """Detach ``child`` as a standalone, unstored, editable node and return it.

        Only the removed root is detached: descendants of a removed nested container stay owned by it. Removal never
        stores or invalidates anything; reinserting the returned node copies it again.
        """
        self._detach_owned(child)
        if getattr(child, '_container_owner', None) is self:
            child._container_owner = None  # type: ignore[attr-defined]
        return child

    def __copy__(self) -> t.NoReturn:
        """Copying a container is not supported, use :meth:`clone` (copies must get new identities)."""
        msg = 'copying a container is not supported, use copy.deepcopy or call Container.clone()'
        raise exceptions.InvalidOperation(msg)

    def __deepcopy__(self, memo: t.Any) -> Self:
        """Create a clone of the container by piping through to :meth:`clone`."""
        return self.clone()

    @override
    def clone(self) -> Self:
        """Create a standalone recursive copy of this container and its complete owned subtree.

        Metadata handling mirrors :meth:`~aiida.orm.Data.clone` (attributes, repository content, extras, label,
        description, user/computer) without requiring ``Data`` semantics; mutable metadata is independent
        between the copies. The copied root is standalone, descendants belong to the new subtree with new
        identities, and no source-copy relationship, provenance link or source UUID metadata is recorded.
        """
        from aiida.orm.entities import from_backend_entity

        self._ensure_materialized()
        backend_clone = self.backend_entity.clone()
        cloned = from_backend_entity(self.__class__, backend_clone)
        cloned.base.attributes.reset(copy.deepcopy(self.base.attributes.all))
        cloned.base.extras.reset(copy.deepcopy(self.base.extras.all))
        cloned.base.repository._clone(self.base.repository)
        cloned._container_owner = None
        cloned._container_element_type = self._container_element_type
        cloned._container_layout = self._container_layout
        cloned._container_materialized = True
        cloned._container_guard_armed = False
        cloned._container_recovery_snapshot = None
        for key, child in self._iter_positioned():
            child_copy: Node = child.clone()
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
            if not isinstance(child, DataNode):
                msg = f'container elements must be data nodes or containers, got {type(child).__name__}'
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
            if isinstance(child, Container):
                child._validate()
        return True

    # -- subtree storage --

    def _collect_subtree(self) -> list[Node]:
        """Return every node of the owned subtree, children before their owner (post-order)."""
        ordered: list[Node] = []
        visiting: set[int] = set()
        visited: set[int] = set()

        def visit(node: Node) -> None:
            if id(node) in visited:
                return
            if id(node) in visiting:
                msg = 'container ownership cycle detected'
                raise exceptions.InvalidOperation(msg)
            visiting.add(id(node))
            if isinstance(node, Container):
                node._ensure_materialized()
                for child in node._owned_children():
                    visit(child)
            visiting.remove(id(node))
            visited.add(id(node))
            ordered.append(node)

        visit(self)
        return ordered

    def _snapshot_subtree(self, subtree: list[Node]) -> dict[str, dict[str, t.Any]]:
        """Capture the recoverable in-memory/database state of every subtree node."""
        snapshot: dict[str, dict[str, t.Any]] = {}
        for node in subtree:
            bare_model = t.cast(t.Any, node.backend_entity).bare_model
            entry: dict[str, t.Any] = {
                'attributes': copy.deepcopy(node.base.attributes.all),
                'extras': copy.deepcopy(node.base.extras.all),
                'repository_metadata': copy.deepcopy(node.backend_entity.repository_metadata),
                'repository_content': node.base.repository.serialize_content(),
                'label': node.label,
                'description': node.description,
                'owner_id': getattr(bare_model, 'owner_id', None),
            }
            if isinstance(node, Container):
                # Container state lives in `db_dbcontainer`, locked at first-element time alongside
                # the element type; snapshot the in-memory locks so recovery restores them.
                entry['container_element_type'] = node._container_element_type
                entry['container_layout'] = node._container_layout
            snapshot[node.uuid] = entry
        return snapshot

    def _iter_positioned(self) -> Iterator[tuple[str | None, Node]]:
        """Yield ``(key, child)`` pairs in persisted position order (``key`` is ``None`` for lists)."""
        raise NotImplementedError

    def _container_store_specs(self) -> tuple[list[Container], list[t.Any]]:
        """Return the nested-first containers and their narrow storage membership specs.

        Each spec references backend entities with explicit ``position``/``key``
        metadata (no ORM container objects or callbacks cross into storage);
        child ``node_type`` identifiers and pks are resolved by the storage
        layer after the node rows exist. Containers are ordered nested-first so
        parent edges reference already-owned children.
        """
        from aiida.storage import ownership as ownership_contract

        ordered: list[Container] = []
        seen: set[int] = set()

        def visit(node: Node) -> None:
            if id(node) in seen:
                return
            seen.add(id(node))
            if isinstance(node, Container):
                node._ensure_materialized()
                for child in node._owned_children():
                    visit(child)
                ordered.append(node)

        visit(self)
        specs = [
            ownership_contract.OwnedContainerSpec(
                owner=container.backend_entity,
                members=[
                    ownership_contract.OwnedMemberSpec(entity=child.backend_entity, position=position, key=key)
                    for position, (key, child) in enumerate(container._iter_positioned())
                ],
                element_type=container._container_element_type,
                kind=container._container_kind,
                layout=container._container_layout,
            )
            for container in ordered
        ]
        return ordered, specs

    def _recover_subtree(self, subtree: list[Node], snapshot: dict[str, dict[str, t.Any]]) -> None:
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
                # Ownership references are set in memory by `create_container_membership`; a rolled-back
                # attach leaves them populated on the retained models, so restore the snapshotted
                # (pre-store, standalone) references to keep the subtree retryable. Container rows
                # (`db_dbcontainer` + kind markers) vanish with the database rollback; the in-memory
                # element-type/layout locks below survive on the retained objects.
                if hasattr(bare_model, 'owner_id'):
                    bare_model.owner_id = state.get('owner_id')
            except Exception:
                pass
            if isinstance(node, Container):
                node._container_element_type = state.get('container_element_type')
                node._container_layout = state.get('container_layout', 'row')
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
        for node in subtree:
            if node is self:
                continue
            node._validate_storability()
            # Nested containers were validated recursively by the root.
            if not isinstance(node, Container):
                node._validate()
        snapshot = self._snapshot_subtree(subtree)
        joined_outer = self.backend.in_transaction
        store_subtree = getattr(self.backend, 'store_container_subtree', None)
        if store_subtree is None:
            msg = 'this storage backend does not support owned data containers'
            raise exceptions.InvalidOperation(msg)
        try:
            for node in subtree:
                node.base.repository._store()
            containers_and_specs = self._container_store_specs()
            # Atomic relational freeze: node rows and owner references,
            # membership rows and element-type metadata are validated and
            # written in one storage transaction joining the enclosing
            # transaction when present. Only the ownership root carries
            # incoming provenance links.
            resolved = store_subtree(
                [node.backend_entity for node in subtree],
                containers_and_specs[1],
                root_links=self.base.links.incoming_cache,
                clean=True,
            )
            for container, element_type in zip(containers_and_specs[0], resolved, strict=True):
                container._container_element_type = element_type
        except Exception:
            self._recover_subtree(subtree, snapshot)
            raise

        self.base.links.incoming_cache = []
        self.base.caching.rehash()
        if joined_outer:
            # The rows may still be rolled back with the enclosing transaction: recover eagerly through a
            # rollback hook (child-first safe, no root check needed), keeping lazy verification (see
            # `is_stored`) as a fallback for backends without hook support.
            self._container_guard_armed = True
            self._container_recovery_snapshot = snapshot
            self._register_rollback_recovery(subtree, snapshot)
        else:
            self._container_guard_armed = False
            self._container_recovery_snapshot = None

        if self.backend.autogroup.is_to_be_grouped(self):
            group = self.backend.autogroup.get_or_create_group()
            group.add_nodes(self)

        return self


# Backwards-compatible alias for the former private base class name.
_ContainerBase = Container


@t.final
class DataList(Container, t.Generic[_Element]):
    """Ordered container of data nodes (entry point ``core.data_list`` of the ``aiida.container`` group).

    Elements are independent, exclusively owned copies of ownable nodes (leaf data or nested containers) sharing
    one exact concrete node type (see the module contract). Sequence scaffolding exposes length, integer indexing and
    iteration in persisted position order; slicing is not supported. Positions are persisted explicitly. Equality
    and hashing are UUID identity based: independent copies are unequal even when their content matches.

    ``DataList[StructureData]`` annotates the element type for static type checkers. The parameter is erased at runtime:
    storage and ports still use ``DataList``, and the existing concrete-type homogeneity rules remain unchanged.
    """

    @property
    @override
    def _container_kind(self) -> t.Literal['list', 'dict']:
        """Return the membership kind of this container (``'list'``)."""
        return 'list'

    def __init__(self, value: t.Iterable[_Element] | None = None, **kwargs: t.Any) -> None:
        """Initialize the node, copying each element of ``value`` as an owned child."""
        super().__init__(**kwargs)
        if value is not None:
            for element in value:
                self.append(element)

    def initialize(self) -> None:
        """Initialize the in-memory ordered membership."""
        super().initialize()
        self._container_entries: list[Node] = []

    def _owned_children(self) -> list[Node]:
        self._ensure_materialized()
        return list(self._container_entries)

    def _attach_owned(self, child: Node) -> None:
        self._container_entries.append(child)

    def _detach_owned(self, child: Node) -> None:
        self._container_entries = [entry for entry in self._container_entries if entry is not child]

    def _iter_positioned(self) -> Iterator[tuple[None, Node]]:
        self._ensure_materialized()
        for child in self._container_entries:
            yield None, child

    def _hashable_members(self) -> list[str | None]:
        self._ensure_materialized()
        return [child.base.caching._compute_hash() for child in self._container_entries]

    def __len__(self) -> int:
        self._ensure_materialized()
        return len(self._container_entries)

    def __iter__(self) -> Iterator[_Element]:
        self._ensure_materialized()
        return iter(t.cast('list[_Element]', list(self._container_entries)))

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

    def __getitem__(self, index: int | slice) -> _Element:
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        return t.cast('_Element', self._container_entries[self._normalize_index(index)])

    def __setitem__(self, index: int | slice, source: _Element) -> None:
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

    def append(self, source: _Element) -> None:
        """Append an independent copy of ``source`` as a new owned element."""
        self._require_mutable()
        self._attach_owned(self._clone_for_insert(source))

    def insert(self, index: int, source: _Element) -> None:
        """Insert an independent copy of ``source`` before ``index`` (clamped like :meth:`list.insert`)."""
        if isinstance(index, bool) or not isinstance(index, int):
            msg = f'list indices must be integers, got {type(index).__name__}'
            raise TypeError(msg)
        self._require_mutable()
        child = self._clone_for_insert(source)
        size = len(self._container_entries)
        position = max(0, min(index + size if index < 0 else index, size))
        self._container_entries.insert(position, child)

    def pop(self, index: int = -1) -> _Element:
        """Remove the element at ``index`` and return it detached (standalone, unstored, editable)."""
        self._require_mutable()
        removed = self._container_entries.pop(self._normalize_index(index))
        return t.cast('_Element', self._finalize_remove(removed))

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


@t.final
class DataDict(Container):
    """String-keyed container of data nodes (entry point ``core.data_dict`` of the ``aiida.container`` group).

    Values are independent, exclusively owned copies of ownable nodes (leaf data or nested containers) sharing one
    exact concrete node type (see the module contract). Keys must be strings and are never coerced. Insertion order is
    preserved and persisted via explicit positions: replacing a value keeps its position, while removing and
    reinserting a key moves it to the end. Mapping scaffolding exposes length, key lookup and iteration in
    persisted position order. Equality and hashing are UUID identity based: independent copies are unequal even
    when their content matches.
    """

    @property
    @override
    def _container_kind(self) -> t.Literal['list', 'dict']:
        """Return the membership kind of this container (``'dict'``)."""
        return 'dict'

    def __init__(self, value: Mapping[str, Node] | t.Iterable[tuple[str, Node]] | None = None, **kwargs: t.Any) -> None:
        """Initialize the node, copying each entry of ``value`` as an owned child."""
        super().__init__(**kwargs)
        if value is not None:
            items = value.items() if isinstance(value, Mapping) else value
            for key, element in items:
                self[key] = element

    def initialize(self) -> None:
        """Initialize the in-memory insertion-ordered membership."""
        super().initialize()
        self._container_entries: dict[str, Node] = {}

    @staticmethod
    def _check_key(key: object) -> str:
        """Validate a dictionary key (strings only, never coerced)."""
        if not isinstance(key, str):
            msg = f'dictionary keys must be strings, got {type(key).__name__}'
            raise TypeError(msg)
        return key

    def _owned_children(self) -> list[Node]:
        self._ensure_materialized()
        return list(self._container_entries.values())

    def _attach_owned(self, child: Node) -> None:
        msg = 'dictionary insertion requires an explicit key; use __setitem__'
        raise exceptions.InvalidOperation(msg)

    def _materialize_child(self, key: str | None, child: Node) -> None:
        assert key is not None
        self._container_entries[key] = child

    def _detach_owned(self, child: Node) -> None:
        for key, entry in list(self._container_entries.items()):
            if entry is child:
                del self._container_entries[key]
                return

    def _iter_positioned(self) -> Iterator[tuple[str, Node]]:
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

    def __getitem__(self, key: str) -> Node:
        self._check_key(key)
        self._ensure_materialized()
        try:
            return self._container_entries[key]
        except KeyError:
            raise KeyError(key) from None

    def __setitem__(self, key: str, source: Node) -> None:
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

    def pop(self, key: str) -> Node:
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

    def values(self) -> Iterator[Node]:
        """Iterate over owned values in persisted position order."""
        self._ensure_materialized()
        yield from list(self._container_entries.values())

    def items(self) -> Iterator[tuple[str, Node]]:
        """Iterate over ``(key, value)`` pairs in persisted position order."""
        self._ensure_materialized()
        yield from list(self._container_entries.items())
