.. _internal_architecture:storage:containers:

**********************
Owned data containers
**********************

Most data in AiiDA is a single node: an ``Int``, a ``StructureData``, a file.
Sometimes a calculation needs an ordered collection of nodes — the frames of a trajectory, the structures of a screening study — and the collection itself has to be a node so it can be passed around, stored, and linked into the provenance graph.

That is what the owned data containers are for.
``DataList`` holds an ordered list of data nodes, ``DataDict`` maps string keys to data nodes, and each container is itself a node so it can be stored and linked into the provenance graph.
Elements are leaf data nodes or nested containers, and every element of one container must have the same concrete node type.
The container set is closed: ``DataList`` and ``DataDict`` are final, third-party containers are unsupported, and ``aiida.storage.ownership`` is the single source of truth for the reserved node types consulted by backend dispatch, class loading, and querying.

Containers share node identity (a ``DbNode`` row, a ``node_type`` string, provenance links) but they are not ``Data``: they subclass :py:class:`~aiida.orm.DataNode` via :py:class:`~aiida.orm.nodes.data.container.Container` and persist through the dedicated :py:class:`~aiida.orm.implementation.containers.BackendContainer` storage entity (``store_container``), never through ``BackendNode.store``.
Querying ``DataNode`` matches data and containers, querying ``Data`` excludes containers, and querying ``Container`` matches ``DataList`` and ``DataDict``.
This split lets container persistence evolve independently of data persistence while provenance keeps treating both as nodes.

For usage and examples, see :ref:`topics:data_containers`.
This page describes the storage implementation.
The relational storage described here is implemented, while several integrations listed under :ref:`known limitations <internal_architecture:storage:containers:limitations>` still reject container input instead of handling it.


Ownership, not links
=====================

A container owns its elements.
Ownership is recorded in two places, and deliberately in neither the node attributes nor the provenance link table:

* Every node row carries a nullable ``owner_id`` reference to ``db_dbnode.id``.
  ``NULL`` means the node is standalone; non-``NULL`` means it is owned and cannot exist on its own.
* Every owned child has exactly one row in the membership table recording its immediate owner, its position, and — for ``DataDict`` — its key.
  The membership ``owner_id`` points at the container row (``db_dbcontainer.node_id``), not at the node row, and must agree with the child's ``owner_id`` reference.

.. code-block:: text

    db_dbnode  (base table: id, owner_id, and every other node column)
    ┌────────┬──────────┬─────────┐
    │ id (PK)│ owner_id │ …       │
    ├────────┼──────────┤         │
    │ 1 list │ NULL     │         │
    │ 2 int  │ 1        │         │
    │ 3 int  │ 1        │         │
    └────────┴──────────┴─────────┘
         ▲ ▲         ▲
         │ └ self-FK ┘  owner_id ──▶ id (NULL = standalone)
         │
    db_dbcontainer  (element_type NULL when unset, layout 'row')
    ┌─────────┬──────────────┬────────┐
    │ node_id │ element_type │ layout │  node_id ──▶ db_dbnode.id
    ├─────────┼──────────────┼────────┤  (the container IS node 1)
    │ 1       │ data.Int...  │ row    │
    └─────────┴──────────────┴────────┘
         ▲
         │  membership owner_id ──▶ db_dbcontainer.node_id
         │
    db_dbmembership
    ┌──────────┬──────────┬──────────┬──────┐
    │ owner_id │ child_id │ position │ key  │
    ├──────────┼──────────┼──────────┼──────┤  child_id ──▶ db_dbnode.id
    │ 1        │ 2        │ 0        │ NULL │
    │ 1        │ 3        │ 1        │ NULL │
    └──────────┴──────────┴──────────┴──────┘

The kind markers (``db_dblistcontainer`` / ``db_dbdictcontainer``) are single-column ``node_id`` rows pointing at ``db_dbcontainer.node_id``.
Reads join the appropriate kind marker to reject cross-kind access; these tables are omitted from the sketch.

Membership rows are containment edges, not provenance.
Duplicating them as ``CREATE`` or ``INPUT`` links would claim a computation happened that never did, so containment stays in its own tables and provenance links never point at owned children directly.

Three consequences fall out of this shape.
First, ownership is exclusive and acyclic: ``child_id`` is unique, so a node can only ever have one owner, and the backend refuses self-ownership plus any edge that would close a cycle through already-stored rows.
Second, only the reserved container types can own, and only leaf data or nested containers can be owned — process nodes are rejected, which is what keeps the provenance graph honest.
Third, the finer rules (list keys are always ``NULL``, dict keys are never ``NULL`` and never coerced, positions are explicit integers with no overlap against stored rows, homogeneity against the locked ``element_type``) are enforced in Python by the shared ``aiida.storage.ownership`` module rather than in DDL, with no database triggers.
Every write path — single inserts, bulk operations, provenance links, deletion, archive import — goes through those validators, so the ORM convenience methods are never the enforcement boundary.
Uniqueness constraints make concurrent double-ownership attempts fail, but cycle checks read live state and are best-effort under concurrent writes; callers needing strict serialisation must also coordinate concurrent writers, for example with a shared locking protocol.
On SQLite, foreign-key enforcement depends on the connection ``PRAGMA foreign_keys`` setting, so the Python validation is the authoritative boundary on both backends.


Copy on insert
==============

Inserting a node into a container never adopts it.
The container clones the source recursively and owns the copy; the source keeps its identity, its lifetime, and no knowledge of the copy.
Inserting the same source twice produces two independent copies, and inserting an explicitly made copy copies it again.
There is no persistent record of which source a copy came from — no UUID back-pointer, no copy link — because a copy that outlives its source must be indistinguishable from any other standalone node.

The same rule applies at process boundaries.
Handing an owned child to a process detaches a standalone copy first, and the process executes with the copy it records as its provenance input.
Exposing an owned child as a calculation output copies it and attaches ``CREATE`` to the copy.
Workflows never copy on output: they may return a whole standalone container, but returning an owned child is rejected, since silently duplicating data out of a workflow would hide where nodes came from.

Copy-on-insert is also what makes the type rule cheap to enforce.
The first element locks the container's ``element_type`` — the exact ``node_type`` string, compared without loading any plugin — and every later insertion must match it.
The lock survives removing all elements, so a container that once held ``Int`` nodes can never later hold ``Float`` nodes, and empty containers remain storable with the lock unset.
Nested containers compare only their own concrete type: a list may hold dicts whose value types differ from each other, because each nested container enforces its own lock.


Mutable until stored
====================

Before storage, a container behaves like an ordinary Python collection: append, insert, replace, remove, reorder, clear.
Removing an element detaches just that root — it becomes standalone, unstored, and editable again, while anything nested inside it stays owned by it.
Re-inserting it copies it afresh; there is no reparenting in place.

Storing the root freezes the entire subtree at once, and the freeze is all-or-nothing.
Before any repository or database write, the root validates itself and every descendant passes the same storability check as a standalone store, with each leaf additionally receiving its normal validation; nested containers are covered once by the root recursion rather than re-validated per level.
The ORM then writes every repository file first (repo-first), then hands narrow storage specs — backend entities plus explicit position/key metadata, no ORM objects — to ``backend.store_container_subtree``.
That call writes all node rows in post-order (children before owner, root last), then all membership edges with the locked ``element_type``/``layout``, in a single backend transaction that joins any enclosing transaction.
Leaf rows go through ``BackendNode.store``; container rows go through ``BackendContainer.store_container``.
Calling the ordinary ``store`` method on a backend container raises ``IntegrityError``.
Only the ownership root receives the incoming provenance links.
If anything fails, no partially stored ownership graph is left behind: the retained Python objects are restored from snapshots to unstored, editable, retryable state, with their content, ordering, and type locks intact.
When the store joined an enclosing transaction, recovery is eager: the store registers a backend rollback hook that restores the retained subtree at rollback time, safe to observe from a retained leaf child first and correct across nested savepoints, since only the failed scope fires while outer scopes keep theirs.
Backends without hook support keep the lazy fallback: the root re-verifies its row on the next status check outside an active transaction and recovers the subtree the same way.
Database rollback cannot undo repository writes, so orphaned files are left for normal storage maintenance rather than chased synchronously — the recovered objects are reseeded from snapshots and never depend on cleanup having run.

Once stored, the subtree is immutable except for the ordinary node mutability exceptions such as extras.
Owned children cannot be stored on their own, and stored membership rows can never be changed in place.


Module overview
===============

.. code-block:: text

    src/aiida/orm/nodes/data/container.py
    ├── DataList / DataDict       public containers (entry points core.data_list / core.data_dict)
    ├── _ContainerBase            shared behaviour: validation, store, clone, hashing
    └── detach / expand helpers   process-boundary copies, ownership-unit traversal

    src/aiida/orm/implementation/containers.py
    └── BackendContainer          dedicated entity: store_container, never BackendNode.store

    src/aiida/storage/ownership.py
    ├── validate_ownership_graph  pre-write checks shared by every backend
    ├── attach_membership         the only writer of owner references and membership rows
    ├── store_container_subtree   one-transaction node-plus-edge persistence
    └── expand_ownership_closure  root-plus-subtree traversal for deletion and groups

    src/aiida/storage/{psql_dos,sqlite_dos,sqlite_temp}/backend.py
    ├── create_container_membership  backend entry point delegating to attach_membership
    ├── store_container_subtree     backend entry point joining any enclosing transaction
    ├── _ownership_models          (DbNode, DbMembership) model pair
    └── _container_models          (DbContainer, DbListContainer, DbDictContainer) model triple

    DbNode / DbContainer / DbMembership models (+ main_0003 migration)
    ├── DbNode.owner_id           nullable reference to db_dbnode.id, indexed
    ├── DbContainer               one row per container: element_type + layout
    ├── DbListContainer /          kind markers; reads join the asserted kind, so a
    │   DbDictContainer            list read through the dict accessor fails loudly
    └── DbMembership               containment edges with position / key


Deletion and groups follow the unit
===================================

Deleting a container deletes its whole subtree, subject to the ordinary provenance safeguards — owned children cannot be deleted on their own.
``backend.delete_nodes_and_connections`` must run inside a transaction and rejects any set that is not ownership-closed (``validate_deletion_set``): targeting an owned child without its root, or a container without its full subtree, fails so the caller expands to the full unit with explicit approval.
Single-row ``nodes.delete(pk)`` rejects owned-child and container targets outright with a pointer at the root.
The ``verdi`` deletion path expands the request to the ownership unit before the usual confirmation, and the backend revalidates the approved set without enlarging it.

Groups work the same way: a group contains a complete ownership unit or none of it.
Adding a container root adds the root and every descendant as explicit rows, so group iteration and queries need no special traversal.
Adding or removing through the Python API with an owned child is rejected with a pointer at the root (``ModificationNotAllowed``); the ``verdi group`` commands show the expansion and ask for confirmation before applying it.


Queries and archives
====================

QueryBuilder support is intentionally initial: joins from a container to its immediate children (``with_members``) and back (``with_owner``), with the membership edge exposed for ``position``/``key`` edge filters and projections.
Container classes are also queryable by concrete type through the shared node identity, so a ``DataList`` query never returns a ``DataDict``.
There is no recursive traversal and no container-specific aggregation yet; each join on a child matches that child, and separate joins may match different children.
``with_incoming``/``with_outgoing`` additionally traverse immediate membership at query time, without persisting anything.

Archives have no representation for ownership yet, so both directions refuse rather than silently drop it.
Exporting any selection that touches an owned node — container roots (including empty containers, which carry container state but no membership rows), nested containers, dict units, or individual owned children — fails with ``ExportValidationError``.
Import validates ownership agreement before writing anything: an archive carrying ownership data or a container node type (including empty containers) is rejected, and UUID deduplication reuses a node only when both sides agree it is standalone with no container state; any disagreement under one UUID is an integrity error, never a silent detach.


Container caching
=================

Container hashes are content-based: the element type and layout plus each child's hash, recursively, with list order significant and dict order ignored; a typed-but-emptied container hashes differently from one that never held an element.
Owner IDs and child UUIDs are excluded, so equivalent independent copies hash equally.
Cache reuse is explicitly disabled (``_cachable = False``) — restoring a cached run would have to materialise an independent ownership subtree, which the generic ``_store_from_cache`` root-only clone cannot provide — while hashing itself works.


.. _internal_architecture:storage:containers:limitations:

Known limitations
=================

- Archives cannot carry ownership yet: the archive format has no fields for owner references or membership edges, so containers are blocked from travelling through ``.aiida`` files by design until the format supports them. Exporting any selection that touches an owned node (including empty containers) fails validation, and importing an archive that carries ownership data or a container node type is rejected before anything is written — instead of silently freeing owned children into standalone nodes.
- QueryBuilder has no recursive membership traversal or container-specific aggregation.
  ``DataNode`` queries match data and containers, ``Data`` queries exclude containers, and ``Container`` queries match ``DataList`` and ``DataDict``.
- Container cache reuse is disabled (``_cachable = False``).
- Slicing a ``DataList`` raises ``TypeError``; there is no view or copy semantics for slices.
- Port validation for containers is class-only (``valid_type`` accepts ``DataNode``); element types are not checked by the port.
