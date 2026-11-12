.. _internal_architecture:storage:containers:

**********************
Owned data containers
**********************

Most data in AiiDA is a single node: an ``Int``, a ``StructureData``, a file.
Sometimes a calculation needs an ordered collection of nodes — the frames of a trajectory, the structures of a screening study — and the collection itself has to be a node so it can be passed around, stored, and linked into the provenance graph.

That is what the owned data containers are for.
``DataList`` holds an ordered list of data nodes, ``DataDict`` maps string keys to data nodes, and both are themselves ``Data`` nodes.
Elements can be any data type, including nested containers, but every element of one container must have the same concrete node type.

This page documents the internal architecture for developers working on the containers themselves.
It is under active development: the relational storage described here is implemented, while several integrations listed under :ref:`known limitations <internal_architecture:storage:containers:limitations>` still reject container input instead of handling it.


Ownership, not links
=====================

A container owns its elements.
Ownership is recorded in two places, and deliberately in neither the node attributes nor the provenance link table:

* Every node row has a nullable ``owner_id`` foreign key pointing at another node row.
  ``NULL`` means the node is standalone; non-``NULL`` means it is owned and cannot exist on its own.
* Every owned child has exactly one row in the membership table recording its immediate owner, its position, and — for ``DataDict`` — its key.

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
    db_dbcontainer  (subtype row: no node columns of its own)
    ┌─────────┬──────────────┐ │
    │ node_id │ element_type │─┘  node_id ──▶ id (the container IS node 1;
    ├─────────┼──────────────┤    base columns come from the join)
    │ 1       │ data.Int...  │
    └─────────┴──────────────┘
         ▲
         │  owner_id ──▶ node_id (the container row, not the node row)
         │
    db_dbmembership
    ┌──────────┬──────────┬──────────┬──────┐
    │ owner_id │ child_id │ position │ key  │
    ├──────────┼──────────┼──────────┼──────┤  child_id ──▶ db_dbnode.id
    │ 1        │ 2        │ 0        │ NULL │  row 1: 2 ──▶ node 2
    │ 1        │ 3        │ 1        │ NULL │  row 2: 3 ──▶ node 3
    └──────────┴──────────┴──────────┴──────┘
                    
                      
                      

    The kind markers (``db_dblistcontainer`` / ``db_dbdictcontainer``) are single-column ``node_id`` rows pointing at ``db_dbcontainer.node_id``, read through a join so cross-kind access fails instead of returning an ambiguously-interpreted row; they are omitted from the sketch.

Membership rows are containment edges, not provenance.
Duplicating them as ``CREATE`` or ``INPUT`` links would claim a computation happened that never did, so containment stays in its own tables and provenance links never point at owned children directly.

Three consequences fall out of this shape.
First, ownership is exclusive and acyclic by construction: the ``child_id`` column is unique, so a node can only ever have one owner, and the backend refuses any edge that would close a cycle.
Second, only containers can own, and only data nodes can be owned — process nodes are rejected, which is what keeps the provenance graph honest.
Third, the database cannot see node types through the subtype rows, so the finer rules (list keys are always ``NULL``, dict keys never are, positions have no gaps for a given owner) are enforced in Python by the shared ``ownership`` module rather than in DDL.
Every write path — single inserts, bulk operations, provenance links, deletion, archive import — goes through those validators, so the ORM convenience methods are never the enforcement boundary.


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
The store path validates the whole subtree, writes every repository file first, and then persists all node rows, owner references, membership rows, and type metadata in a single database transaction that joins any enclosing transaction.
If anything fails, no partially stored ownership graph is left behind: the retained Python objects are restored to unstored, editable, retryable state, with their content, ordering, and type locks intact.
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

    src/aiida/storage/ownership.py
    ├── validate_ownership_graph  pre-write checks shared by every backend
    ├── attach_membership         the only writer of owner references and membership rows
    └── expand_ownership_closure  root-plus-subtree traversal for deletion and groups

    src/aiida/storage/{psql_dos,sqlite_*}/models, backend.py, migrations
    ├── DbNode.owner_id           nullable self-FK, deferred, indexed
    ├── DbContainer               one row per container: element_type + layout
    ├── DbListContainer /          kind markers; reads join the asserted kind, so a
    │   DbDictContainer            list read through the dict accessor fails loudly
    └── DbMembership               containment edges with position / key
    └── main_0003                 migration introducing all of the above


Deletion and groups follow the unit
===================================

Deleting a container deletes its whole subtree, subject to the ordinary provenance safeguards — owned children cannot be deleted on their own.
A deletion request aimed at an owned child is expanded to its ownership root plus the full subtree before the usual confirmation, and programmatic callers must explicitly approve the expansion; the backend revalidates the approved set without enlarging it.

Groups work the same way: a group contains a complete ownership unit or none of it.
Membership rows are stored explicitly for the root and every descendant, so group iteration and queries need no special traversal.
Adding or removing through the Python API with an owned child is rejected with a pointer at the root; the CLI shows the expansion and asks for confirmation.


Queries and archives
====================

QueryBuilder support is intentionally initial: joins from a container to its immediate children and back, filters on membership position and key, and filters on the persisted element type.
There is no recursive traversal and no container-specific aggregation yet; each join on a child matches that child, and separate joins may match different children.

Archives have no representation for ownership yet, so both directions refuse rather than silently drop it.
Exporting a selection that touches any owned node fails validation, and importing an archive that carries owner references or container tables fails before anything is written.
UUID deduplication on import reuses a node only when both sides agree it is standalone; any disagreement under one UUID is an integrity error, never a silent detach.


Container caching
=================

Container hashes are content-based: the element type and layout plus each child's hash, recursively, with list order significant and dict order ignored.
Owner IDs and child UUIDs are excluded, so equivalent independent copies hash equally.
Cache reuse is disabled for now — restoring a cached run must rebuild an independent ownership subtree, and that wiring is still open — while hashing itself works.


.. _internal_architecture:storage:containers:limitations:

Known limitations
=================

- Archives cannot carry ownership yet: the archive format has no fields for owner references or membership edges, so containers are blocked from travelling through ``.aiida`` files by design until the format supports them. Exporting any selection that touches an owned node fails validation, and importing an archive that carries ownership data is rejected before anything is written — instead of silently freeing owned children into standalone nodes.
- QueryBuilder has no recursive membership traversal and no any/all, count, or empty-container predicates.
- Cached processes whose outputs include containers are not reused yet.
- Graphs reject container-typed ports in several positions; running tasks over collection items in parallel is the motivating use case and is in development.
- Slicing, if added, will produce an independent copied container, never a view.
- Port validation for containers is class-only; parameterized generics do not imply runtime checks.
- A ``while`` loop over a container cannot return one result per iteration; copy the values into one list node instead.
