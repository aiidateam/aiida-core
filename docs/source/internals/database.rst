.. _internal_architecture:database:

******************
Database structure
******************

The database is the main tool that AiiDA uses to keep track of the provenance.
It directly stores the most critical data and contains the access information for everything that gets stored in the repository.
Its content is organized into different tables, and although the exact structure will depend on the backend used (django or sqlalchemy), most of it is the same for both possibilities.

In the following section, we will first go through the main tables that are related to the AiiDA entities and their relationships.
These tables also have the property of being the same for both backends.
We will give a general overview and explanation of how they work, and provide a more exhaustive technical description of their internal structure.
After that, we will introduce the remaining tables that either serve a more auxiliary purpose or are backend specific.


The AiiDA entities and their tables
===================================

There are 7 entities that are stored in the database, each within its own table:

 - **db_dbnode:** the `nodes` are the most important entities of AiiDA.
   The very provenance graph is made up of interconected data and process nodes.

 - **db_dbgroup:** `groups` are containers for organizing nodes.
   A group may contain many different nodes, but also each node can be included in different groups.

 - **db_dbuser:** `users` represent (and contain the information of) the real life individuals working with the program.
   Every node that is created has a single user as its author.

 - **db_dbcomputer:** `computers` represent (and contain the information of) the physical hardware resources available.
   Nodes can be associated with computers if they are remote codes, remote folders, or processes that had run remotely.

 - **db_dbauthinfo:** `authinfos` contain the specific user configurations for accessing a given computer.

 - **db_dbcomment:** `comments` can be attach to the nodes by the users.

 - **db_dblog:** `logs` may be attached to nodes by AiiDA to provide further information of relevant events that transpired during its creation (for example, warning an errors during the execution of processes).


In all of the tables in the database (not just the ones mentioned above), the primary key that uniquely identifies each of their members is a positive integer number called ``id`` (sometimes also ``pk``).
However, this number is only unique within the table, and thus there can be a user with an ``id`` of 2 and a node with an ``id`` of 2 in the same database (or, more trivially, two different nodes both with an ``id`` of 2, each in a different database).

What most of the entities also have (all the aforementioned except for users and authinfos) is a ``uuid`` value.
The ``uuid`` is meant to serve as an identifier that is unique within all tables of all AiiDA databases in the world.
This is a 32-position hexadecimal sequence that is stored as a string with some dash separated sections (for example: ``479a312d-e9b6-4bbb-93b4-f0a7174ccbf4``).

When going over the descriptions for the entities before, you may have noticed that all of them have some kind of "interaction" or "relationship" with at least one other entity in some way.
Some of these relationships can be tracked inside of one of the related entity's tables, whilst others require the creation of a whole new table with the only purpose of keeping track of them.


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

 - **Between groups and nodes:**
   as specified before, many nodes can be inside the same group and a single node can belong to many different groups.
   This relationship is tracked in the **db_dbgroup_dbnodes** table.

 - **Between nodes themselves (Links):**
   nodes have what is known as a "self-referencing relationship", meaning that they can be connected among themselves.
   Indeed, this is one of the core principles of how the provenance graph works.
   This relationship is tracked in the **db_dblinks** table.


Table schema
============

The following section provides a complete schema for each of the tables of the SQLAlchemy backend.

``*`` indicates columns with a unique constraint, ``→`` indicate foreign keys, and ``?`` indicate value types that are nullable.

.. sqla-model:: ~aiida.backends.sqlalchemy.models.node.DbNode

.. sqla-model:: ~aiida.backends.sqlalchemy.models.node.DbLink

.. sqla-model:: ~aiida.backends.sqlalchemy.models.group.DbGroup

.. sqla-model:: ~aiida.backends.sqlalchemy.models.group.DbGroupNode

.. sqla-model:: ~aiida.backends.sqlalchemy.models.user.DbUser

.. sqla-model:: ~aiida.backends.sqlalchemy.models.computer.DbComputer

.. sqla-model:: ~aiida.backends.sqlalchemy.models.authinfo.DbAuthInfo

.. sqla-model:: ~aiida.backends.sqlalchemy.models.comment.DbComment

.. sqla-model:: ~aiida.backends.sqlalchemy.models.log.DbLog

.. sqla-model:: ~aiida.backends.sqlalchemy.models.settings.DbSetting


Sequence tables
---------------

These are necessary to keep track of the id primary key for each main table (including the backend-specific ones).
They end in ``_id_seq`` (for example, **db_dbnode_id_seq**, **db_dbgroup_id_seq**, **db_dblink_id_seq**).


Backend specific tables
-----------------------

 - **auth_group** (django)
 - **auth_group_permissions** (django)
 - **auth_permission** (django)
 - **django_content_type** (django)
 - **django_migrations** (django)
 - **alembic_version** (sqlalchemy)


.. todo:: Database migrations (#4035)
