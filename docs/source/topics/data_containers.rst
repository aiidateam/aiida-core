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

Containers derive from :py:class:`~aiida.orm.Container`, not :py:class:`~aiida.orm.Data`.
Both derive from the shared :py:class:`~aiida.orm.DataNode` base.
To accept both in a type check or process port, use ``DataNode``.
Querying ``DataNode`` matches data and containers, querying ``Data`` excludes containers, and querying ``Container`` matches ``DataList`` and ``DataDict``.

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
Dict keys must be strings and are never coerced: ``mapping[1]`` raises ``TypeError``.
Dicts keep insertion order: replacing a value keeps its position, while deleting a key and re-adding it moves the key to the end.
Slicing a ``DataList`` raises ``TypeError``; copy the elements you need into a new container instead.

.. _topics:data_containers:homogeneity:

All elements share one concrete type
====================================

Every element of one container must have the exact same concrete node type, compared as the stored type string.
The first insertion locks the type, and the lock survives removing every element:

.. code-block:: ipython

    In [1]: numbers = DataList([Int(1)])

    In [2]: numbers.append(Str('nope'))
    TypeError: container element type is locked to data.core.int.Int., cannot insert node of type data.core.str.Str.

    In [3]: numbers.clear()

    In [4]: numbers.append(Str('still locked'))
    TypeError: container element type is locked to data.core.int.Int., cannot insert node of type data.core.str.Str.

A container that never held an element has no locked type (``element_type`` is ``None``) and can still be stored.
Containers can be nested: a list may hold dicts whose value types differ from each other, because each nested container enforces its own lock and only the outer concrete type is compared.

.. _topics:data_containers:copy:

Insertion copies, never adopts
==============================

Inserting a node into a container clones it, and the container owns the copy.
The source keeps its identity and stays usable; inserting the same source twice produces two independent copies; inserting a copy copies it again.
There is no record of where a copy came from, so a copy that outlives its source is indistinguishable from any other node.
Process nodes cannot be inserted: only data nodes and nested containers are eligible.

Removing an element detaches just that element as a standalone, unstored, editable node.
For a removed nested container, only the nested root is detached; its own descendants stay owned by it.
Re-inserting a detached node copies it again.

.. _topics:data_containers:storing:

Storing freezes the whole subtree
=================================

Only the ownership root can be stored.
Storing a ``DataList`` validates the complete subtree first — an invalid element fails the store before anything is written — then writes every repository file, then persists all node rows, ownership references, and membership rows in a single database transaction.
If a repository write or the database transaction fails, the database changes are rolled back and the retained objects are restored for retry.
Repository objects already written may remain unreferenced until storage maintenance removes them.

.. code-block:: ipython

    In [1]: numbers = DataList([Int(1), Int(2)])

    In [2]: _ = numbers.store()

    In [3]: numbers.append(Int(3))
    ModificationNotAllowed: DataList with pk 1 is stored and its membership is immutable

Once stored, membership cannot change.
Owned children cannot be stored on their own: storing ``numbers[0]`` raises ``ModificationNotAllowed``.
Stored children behave like any stored node and can be reloaded with :py:func:`~aiida.orm.load_node`:

.. code-block:: ipython

    In [4]: from aiida.orm import load_node

    In [5]: reloaded = load_node(numbers.pk)

    In [6]: [node.value for node in reloaded]
    Out[6]: [1, 2]

Reloading preserves order for lists and insertion order for dicts, along with the locked element type.
Extras stay mutable after storage; everything else about the subtree is frozen.

.. _topics:data_containers:processes:

Using containers in processes
=============================

Processes link whole containers, never owned children directly.
Passing a whole container as an input links that container; passing an owned child detaches a standalone copy first, and the process records that same copy as its provenance input.

.. code-block:: python

    from aiida.engine import calcfunction

    @calcfunction
    def first(container):
        return container[0]

The ``return container[0]`` here exposes an owned child as a calculation output.
The engine records a standalone copy as the output, with a ``CREATE`` link from the calculation, and the caller receives that recorded copy.
Workflows never copy on output: a workfunction may return a whole standalone container, but returning an owned child raises ``InvalidOperation`` instead of silently duplicating data.
Return the container itself in that case.
Port validation accepts containers alongside data (``valid_type`` accepts ``DataNode``) but does not check element types; validate those inside the process if they matter.

.. _topics:data_containers:querying:

Querying container contents
===========================

:py:class:`~aiida.orm.QueryBuilder` joins containers to their immediate children with ``with_members``, and children back to their owner with ``with_owner``:

.. code-block:: python

    from aiida.orm import DataList, Int, QueryBuilder

    builder = (
        QueryBuilder()
        .append(DataList, filters={'id': numbers.pk}, tag='owner')
        .append(Int, with_members='owner', edge_filters={'position': 0}, project='id')
    )

Membership ``position`` (lists) and ``key`` (dicts) are available as edge filters.
Each join matches one child; separate joins may match different children.
There is no recursive traversal: reaching grandchildren takes one join per level.

.. _topics:data_containers:groups:

Groups and deletion cover the whole unit
========================================

A group contains a complete ownership unit or none of it: adding a container root adds the root and every descendant as explicit rows, so ordinary group iteration and queries include all nodes.
Adding or removing an owned child directly is rejected; pass the ownership root instead.
The ``verdi group`` commands show the whole-unit expansion and ask for confirmation before applying it.
Deletion works the same way: deleting a container requires deleting the root plus the complete subtree, and requests that target only part of a unit are rejected with a pointer at the root.

.. _topics:data_containers:limitations:

Limitations
===========

- Archives cannot carry ownership yet: exporting any selection that touches an owned node (including an empty container) raises ``ExportValidationError``, and importing an archive that carries ownership data is rejected before anything is written.
  To export an individual element, clone it and store the standalone copy first.
- Container cache reuse is disabled.
- The container set is closed: ``DataList`` and ``DataDict`` cannot be subclassed and no custom container types are supported.
  List order affects the hash; dict insertion order does not.
- Slicing a ``DataList`` raises ``TypeError``.
- Querying is limited to immediate membership joins as described above; there is no recursive traversal and no container-specific aggregation.
