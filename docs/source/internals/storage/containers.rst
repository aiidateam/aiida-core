.. _internal_architecture:storage:containers:

**********************
Owned data containers
**********************

Most data in AiiDA is a single node: an ``Int``, a ``StructureData``, a file.
Sometimes a calculation needs an ordered collection of nodes — the frames of a trajectory, the structures of a screening study — and the collection itself has to be a node so it can be passed around, stored, and linked into the provenance graph.

That is what the owned data containers are for.
``DataList`` holds an ordered list of data nodes, ``DataDict`` maps string keys to data nodes, and each container is itself a node so it can be stored and linked into the provenance graph.
Elements are leaf data nodes or nested containers and can have different concrete node types.
The container set is closed: ``DataList`` and ``DataDict`` are final, third-party containers are unsupported, and ``aiida.storage.ownership`` is the single source of truth for the reserved node types consulted by backend dispatch, class loading, and querying.

Containers are :py:class:`~aiida.orm.Data` nodes, but persist through the dedicated :py:class:`~aiida.orm.implementation.containers.BackendContainer` storage entity (``store_container``), never through ``BackendNode.store``.
Querying ``Data`` matches containers and other data nodes, and querying ``Container`` matches only ``DataList`` and ``DataDict``.
This split lets container persistence evolve independently of data persistence while provenance keeps treating both as nodes.

For usage and examples, see :ref:`topics:data_containers`.
This page describes the storage implementation.
The relational storage described here is implemented, while several integrations listed under :ref:`known limitations <internal_architecture:storage:containers:limitations>` still reject container input instead of handling it.


Ownership, not links
=====================

Storage claims ownership of unstored members; a ``DataList`` can reference a stored standalone leaf without owning it.
Ownership is recorded in two places, and deliberately in neither the node attributes nor the provenance link table:

* Every node row carries a nullable ``owner_id`` reference to ``db_dbnode.id``.
  ``NULL`` means the node is standalone; non-``NULL`` means it is owned and cannot exist on its own.
* Every owned child has exactly one row in the membership table recording its immediate owner, its position, and — for ``DataDict`` — its key.
  Both membership endpoints point at ``db_dbnode.id``.
  The child's ``owner_id`` matches the membership's ``owner_id`` for owned children and remains ``NULL`` for references.

.. code-block:: text

    db_dbnode  (base table: id, owner_id, and every other node column)
    ┌────────┬──────────┬─────────┐
    │ id (PK)│ owner_id │ …       │
    ├────────┼──────────┤         │
    │ 1 list │ NULL     │         │
    │ 2 int  │ 1        │         │
    │ 3 int  │ 1        │         │
    └────────┴──────────┴─────────┘
                        owner_id ──▶ id (NULL = standalone)

         │
    db_dbmembership
    ┌──────────┬──────────┬──────────┬──────┐
    │ owner_id │ child_id │ position │ key  │  owner_id ──▶ db_dbnode.id
    ├──────────┼──────────┼──────────┼──────┤  child_id ──▶ db_dbnode.id
    │ 1        │ 2        │ 0        │ NULL │
    │ 1        │ 3        │ 1        │ NULL │
    └──────────┴──────────┴──────────┴──────┘

The node's ``node_type`` identifies a list or dict, even when the container is empty and has no membership rows.
Typed reads check ``node_type`` to reject cross-kind access.

Membership rows are containment edges, not provenance.
Duplicating them as ``CREATE`` or ``INPUT`` links would claim a computation happened that never did, so containment stays in its own tables and provenance links never point at owned children directly.

Three consequences fall out of this shape.
First, ownership is exclusive and acyclic: ``child_id`` is unique, so a node can only ever have one owner, and the backend refuses self-ownership plus any edge that would close a cycle through already-stored rows.
Second, the foreign keys only require both endpoints to exist; AiiDA's storage layer checks that the owner is a reserved container type and that the child is leaf data or a nested container, not a process node.
Third, the finer rules (list keys are always ``NULL``, dict keys are never ``NULL`` and never coerced, positions are explicit integers with no overlap against stored rows) are enforced in Python by the shared ``aiida.storage.ownership`` module rather than in DDL, with no database triggers.
Every write path — single inserts, bulk operations, provenance links, deletion, archive import — goes through those validators, so the ORM convenience methods are never the enforcement boundary.
Uniqueness constraints make concurrent double-ownership attempts fail, but cycle checks read live state and are best-effort under concurrent writes; callers needing strict serialisation must also coordinate concurrent writers, for example with a shared locking protocol.
On SQLite, foreign-key enforcement depends on the connection ``PRAGMA foreign_keys`` setting, so the Python validation is the authoritative boundary on both backends.


Membership and ownership
========================

Inserting a node into a draft container retains its identity without claiming ownership.
At store time, the ORM rejects cycles, repeated identities in the proposed tree, and already-owned nodes before writing the subtree.
Use ``clone()`` explicitly to create an independent node or subtree.
There is no persistent record of which source a clone came from.

Process boundaries still enforce separate provenance rules.
Handing an owned child to a process detaches a standalone copy first, and the process executes with the copy it records as its provenance input.
Exposing an owned child as a calculation output copies it and attaches ``CREATE`` to the copy.
Workflows never copy on output: they may return a whole standalone container, but returning an owned child is rejected, since silently duplicating data out of a workflow would hide where nodes came from.

Members may have different concrete types; each member's ``node_type`` lives on its own node row.
The ownership step in ``main_0003`` leaves existing nodes and provenance links intact.
Downgrading from ``main_0003`` is not supported, even if no containers are stored, because the revision also makes irreversible data changes.


Mutable until stored
====================

Before storage, a container behaves like an ordinary Python collection: append, insert, replace, remove, reorder, clear.
Removing an element from a draft drops the membership without changing the node.

Storing the root freezes the entire subtree at once, and the freeze is all-or-nothing.
Before any repository or database write, the ORM validates the proposed memberships and checks each node to be stored once.
The ORM then writes every repository file first (repo-first), then hands narrow storage specs — backend entities plus explicit position/key metadata, no ORM objects — to ``backend.store_container_subtree``.
That call writes all node rows in post-order (children before owner, root last), then all membership edges with the container's layout, in a single backend transaction that joins any enclosing transaction.
Leaf rows go through ``BackendNode.store``; container rows go through ``BackendContainer.store_container``.
Calling the ordinary ``store`` method on a backend container raises ``IntegrityError``.
Only the ownership root receives the incoming provenance links.
If anything fails, no partially stored ownership graph is left behind: the retained Python objects are restored from snapshots to unstored, editable, retryable state, with their content and ordering intact.
When the store joined an enclosing transaction, recovery is eager: the store registers a backend rollback hook that restores the retained subtree at rollback time, safe to observe from a retained leaf child first and correct across nested savepoints, since only the failed scope fires while outer scopes keep theirs.
Backends without hook support keep the lazy fallback: the root re-verifies its row on the next status check outside an active transaction and recovers the subtree the same way.
Database rollback cannot undo repository writes, so orphaned files are left for normal storage maintenance rather than chased synchronously — the recovered objects are reseeded from snapshots and never depend on cleanup having run.

Once stored, the subtree is immutable except for the ordinary node mutability exceptions such as extras.
Stored ownership and membership cannot be changed in place.


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
    └── _ownership_models          (DbNode, DbMembership) model pair

    DbNode / DbMembership models (+ main_0003 migration)
    ├── DbNode.node_type          identifies list and dict containers
    ├── DbNode.owner_id           nullable reference to db_dbnode.id, indexed
    └── DbMembership             containment edges with position / key


Deletion and group membership
=============================

Deletion follows owned members downward by default, in addition to ordinary provenance traversal.
The ``verdi`` path previews surviving containers that lose members, then the backend revalidates the plan without enlarging it.
With ``--no-contains-forward``, deletion clears the owner reference of each surviving owned member of a deleted container and removes the corresponding edge in the same transaction.
It does not renumber the remaining membership positions.
Deleting a member edits any surviving container that contains it and invalidates the container's content hash and its ancestors' hashes.
The guarded single-row storage primitive ``nodes.delete(pk)`` still requires callers to use a graph deletion plan for these cases.

Group add and remove operations act on the supplied nodes exactly, without following containment or provenance links.
The rows are independent of ownership.


Queries and archives
====================

QueryBuilder support is intentionally initial: joins from a container to its immediate children (``with_members``) and back (``with_owner``), with the membership edge exposed for ``position``/``key`` edge filters and projections.
On PostgreSQL, equality lookups by membership ``child_id`` can use a hash index; the unique B-tree enforces one membership per child, including references.
SQLite uses the existing B-tree indexes.
Container classes are also queryable by concrete type through the shared node identity, so a ``DataList`` query never returns a ``DataDict``.
There is no recursive traversal and no container-specific aggregation yet; each join on a child matches that child, and separate joins may match different children.
``with_incoming``/``with_outgoing`` additionally traverse immediate membership at query time, without persisting anything.

SQLite archives store a membership edge only when both endpoints are exported.
Export clears projected owner references without changing UUIDs or source rows.
Import translates archive-local IDs and merges explicit edges in the same transaction as the nodes.
UUID reuse leaves existing edges that are absent from the archive alone and rejects conflicting owners, container kinds, positions, keys, and provenance links.


Container caching
=================

Container hashes include the storage layout and each child's content hash recursively, with list order significant and dict order ignored.
A cleared container hashes like a newly constructed empty container with the same metadata.
Owner IDs and child UUIDs are excluded, so equivalent independent copies hash equally.
A process with container inputs bypasses cache lookup, and a process with container inputs or outputs cannot serve as a cache source.
Deletion and archive merges can change membership after a process has run, and order-sensitive calculations can distinguish dictionaries with the same content hash.


.. _internal_architecture:storage:containers:limitations:

Known limitations
=================

- QueryBuilder has no recursive membership traversal or container-specific aggregation.
  ``Data`` queries match containers and other data nodes, and ``Container`` queries match only ``DataList`` and ``DataDict``.
- Process cache reuse is disabled for runs with container inputs or outputs.
- Slicing a ``DataList`` raises ``TypeError``; there is no view or copy semantics for slices.
- Port validation for containers is class-only (``valid_type`` accepts ``Data``); element types are not checked by the port.
