=================================
Import and export data from AiiDA
=================================

AiiDA platform allows its users to exchange parts of their graphs containing
already executed calculations but also related nodes like their inputs &
outputs. Exchanging such information among AiiDA instances, or even users of
the same instance, is not a simple task.

Two tools are provided that facilitate the exchange of AiiDA information.

Export
++++++

The export tool can take as input various parameters allowing the user to
export specific nodes based on their identifier or nodes belonging to a
specific group. Given a set of nodes, the export function automatically
selects all the parents and the direct outputs of the selected calculations
(this can be overridden by the user).

The idea behind this automatic selection is that when a node is exported,
very likely, we would like to know how we arrived at the generation of this
node. The same stands for calculation nodes. When a calculation is exported,
it doesn't make a lot of sense to be exported without providing also the
results of that calculation. The exported data (database information but
also files) is stored to a single file which can also be compressed if the
user provides the corresponding option during the export.

Import
++++++
Import is less parameterizable than export. The user has just to provide
a path to the file to be imported (file-system path or URL) and AiiDA will
import the needed information by also checking, and avoiding, possible
identifier collisions and or node duplication.


File format
+++++++++++
The result of the export is a single file which contains all the needed
information for a successful import. This is:

* metadata.json - information about the schema of the database information
  that is exported.
* data.json - information about the exported database nodes that follows the
  format mentioned in the metadata.json. In this files the links between
  the nodes are stored too.
* nodes directory - the repository files that correspond to the exported nodes.

metadata.json
-------------
In this file, apart from the schema, the AiiDA code and the export
file version are also mentioned. This is very important to avoid any
incompatibilities among different versions of AiiDA. It should be noted that
the schema described in metadata.json is related to the data itself -
abstracted schema focused on the extracted information -  and not how the
data is stored in the database (database schema). This makes the import/export
mechanism to be transparent to the database system used, backend selected and
how the data is organised in the database (database schema).

Let's see more closely what is inside this file. If you unzip it you will find
the aforementioned files and directories.

Code sample::

    -rw-rw-r--  1 aiida aiida 165336 Nov 29 16:39 data.json
    -rw-rw-r--  1 aiida aiida   1848 Nov 29 16:39 metadata.json
    drwxrwx--- 70 aiida aiida   4096 Nov 29 16:39 nodes/

It
ds