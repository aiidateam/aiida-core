.. _internal_architecture:storage:psql_dos:

``psql_dos`` format
*******************

The :py:class:`~aiida.storage.psql_dos.backend.PsqlDosBackend` is the primary format for storing provenance data.
It stores data in two places:

1. A `PostgreSQL <https://www.postgresql.org/>`_ database.
2. A disk-objectstore repository (see :ref:`internal-architecture:repository:dostore`).

The database stores all "JSONable" entity data, organized into different tables (closely related to AiiDA ORM entities) and columns/fields.
Larger binary data (such as input/output file content), required for nodes, are stored in the disk-objectstore, and referenced by `db_dbnode.repository_metadata` as a virtual file-system.

Interfacing with the database is achieved using the `sqlalchemy <https://www.sqlalchemy.org/>`_ ORM API.


The PostgreSQL database schema
==============================

The following section provides a complete schema for the PostgreSQL database.

Tables
------

In all tables, the primary key that uniquely identifies each of their members is a positive integer number in the ``id`` field.
However, this number is only unique within the table, and thus there can be a user with an ``id`` of 2 and a node with an ``id`` of 2 in the same database (or, more trivially, two different nodes both with an ``id`` of 2, each in a different database).

Most of the entities also have a ``uuid`` value.
The ``uuid`` is meant to serve as an identifier that is unique within all tables of all AiiDA databases in the world.
This is a 32-position hexadecimal sequence that is stored as a string with some dash separated sections (for example: ``479a312d-e9b6-4bbb-93b4-f0a7174ccbf4``).

.. note::

  - ``*`` indicates columns with a unique constraint
  - ``→`` indicate foreign keys
  - ``?`` indicate value types that are nullable.

.. sqla-model:: ~aiida.storage.psql_dos.models.user.DbUser

.. sqla-model:: ~aiida.storage.psql_dos.models.node.DbNode

.. sqla-model:: ~aiida.storage.psql_dos.models.node.DbLink

.. sqla-model:: ~aiida.storage.psql_dos.models.group.DbGroup

.. sqla-model:: ~aiida.storage.psql_dos.models.group.DbGroupNode

.. sqla-model:: ~aiida.storage.psql_dos.models.computer.DbComputer

.. sqla-model:: ~aiida.storage.psql_dos.models.authinfo.DbAuthInfo

.. sqla-model:: ~aiida.storage.psql_dos.models.comment.DbComment

.. sqla-model:: ~aiida.storage.psql_dos.models.log.DbLog

.. sqla-model:: ~aiida.storage.psql_dos.models.settings.DbSetting


The many-to-one relationship
----------------------------

You can see an example of a many-to-one relationship between users and nodes: each node will have one and only one user that has created it, while a single user may have created many nodes.
Although in that case the relationship is "mandatory", this doesn't need to be the case: for example, not all nodes will have a computer associated with them, but the ones that do will have only one and no more.

The following entities have a many-to-one relationship:

* Many `nodes` can be created by the same `user`.
* Many `nodes` can point to the same `computer`.
* Many `groups` can be created by the same `user`.
* Many `authinfos` can be set for the same `user`.
* Many `authinfos` can be set for the same `computer`.
* Many `comments` can be created by the same `user`.
* Many `comments` can be attached to the same `node`.
* Many `logs` can be attached to the same `node`.

The way to keep track of these relationships is by inserting a `foreign key` column in the table of the "many" entity that points to the corresponding id value of the "one" entity they are related to.
For example, there is a ``user_id`` foreign key column in the **db_dbnode** table that stores the id of the user that created each node.


The many-to-many relationship
-----------------------------

This type of relationship is a bit more difficult to track, since now both members can be related to more than one element.
Recording this in the same table as one of the entities would imply storing a list of values in a column (which is often discouraged and not well supported).
Therefore, it is more convenient to use an extra table in which each of the connections has its corresponding entry indicating which are the specific elements that are related.

There are only two many-to-many relationships in AiiDA:

Between groups and nodes
   as specified before, many nodes can be inside the same group and a single node can belong to many different groups.
   This relationship is tracked in the **db_dbgroup_dbnodes** table.

Between nodes themselves (Links)
   nodes have what is known as a "self-referencing relationship", meaning that they can be connected among themselves.
   Indeed, this is one of the core principles of how the provenance graph works.
   This relationship is tracked in the **db_dblinks** table.

Storage schema migrations
=========================

Migrations of the storage schema, to bring it inline with updates to the ``aiida-core`` API, are implemented by :py:class:`~aiida.storage.psql_dos.migrator.PsqlDosMigrator` , using `alembic <https://alembic.sqlalchemy.org>`_.

Legacy schema
-------------

The `psql_dos` storage format originates from the merging of the `django` and `sqlalchemy` backends, present in `aiida-core` version 1.
Both backends had very similar PostgreSQL database schema, and there are now two separate migration branches to merge these into a single schema.
