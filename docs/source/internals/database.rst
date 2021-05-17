.. _internal_architecture:database:

******************
Database structure
******************

The database is the main tool that AiiDA uses to keep track of the provenance.
It directly stores the most critical data and contains the access information for everything that gets stored in the repository.
Its content is organized into different tables, and although the exact structure will depend on the backend used (django or sqlalchemy), most of it is the same for both possibilities.

In the following section, we will first go through the main 9 tables that are related to the AiiDA entities and their relationships.
These tables also have the property of being the same for both backends.
We will give a general overview and explanation of how they work, and provide a more exaustive technical description of their internal structure.
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
This is a 32-position exadecimal sequence that is stored as a string with some dash separated sections (for example: ``479a312d-e9b6-4bbb-93b4-f0a7174ccbf4``).

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


In depth table descriptions
===========================

In the following section you can find a complete list of all the columns for each of the tables.
Each table will also feature a brief description of its more specific and relevant columns.
There are some that are common in many of the tables and so will be described here:

    1. The ``id`` and the ``uuid`` columns were already mentioned above.

    2. The `foreign key` columns were already introduced in the many-to-one section and are easy to recognize.

    4. The columns formatted for timestamps are used to store either the creation time (``time``, ``ctime``) or the last modification time (``mtime``).

    5. The columns for ``label`` and ``description`` are for what the name intuitively implies, and their content is ultimately more free-form and up to the user.


db_dbnode
---------

Each node can be cathegorized according to its ``node_type``, which indicates what kind of data or process node it is.
Additionally, process nodes also have a ``process_type`` that further indicates what is the specific plugin it uses.

Nodes can also store two kind of properties: ``attributes`` and ``extras``.
The ``attributes`` are determined by the ``node_type``, and are set before storing the node and can't be modified afterwards.
The ``extras``, on the other hand, can be added and removed after the node has been stored and are usually set by the user.

 * ``id`` (primary key)
 * ``uuid`` (uuid)
 * ``label`` (varchar255)
 * ``description`` (text)
 * ``node_type`` (varchar255)
 * ``process_type`` (varchar255)
 * ``attributes`` (jsonb)
 * ``extras`` (jsonb)
 * ``ctime`` (timestamp)
 * ``mtime`` (timestamp)
 * ``user_id`` (foreign key)
 * ``dbcomputer_id`` (foreign key)


db_dblink
---------

Each entry in this table contains not only the ``id`` information of the two nodes that are linked, but also some extra properties of the link themselves.
This includes the ``type`` of the link (see the :ref:`topics:provenance:concepts` section for all possible types) as well as a ``label``.
This last one is more specific and tipically determined by the procedure generating the process node that links the data nodes.

 * ``id`` (primary key)
 * ``type`` (varchar255)
 * ``label`` (varchar255)
 * ``input_id`` (foreign key)
 * ``output_id`` (foreign key)


db_dbgroup
----------

Users will tipically identify and handle groups by using their ``label`` (which, unlike the ``labels`` in other tables, must be unique).
Groups also have a ``type``, which serves to identify what plugin is being instanced, and the ``extras`` property for users to set any relevant information.

 * ``id`` (primary key)
 * ``uuid`` (uuid)
 * ``label`` (varchar255)
 * ``description`` (text)
 * ``type_string`` (varchar255)
 * ``extras`` (jsonb)
 * ``time`` (timestamp)
 * ``user_id`` (foreign key)


db_dbgroup_dbnodes
------------------

Unlike the table for the many-to-many relationship between nodes, which adds a bit of extra contextual information, the table for the relationship between nodes and groups just assigns an ``id`` for each relation and records the two elements related.

 * ``id`` (primary key)
 * ``dbnode_id`` (foreign key)
 * ``dbgroup_id`` (foreign key)


db_dbuser
---------

The user information consists of the most basic personal contact details.

 * ``id`` (primary key)
 * ``email`` (varchar255)
 * ``first_name`` (varchar255)
 * ``last_name`` (varchar255)
 * ``institution`` (varchar255)


db_dbcomputer
-------------

Just like groups do with ``labels``, computers are identified within AiiDA by their ``name`` (and thus it must be unique for each one in the database).
On the other hand, the ``hostname`` is the label that identifies the computer within the network from which one can access it.

The ``scheduler_type`` column contains the information of the scheduler (and plugin) that the computer uses to manage jobs, whereas the ``transport_type`` the information of the transport (and plugin) required to copy files and communicate to and from the computer.
The ``metadata`` contains some general settings for these communication and management protocols.

 * ``id`` (primary key)
 * ``uuid`` (uuid)
 * ``name`` (varchar255)
 * ``hostname`` (varchar255)
 * ``description`` (text)
 * ``metadata`` (jsonb)
 * ``transport_type`` (varchar255)
 * ``scheduler_type`` (varchar255)


db_dbauthinfo
-------------

The ``auth_params`` contains the specifications that are user-specific of how to submit jobs in the computer.
The table also has an ``enabled`` logical switch that indicates whether the device is available for use or not.
This last one can be set and unset by the user.

 * ``id`` (primary key)
 * ``metadata`` (jsonb)
 * ``enabled`` (boolean)
 * ``auth_params`` (jsonb)
 * ``aiidauser_id`` (foreign key)
 * ``dbcomputer_id`` (foreign key)


db_dbcomment
------------

The comment table only has the ``content`` column that is specific to it, while the rest of the columns just track the contextual information of the entry.

 * ``id`` (primary key)
 * ``uuid`` (uuid)
 * ``content`` (text)
 * ``ctime`` (timestamp)
 * ``mtime`` (timestamp)
 * ``user_id`` (foreign key)
 * ``dbnode_id`` (foreign key)


db_dblog
--------

The log table not only keeps track of the ``messages`` being recorded, but also of the ``levelname`` (how critical the message is, from a simple report to an irrecoverable error) and the ``loggername`` (what process recorded the message).

 * ``id`` (primary key)
 * ``uuid`` (uuid)
 * ``time`` (timestamp)
 * ``message`` (text)
 * ``metadata`` (jsonb)
 * ``levelname`` (varchar255)
 * ``loggername`` (varchar255)
 * ``dbnode_id`` (foreign key)


The auxiliary tables
====================

db_dbsetting
------------

 * ``id`` (primary key)
 * ``key`` (varchar1024)
 * ``val`` (jsonb)
 * ``time`` (timestamp)
 * ``description`` (text)


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
