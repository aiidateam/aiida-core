.. _topics:data_containers:

**********************
Owned data containers
**********************

:py:class:`~aiida.orm.DataList` and :py:class:`~aiida.orm.DataDict` hold data *nodes*, where :py:class:`~aiida.orm.List` and :py:class:`~aiida.orm.Dict` hold plain values.
Use a container when each element needs its own identity in the provenance graph: the frames of a trajectory, the structures of a screening study, the files behind a multi-step result.
The container itself is a node, so it can be stored, passed to processes, and linked like any other node.

Both classes are imported directly from :py:mod:`aiida.orm`:

.. code-block:: python

    from aiida.orm import DataDict, DataList, Int, Str

They are registered as ``core.data_list`` and ``core.data_dict`` in the ``aiida.container`` entry point group, so plugin-style loading goes through :py:func:`~aiida.plugins.factories.ContainerFactory` instead of :py:func:`~aiida.plugins.factories.DataFactory`:

.. code-block:: python

    from aiida.plugins import ContainerFactory

    DataList = ContainerFactory('core.data_list')

Containers derive from :py:class:`~aiida.orm.Container`, a subclass of :py:class:`~aiida.orm.Data`.
Use ``Data`` for type checks, ports, and queries that accept both containers and other data nodes.
Querying ``Container`` matches only ``DataList`` and ``DataDict``.

.. _topics:data_containers:editing:

Creating and editing containers
===============================

A ``DataList`` behaves like a mutable sequence of nodes, a ``DataDict`` like a mutable mapping from strings to nodes:

.. code-block:: ipython

    In [1]: fruits = DataList([Str('apple'), Str('pear')])

    In [2]: fruits.append(Str('kiwi'))

    In [3]: [node.value for node in fruits]
    Out[3]: ['apple', 'pear', 'kiwi']

    In [4]: mapping = DataDict({'a': Int(1), 'b': Int(2)})

    In [5]: mapping['a'].value
    Out[5]: 1

Lists support indexing (including negative indices), ``append``, ``insert``, ``pop``, ``move``, and ``clear``.
Dicts support lookup, assignment, ``del``, ``pop``, ``clear``, ``get``, ``keys``, ``values``, and ``items``.
``DataDict`` requires string keys so SQLite cannot silently store a key supplied as the integer ``1`` as the string ``'1'``.
Using a non-string key raises ``TypeError``.
Keys are literal strings, not process port names, so ``sample-name`` and ``sample__name`` are both valid.
Storing a container with a key longer than 255 characters or containing a NUL character fails on both backends.
SQLite storage checks these limits for portability, while PostgreSQL reports its own error.
Existing stored keys remain readable.
Dicts keep insertion order: replacing a value keeps its position, while deleting a key and re-adding it moves the key to the end.
Slicing a ``DataList`` raises ``TypeError``; copy the elements you need into a new container instead.

.. _topics:data_containers:homogeneity:
.. _topics:data_containers:member_types:

Member types
============

Members may have different concrete types, including nested containers.
For example, a dictionary can contain a label, a scalar, and a nested list:

.. code-block:: python

    from aiida.orm import DataDict, DataList, Float, Int, Str

    result = DataDict({'label': Str('sample'), 'energy': Float(-1.2), 'counts': DataList([Int(2), Int(3)])})

An empty container can also be stored.
Clearing an unstored container puts no type constraints on its next insertion.

.. _topics:data_containers:copy:

Copies and references
=====================

Insertion retains the exact node supplied; it neither clones it nor claims ownership.
Removing a draft member returns the same node unchanged.
Process nodes cannot be inserted: only data nodes and nested containers are eligible.

Storing a container claims ownership of its unstored members.
If a node appears in more than one membership in the proposed tree or is already owned, ``store()`` raises ``IntegrityError`` without storing any part of the tree.
Use ``node.clone()`` explicitly when you want a separate node with the same content.

A ``DataList`` can reference stored standalone leaf data on the same backend without taking ownership, so ``numbers.append(result)`` keeps the UUID and provenance links of an existing calculation result.
A stored container, or any stored value supplied to a ``DataDict``, must be explicitly cloned before it can be stored as a member.
A node can be referenced by only one stored list at a time.
Use ``numbers.append(result.clone())`` to insert an independent owned copy instead.
Deleting the list leaves the result intact; deleting the result while the list still references it is rejected.

.. _topics:data_containers:storing:

Storing freezes the whole subtree
=================================

Storing a container validates the complete draft tree first, then writes repository files and persists the node rows, ownership references, and membership rows in a single database transaction.
A draft member can be stored independently, but a later store of its container must then satisfy the rules for already-stored members.
If a repository write or the database transaction fails, the database changes are rolled back and the retained objects are restored for retry.
Repository objects already written may remain unreferenced until storage maintenance removes them.

.. code-block:: ipython

    In [1]: numbers = DataList([Int(1), Int(2)])

    In [2]: _ = numbers.store()

    In [3]: numbers.append(Int(3))
    ModificationNotAllowed: DataList with pk 1 is stored and its membership is immutable

Once stored, membership cannot change.
Owned children are already stored as part of the subtree and can be reloaded with :py:func:`~aiida.orm.load_node`:

.. code-block:: ipython

    In [4]: from aiida.orm import load_node

    In [5]: reloaded = load_node(numbers.pk)

    In [6]: [node.value for node in reloaded]
    Out[6]: [1, 2]

Reloading preserves each member's concrete type, as well as list order and dictionary insertion order.
Extras stay mutable after storage; everything else about the subtree is frozen.

.. _topics:data_containers:processes:

Using containers in processes
=============================

Process ports link whole containers, not their owned children.
Passing a whole container as an input links the root to the declared port.
For calculations, nested containers, owned members, and referenced nodes also get ``INPUT_CALC`` links as dependencies, but do not appear as extra ports in ``node.inputs``.
Passing an owned child separately detaches a standalone copy first, and the process records that same copy as its provenance input.
Like any other recorded input, the detached copy cannot be returned unchanged by a calculation; use ``value.clone()`` to create a new output.

.. code-block:: python

    from aiida.engine import calcfunction

    @calcfunction
    def first(container):
        return container[0]

The ``return container[0]`` here exposes an owned child as a calculation output.
The engine records a standalone copy as the output, with a ``CREATE`` link from the calculation, and the caller receives that recorded copy.
When a calculation outputs a new container, each newly owned descendant also gets a direct ``CREATE`` link, but only the root appears as a process output port.
A calculation cannot return a stored container or a new container that references stored nodes.
Use ``clone()`` to make an independent output.

Workflows never copy on output: a workfunction may return a stored standalone container, but returning an owned child raises ``InvalidOperation`` instead of silently duplicating data.
Return the container itself in that case.
Port validation accepts containers alongside data (``valid_type`` accepts ``Data``) but does not check element types; validate those inside the process if they matter.

.. _topics:data_containers:querying:

Querying container contents
===========================

:py:class:`~aiida.orm.QueryBuilder` joins containers to their immediate children with ``with_members``, and children back to their owner with ``with_owner``:

.. code-block:: python

    from aiida.orm import DataList, Int, QueryBuilder, Str

    numbers = DataList([Int(2), Str('three')]).store()
    builder = (
        QueryBuilder()
        .append(DataList, filters={'id': numbers.pk}, tag='owner')
        .append(Int, with_members='owner', edge_filters={'position': 0}, project='id')
    )

Membership ``position`` (lists) and ``key`` (dicts) are available as edge filters.
The child class filters the join independently of any sibling types.
Each join matches one child; separate joins may match different children.
QueryBuilder does not follow these joins recursively, reaching grandchildren takes one join per level.

Following ownership in graph walks
==================================

:py:func:`~aiida.tools.graph.graph_traversers.traverse_graph` follows membership only when you pass ``LinkType.CONTAINS`` in ``links_forward`` or ``links_backward``.
Forward follows container to member, and backward follows member to owner.
For example, given a ``summary`` dict returned by a calculation, traverse from its ``'total'`` member to both its owner and its creator:

.. code-block:: python

    from aiida.common.links import LinkType
    from aiida.tools.graph.graph_traversers import traverse_graph

    walk = traverse_graph(
        [summary['total'].pk],
        links_backward=(LinkType.CONTAINS, LinkType.CREATE),
        get_links=True,
    )

The result contains actual provenance links in ``links`` and ownership edges in ``memberships``.
A ``CONTAINS`` edge is stored as a membership row, not a provenance link.
The ``creator`` property reads a node's direct incoming ``CREATE`` link; membership alone does not establish creation.
This identifies the calculation that created a member, but it does not recover the source of an explicitly cloned node.
You can also pass ``LinkType.CONTAINS`` in the ``link_types`` argument of :py:class:`~aiida.tools.visualization.Graph` to draw membership edges separately.

.. _topics:data_containers:groups:

Group membership
================

Adding or removing nodes in a group acts only on the nodes you pass, without following membership edges.
Group membership does not change container ownership.

.. code-block:: python

    group.add_nodes(container)                 # Add only the container.
    group.add_nodes([container, *container])   # Add the container and its direct members.

Deletion
========

By default, deletion follows ownership downwards, in addition to the ordinary provenance traversal rules.
Membership alone does not select a member's owner or siblings for deletion.
For calculation inputs and outputs, ordinary provenance rules can select calculations that consumed or created the member, and their outputs.
Use ``--no-contains-forward`` to stop following membership during deletion; members not selected by other rules survive as standalone nodes with the same UUIDs.
Nested members retain their own children, and referenced nodes are not selected for deletion merely because their container is deleted.
Preview the deletion, which reports detachment and changes to surviving containers, before confirming:

.. code-block:: console

    $ verdi node delete --dry-run --no-contains-forward 123

Archives
========

Archive selection follows ``CONTAINS`` backward to include ancestor containers, in addition to ordinary provenance traversal.
Use ``--contains-forward`` (Python: ``contains_forward=True``) to also include members recursively.
The archive contains a membership edge only if both endpoints are exported.

.. code-block:: python

    from aiida.tools.archive import create_archive

    create_archive([container[0]], filename='member-and-ancestors.aiida')
    create_archive([container], filename='with-members.aiida', contains_forward=True)

Import merges explicit membership by UUID and never removes existing edges just because they are absent from the archive.
For example, an empty archived container can merge into a populated container without removing its members.
A later import can supply missing edges if they do not conflict with stored ownership, positions, keys, or provenance links.

.. _topics:data_containers:limitations:

Limitations
===========

- Processes with container inputs skip cache lookup, and processes with container inputs or outputs are not cache sources.
  Containers still have content hashes: list order affects the hash; dict insertion order does not.
- The container set is closed: ``DataList`` and ``DataDict`` cannot be subclassed and no custom container types are supported.
- Slicing a ``DataList`` raises ``TypeError``.
- Querying is limited to immediate membership joins as described above; there is no recursive traversal and no container-specific aggregation.
