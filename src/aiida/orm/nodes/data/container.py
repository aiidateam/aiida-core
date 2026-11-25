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
* :class:`Container` is the public base class of both and subclasses :class:`~aiida.orm.Data`.

Contract summary:

* Contents: :class:`~aiida.orm.Data` nodes, including nested containers. Process nodes are rejected.
* Members may have different concrete node types, including nested containers.
* Insertion retains the supplied node. Storage claims ownership of unstored members and rejects duplicate
  memberships or already-owned nodes. ``DataList`` can reference stored standalone leaf data without taking
  ownership. To use an already-owned node or stored container, insert an explicit clone.
* Recursive copy: copying a container recursively copies its owned subtree. The copied root is standalone with new
  identities and no provenance links or source-tracking metadata. Metadata handling (attributes, repository content,
  extras, label, description, user/computer) follows :meth:`~aiida.orm.Data.clone`; mutable metadata is independent
  between copies.
* Pre-storage mutation: insertion, replacement, removal and reordering are allowed while unstored. Removing
  a draft membership leaves the node unchanged.
* Freeze-on-store: storing the ownership root validates the complete subtree, prepares repository content first
  (repo-first), then persists every node in one database transaction joining an enclosing transaction when present.
  Success freezes the whole subtree (immutable modulo extras); failure leaves no partial graph and the retained
  objects stay unstored, editable and retryable.
* Ordering/keys: positions are persisted explicitly; database row order is meaningless. ORM iteration follows
  persisted position order after reloading. Dictionary keys are literal strings, not process port names.
  Replacement preserves position, and remove-plus-reinsert moves the key to the end.
* Python behavior: sequence/mapping scaffolding exposes length, indexing/key lookup and iteration. Slicing is not
  supported. Equality and hashing follow base :class:`~aiida.orm.Node` identity (UUID) behavior; independent copies
  are unequal even when their content matches.

Storage representation (relational, ``orm-container-spec.md`` §§2-3, ``orm-container-adr-01.md`` §3):

* Containment lives in the dedicated membership table (one row per owned
  child: immediate owner container, child, integer ``position``, nullable string
  ``key``), not in node attributes or provenance links. Both endpoints refer to
  node rows.
* Each owned child carries an indexed ``owner_id`` reference to its
  immediate owner (NULL means standalone); the reference and the corresponding
  membership row are written atomically via ``backend.create_container_membership``.
* Each container's kind (``'list'``/``'dict'``) is derived from its own node row via
  ``storage.ownership.container_kind_for``; cross-kind access fails. Each child's concrete type is read
  from its own node row.
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
from aiida.orm.nodes.node import Node

if t.TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Self

    from aiida.storage.ownership import OwnedContainerSpec

__all__ = ('Container', 'DataDict', 'DataList')


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
            return get_session().query(node_model.owner_id).filter(node_model.id == node.pk).scalar()
    except Exception:
        return None


def is_owned(node: Node) -> bool:
    """Return whether ``node`` is an owned container child.

    Stored ownership is authoritative: a retained member handle can outlive
    its owner when the owner is deleted with detachment enabled.
    """
    if node.is_stored:
        return stored_owner_id(node) is not None
    return getattr(node, '_container_owner', None) is not None


def ownership_root(node: Node) -> Node:
    """Return the outermost in-memory owner of ``node`` (itself if standalone)."""
    root = _owned_root(node)
    return root if root is not None else node


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
    occurred, so unaffected input structures keep their identity.
    """

    def walk(entry: t.Any) -> t.Any:
        if isinstance(entry, Data):
            return ensure_standalone(entry)
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

    return walk(value)


class ContainerCaching(NodeCaching):
    """Content-based recursive caching hash for owned data containers (spec §10).

    The hash incorporates child content recursively, excluding owner IDs and
    child UUIDs, so equivalent independent copies hash equally:

    * lists contribute the ordered sequence of child content hashes
      (element order matters; plain ``list`` hashing is order-sensitive);
    * dictionaries contribute the ``{key: child hash}`` mapping (insertion
      order ignored; ``make_hash`` sorts mappings by hashed key).

    Child hashes are content hashes (class, attributes, repository content,
    computer) that never embed UUIDs or owner references. These hashes are not
    safe for process cache reuse: membership can change after a run, and a
    process can observe dictionary order even though the hash ignores it.
    """

    @override
    def get_objects_to_hash(self) -> dict[str, t.Any]:
        """Return the content objects contributing to the container hash."""
        objects = super().get_objects_to_hash()
        node = self._node
        assert isinstance(node, Container)
        node._ensure_materialized()
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


class Container(Data):
    """Public base class for owned containers of data nodes.

    Containers are data nodes but persist through the dedicated
    :class:`~aiida.orm.implementation.containers.BackendContainer` storage entity
    (``store_container``), never ``BackendNode.store``.
    Only the concrete :class:`DataList` and :class:`DataDict` subclasses are
    registered as entry points (``aiida.container`` group). This base implements
    identity-preserving insertion, single ownership at store time, and atomic freeze-on-store.
    Persistence orchestration (the single storage transaction over node rows
    plus membership edges) lives in
    :meth:`aiida.storage.psql_dos.backend.PsqlDosBackend.store_container_subtree`, fed by the narrow
    :meth:`_container_store_specs` inputs; the ORM only prepares repository content first and recovers the
    retained objects on failure.
    """

    # Containers are storable nodes (like data) but through their own entry-point group and storage entity.
    _storable = True
    _unstorable_message = 'storing for this node has been disabled'

    _cachable = False
    _CLS_NODE_CACHING = ContainerCaching

    def initialize(self) -> None:
        """Initialize the in-memory state of a standalone, unmaterialized container."""
        super().initialize()
        self._container_owner: Container | None = None
        self._container_entries: list[Node] | dict[str, Node]
        self._container_materialized = False
        self._container_membership_mtime: datetime | None = None
        self._container_guard_armed = False
        self._container_recovery_snapshot: dict[str, dict[str, t.Any]] | None = None

    @property
    def _container_kind(self) -> t.Literal['list', 'dict']:
        """Return the membership kind of this container (``'list'``/``'dict'``)."""
        raise NotImplementedError

    def _owns(self, child: Node) -> bool:
        return getattr(child, '_container_owner', None) is self

    def _owned_children(self) -> Iterator[Node]:
        """Yield the owned children in persisted position order."""
        return (child for _, child in self._iter_positioned() if self._owns(child))

    # -- in-memory membership primitives (implemented by subclasses) --

    def _materialize_child(self, key: str | None, child: Node) -> None:
        """Record a copied or reloaded member (``key`` is ``None`` for lists)."""
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

    def _read_storage_records(self) -> list[tuple[int, str | None, int, str, bool]] | None:
        """Read persisted membership records for this stored container.

        Kind validation is derived from the owner's own node row via
        ``storage.ownership.container_kind_for``: cross-kind access raises instead of returning an
        ambiguously-interpreted row. Dict ``position`` is ``ORDER BY``-only, never a lookup.

        Returns ``(position, key, child_id, child_node_type, owned)`` ordered by persisted
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
            from aiida.storage import ownership as ownership_contract

            if ownership_contract.container_kind_for(owner_row.node_type) != self._container_kind:
                msg = (
                    f'Container-kind mismatch: node {self.pk} has type {owner_row.node_type!r}, '
                    f'which cannot be accessed as a {self._container_kind} container.'
                )
                raise exceptions.IntegrityError(msg)
            edge_rows = (
                session.query(membership_model)
                .filter(membership_model.owner_id == self.pk)
                .order_by(membership_model.position)
                .all()
            )
            child_ids = [edge.child_id for edge in edge_rows]
            child_rows = session.query(node_model).filter(node_model.id.in_(child_ids)).all() if child_ids else []
        by_id = {row.id: row for row in child_rows}
        edges: list[tuple[int, str | None, int, str, bool]] = []
        for edge in edge_rows:
            child_row = by_id.get(edge.child_id)
            if child_row is None:
                msg = f'membership edge of container {self.pk} references missing child {edge.child_id}'
                raise exceptions.IntegrityError(msg)
            edges.append((edge.position, edge.key, edge.child_id, child_row.node_type, child_row.owner_id == self.pk))
        return edges

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

        The query retrieves the node by identity and checks that it is ownable.
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
        if child is None or not isinstance(child, Data):
            msg = f'persisted container child id {child_id} is not an ownable node'
            raise exceptions.IntegrityError(msg)
        return child

    def _ensure_materialized(self) -> None:
        """Load owned children and element-type metadata for stored containers.

        Stored container handles refresh when storage changes membership on deletion or archive import.
        Loaded children are ordered by persisted position and marked as owned in memory when applicable.
        Structural inspection without loading element plugins uses :meth:`_iter_storage_edges` instead.
        """
        if not self.is_stored:
            self._container_materialized = True
            return
        mtime = self.mtime
        if self._container_materialized and self._container_membership_mtime in (None, mtime):
            self._container_membership_mtime = mtime
            return
        edges = self._read_storage_records()
        if edges is None:
            return
        children = [(key, self._load_stored_child(pk, node_type), owned) for _, key, pk, node_type, owned in edges]
        self._container_entries.clear()
        for key, child, owned in children:
            if owned:
                child._container_owner = self  # type: ignore[attr-defined]
            self._materialize_child(key, child)
        self._container_materialized = True
        self._container_membership_mtime = mtime

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
        for position, key, child_id, child_node_type, _ in records:
            yield position, key, child_id, child_node_type

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
            snapshot = self._container_recovery_snapshot
            # Disarm before recovering: recovery mutates attributes, whose mutability checks consult
            # `is_stored`, which would otherwise re-enter this verification and recurse on nested subtrees.
            self._container_guard_armed = False
            self._container_recovery_snapshot = None
            if snapshot is not None:
                self._recover_subtree(self._collect_subtree(stored=True), snapshot)
        else:
            self._container_guard_armed = False
            self._container_recovery_snapshot = None

    # -- insertion / copy --

    def _require_mutable(self) -> None:
        """Raise if the stored (frozen) subtree may no longer be mutated."""
        self._ensure_materialized()
        if self.is_stored:
            msg = f'{self.__class__.__name__} with pk {self.pk} is stored and its membership is immutable'
            raise exceptions.ModificationNotAllowed(msg)

    @staticmethod
    def _prepare_member(source: Node) -> Data:
        """Accept a data node without claiming ownership until storage."""
        if not isinstance(source, Data):
            msg = f'container elements must be data nodes or containers, got {type(source).__name__}'
            raise TypeError(msg)
        return source

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
        description, user/computer); mutable metadata is independent
        between the copies. The copied root is standalone, descendants belong to the new subtree with new
        identities, and no source-copy relationship, provenance link or source UUID metadata is recorded.
        """
        return self._clone_subtree(set())

    def _clone_subtree(self, ancestors: set[str]) -> Self:
        if self.uuid in ancestors:
            msg = f'container ownership cycle detected at node {self.uuid}'
            raise exceptions.IntegrityError(msg)
        self._ensure_materialized()
        cloned = super().clone()
        cloned._container_materialized = True
        ancestors.add(self.uuid)
        try:
            for key, child in self._iter_positioned():
                child_copy = child._clone_subtree(ancestors) if isinstance(child, Container) else child.clone()
                cloned._materialize_child(key, child_copy)
        finally:
            ancestors.remove(self.uuid)
        return cloned

    # -- subtree storage --

    def _collect_subtree(self, *, stored: bool = False) -> list[Node]:
        """Validate a draft and collect nodes to store, or collect owned nodes for rollback.

        Nodes are returned in post-order. The draft walk checks identities across the
        entire tree, including members that will be linked as stored references.
        """
        ordered: list[Node] = []
        visiting: set[str] = set()
        owners: dict[str, str] = {}

        def visit(node: Node) -> None:
            visiting.add(node.uuid)
            if isinstance(node, Container):
                children = node._owned_children() if stored else (child for _, child in node._iter_positioned())
                for child in children:
                    if child.uuid in visiting:
                        msg = f'container ownership cycle detected at node {child.uuid}'
                        raise exceptions.IntegrityError(msg)
                    if child.uuid in owners:
                        msg = (
                            f'node {child.uuid} has multiple memberships in the proposed tree '
                            f'(containers {owners[child.uuid]} and {node.uuid}); use an explicit clone to repeat it'
                        )
                        raise exceptions.IntegrityError(msg)
                    owners[child.uuid] = node.uuid
                    if not stored and node._validate_member_for_store(child):
                        continue
                    visit(child)
            visiting.remove(node.uuid)
            ordered.append(node)

        visit(self)
        return ordered

    def _validate_member_for_store(self, child: Node) -> bool:
        """Validate a draft membership and return whether it is a stored reference."""
        if child.backend.profile.uuid != self.backend.profile.uuid:
            msg = 'all nodes of a container subtree must share the same storage backend'
            raise exceptions.ValidationError(msg)
        if child.is_stored:
            if is_owned(child):
                msg = f'node {child.uuid} is already owned by another container; insert an explicit clone instead'
                raise exceptions.IntegrityError(msg)
            if not isinstance(self, DataList) or isinstance(child, Container):
                msg = f'cannot insert stored node {child.uuid} here; insert an explicit clone instead'
                raise exceptions.IntegrityError(msg)
            return True
        if child.base.links.incoming_cache:
            msg = 'provenance links targeting owned container children are not supported'
            raise exceptions.ValidationError(msg)
        return False

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
            snapshot[node.uuid] = entry
        return snapshot

    def _iter_positioned(self) -> Iterator[tuple[str | None, Node]]:
        """Yield ``(key, child)`` pairs in persisted position order (``key`` is ``None`` for lists)."""
        raise NotImplementedError

    def _container_store_specs(self, subtree: list[Node]) -> list[OwnedContainerSpec]:
        """Return the narrow storage membership specs, nested containers first.

        Each spec references backend entities with explicit ``position``/``key``
        metadata (no ORM container objects or callbacks cross into storage);
        child ``node_type`` identifiers and pks are resolved by the storage
        layer after the node rows exist. Containers are ordered nested-first so
        parent edges reference already-owned children.
        """
        from aiida.storage import ownership as ownership_contract

        to_store = {node.uuid for node in subtree}
        return [
            ownership_contract.OwnedContainerSpec(
                owner=container.backend_entity,
                members=[
                    ownership_contract.OwnedMemberSpec(
                        entity=child.backend_entity, position=position, key=key, reference=child.uuid not in to_store
                    )
                    for position, (key, child) in enumerate(container._iter_positioned())
                ],
                kind=container._container_kind,
            )
            for container in subtree
            if isinstance(container, Container)
        ]

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
            node._container_owner = None  # type: ignore[attr-defined]
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
                # (pre-store, standalone) references to keep the subtree retryable.
                if hasattr(bare_model, 'owner_id'):
                    bare_model.owner_id = state.get('owner_id')
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

        Ownership is claimed only at storage. Conflicting draft memberships and already-owned nodes are rejected
        before writing. On success the subtree is immutable modulo extras.
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
            node._validate()
        specs = self._container_store_specs(subtree)
        snapshot = self._snapshot_subtree(subtree)
        joined_outer = self.backend.in_transaction
        store_subtree = getattr(self.backend, 'store_container_subtree', None)
        if store_subtree is None:
            msg = 'this storage backend does not support owned data containers'
            raise exceptions.InvalidOperation(msg)
        try:
            for node in subtree:
                node.base.repository._store()
            # Atomic relational freeze: node rows, owner references and membership rows
            # are validated and written in one storage transaction joining the enclosing
            # transaction when present. Only the ownership root carries
            # incoming provenance links.
            store_subtree(
                [node.backend_entity for node in subtree],
                specs,
                root_links=self.base.links.incoming_cache,
                clean=True,
            )
        except Exception:
            self._recover_subtree(subtree, snapshot)
            raise

        for node in subtree:
            if isinstance(node, Container):
                for _, child in node._iter_positioned():
                    if child.uuid in snapshot:
                        child._container_owner = node  # type: ignore[attr-defined]
        self.base.links.incoming_cache = []
        self.base.caching.rehash()
        self._container_membership_mtime = self.mtime
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
class DataList(Container):
    """Ordered container of data nodes (entry point ``core.data_list`` of the ``aiida.container`` group).

    Elements retain their identity. At storage, the list owns unstored nodes and references stored standalone leaf
    data without adopting it. Sequence scaffolding exposes length, integer indexing and
    iteration in persisted position order; slicing is not supported. Positions are persisted explicitly. Equality
    and hashing are UUID identity based: independent copies are unequal even when their content matches.
    """

    @property
    @override
    def _container_kind(self) -> t.Literal['list', 'dict']:
        """Return the membership kind of this container (``'list'``)."""
        return 'list'

    def __init__(self, value: t.Iterable[Node] | None = None, **kwargs: t.Any) -> None:
        """Initialize the node by appending each element of ``value``."""
        super().__init__(**kwargs)
        if value is not None:
            for element in value:
                self.append(element)

    def initialize(self) -> None:
        """Initialize the in-memory ordered membership."""
        super().initialize()
        self._container_entries: list[Node] = []

    def _materialize_child(self, key: str | None, child: Node) -> None:
        self._container_entries.append(child)

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

    def __iter__(self) -> Iterator[Node]:
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

    def __getitem__(self, index: int | slice) -> Node:
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        return self._container_entries[self._normalize_index(index)]

    def __setitem__(self, index: int | slice, source: Node) -> None:
        """Replace the element at ``index`` using the same insertion rules as :meth:`append`."""
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        self._require_mutable()
        position = self._normalize_index(index)
        self._container_entries[position] = self._prepare_member(source)

    def __delitem__(self, index: int | slice) -> None:
        if isinstance(index, slice):
            msg = 'slicing DataList is not supported'
            raise TypeError(msg)
        self._require_mutable()
        position = self._normalize_index(index)
        del self._container_entries[position]

    def append(self, source: Node) -> None:
        """Append the supplied node without copying it.

        :param source: the data node or container to append.
        """
        self._require_mutable()
        self._container_entries.append(self._prepare_member(source))

    def insert(self, index: int, source: Node) -> None:
        """Insert before ``index`` using the same insertion rules as :meth:`append`."""
        if isinstance(index, bool) or not isinstance(index, int):
            msg = f'list indices must be integers, got {type(index).__name__}'
            raise TypeError(msg)
        self._require_mutable()
        child = self._prepare_member(source)
        size = len(self._container_entries)
        position = max(0, min(index + size if index < 0 else index, size))
        self._container_entries.insert(position, child)

    def pop(self, index: int = -1) -> Node:
        """Remove and return the draft member unchanged."""
        self._require_mutable()
        return self._container_entries.pop(self._normalize_index(index))

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
        """Remove all draft memberships."""
        self._require_mutable()
        self._container_entries.clear()


@t.final
class DataDict(Container):
    """String-keyed container of data nodes (entry point ``core.data_dict`` of the ``aiida.container`` group).

    Values retain their identity and must be unstored when the dictionary claims them at storage.
    They can have different concrete types. Keys are literal strings and are never coerced. To be stored, they
    must be at most 255 characters and contain no NUL characters. Insertion order is preserved and persisted
    via explicit positions: replacing a value keeps its position, while removing and reinserting a key moves it
    to the end. Mapping scaffolding exposes length, key lookup and iteration in
    persisted position order. Equality and hashing are UUID identity based: independent copies are unequal even
    when their content matches.
    """

    @property
    @override
    def _container_kind(self) -> t.Literal['list', 'dict']:
        """Return the membership kind of this container (``'dict'``)."""
        return 'dict'

    def __init__(self, value: Mapping[str, Node] | t.Iterable[tuple[str, Node]] | None = None, **kwargs: t.Any) -> None:
        """Initialize with the supplied nodes as draft members."""
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
        """Require a string before SQLite's text affinity can coerce a non-string key."""
        if not isinstance(key, str):
            msg = f'dictionary keys must be strings, got {type(key).__name__}'
            raise TypeError(msg)
        return key

    def _materialize_child(self, key: str | None, child: Node) -> None:
        assert key is not None
        self._container_entries[key] = child

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
        """Map ``key`` to ``source`` without copying (replacement preserves position)."""
        self._check_key(key)
        self._require_mutable()
        self._container_entries[key] = self._prepare_member(source)

    def __delitem__(self, key: str) -> None:
        self._check_key(key)
        self._require_mutable()
        try:
            del self._container_entries[key]
        except KeyError:
            raise KeyError(key) from None

    def pop(self, key: str) -> Node:
        """Remove ``key`` and return its draft member unchanged."""
        self._check_key(key)
        self._require_mutable()
        try:
            return self._container_entries.pop(key)
        except KeyError:
            raise KeyError(key) from None

    def clear(self) -> None:
        """Remove all draft memberships."""
        self._require_mutable()
        self._container_entries.clear()

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
