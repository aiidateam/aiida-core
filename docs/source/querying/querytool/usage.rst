
Using the ``querytool``
+++++++++++++++++++++++
We provide a Python class (:py:class:`aiida.orm.querytool.QueryTool`) to perform the most common types of queries 
(mainly on nodes, links and their attributes) through an easy Python
class interface, without the need to know anything about the SQL query language.

.. note:: We are working a lot on the interface for querying through
  the QueryTool, so the interface could change significantly in the future
  to allow for more advanced querying capabilities.

To use it, in your script (or within the verdi shell)
you need first to load the :py:class:`~aiida.orm.querytool.QueryTool` class::

  from aiida.orm.querytool import QueryTool

Then, create an instance of this class, which will represent your query (you need to create a new instance for each different query you want to execute)::

 q = QueryTool()

Now, you can call a set of methods on the ``q`` object to decide the filters
you want to apply. The first type of filter one may want to apply is on the
type of nodes you want to obtain (the QueryTool, in the current version,
always queries only nodes in the DB). You can do so passing the correct
Node subclass to the :py:meth:`~aiida.orm.querytool.QueryTool.set_class`
method, for instance::

  q.set_class(Calculation)

Then, if you want to query only calculations within a given group::

  q.set_group(group_name, exclude=False)

where ``group_name`` is the name of the group you want to select. 
The ``exclude`` parameter, if ``True``,
negates the query (i.e., considers all objects *not* included in the 
give group). You can call the
:py:meth:`~aiida.orm.querytool.QueryTool.set_group` method
multiple times to add more filters.

The most important query specification, though, is on the attributes of a
given node.

If you want to query for attributes in the ``DbAttribute`` table,
use the 
:py:meth:`~aiida.orm.querytool.QueryTool.add_attr_filter` method::

  q.add_attr_filter("energy", "<=", 0., relnode="res")

At this point, the query ``q`` describes a query you still have to run, which
will return each calculation ``calc``
for which the result node ``calc.res.energy`` is less or equal to 0. 

The ``relnode`` parameter allows the user to perform queries not only 
on the nodes you want to get out of the query (in this case, do not specify
any ``relnode`` parameter) but also on the value of the attributes of
nodes *linked* to the result nodes. For instance, specifying ``"res"``
as ``relnode``, one gets as result of the query nodes *whose output result*
has a negative energy.

Also in this case, you can add multiple filters on attributes, or you can
use the same syntax also on data you stored in the ``DbExtra`` table 
using :py:meth:`~aiida.orm.querytool.QueryTool.add_extra_filter`.

.. note:: We remind here that while attributes are properties that describe
  a node, are used internally by AiiDA and cannot be changed
  after the node is stored --
  for instance, the coordinates of atoms in a crystal structure, the input
  parameters for a calculation, ... -- extras (stored in ``DbExtra``) have
  the same format and are at full disposal of the user for adding metadata
  to each node, tagging, and later quick querying.

Finally, to run the query and get the results, you can use the 
:py:meth:`~aiida.orm.querytool.QueryTool.run_query` method, that will
return an iterator over the results of the query. For instance, if you
stored ``A`` and ``B`` as extra data of a given node, you can get a list
of the energy of each calculation, and the value of ``A`` and ``B``, using 
the following command::

  res = [(node.res.energy,
          node.get_extra("A"),
          node.get_extra("B") )
          for node in q.run_query()]

.. note:: After having run a query, if you want to run a new one, even if 
  it is a simple modification of the current one, please discard the ``q`` 
  object and create a new one with the new filters.

The transitive closure table
++++++++++++++++++++++++++++
Another type of query that is very common is the discovery of whether
two nodes are linked through a path in the AiiDA graph database, regardless
of how many nodes are in between. 

This is particularly important because, for instance, you may be interested 
in discovering which crystal structures have, say, all phonon frequencies
that are positive; but the information on the phonon frequencies is in a
node that is typically not directly linked to the crystal structure (you
typically have in between at least a SCF calculation, a phonon calculation
on a coarse grid, and an interpolation of the phonon bands on a denser grid; 
moreover, each calculation may include multiple restarts).

In order to make these queries very efficient (and since we expect that
typical workflows, especially in Physics and Materials Science, involve
a lot of relatively small, disconnected graphs), we have implemented 
triggers at the database SQL level to automatically generate a
*transitive closure* table, i.e., a table that for each node contains
all his *parents* (at any depth level) and all the *children* (at any depth
level). This means that, every time two nodes are joined by a link,
this table is automatically updated to contain all the new available paths.

With the aid of such a table, discovering if two nodes are connected or not
becomes a matter of a single query. 
This table is accessible using Django commands, and is called
:py:class:`~aiida.backends.djsite.db.models.DbPath`.

Transitive closure *paths* contain a parent and a child. 
Moreover, they also contain a ``depth``, giving how many nodes have to
be traversed to connect the two ``parent`` and ``child`` nodes (to make
this possible, an entry in the DbPath table is stored for each possible
path in the graph). The depth does not include the first and last node
(so, a depth of zero means that two nodes are directly connected through 
a link).

Three further columns are stored, and they are mainly used to quickly (and
recursively) discover which are the nodes that have been traversed.

.. todo:: The description of the exact meaning of the three additional
  columns (``entry_edge_id``, ``direct_edge_id``, and ``exit_edge_id``,
  will be added soon; in the meatime, you can give a look to the
  implementation of the :py:meth:`~aiida.backends.djsite.db.models.DbPath.expand`
  method).

Finally, given a ``DbPath`` object, we provide a 
:py:meth:`~aiida.backends.djsite.db.models.DbPath.expand` method to get a list
of all the nodes (in the correct order) that are traversed by
the specific path. List elements are AiiDA nodes.

Here we present a simple example of how you can use the transitive closure
table, imagining that you want to get the path between two nodes ``n1`` 
and ``n2``.
We will assume that only a single path exists between the two nodes. If no
path exists, an exception will be raised in the line marked below. 
If more than one path exists, only the first one will be returned. 
The extension to manage the exception and to manage multiple paths 
is straightforward::

  n1 = load_node(NODEPK1)
  n2 = load_node(NODEPK2)
  # In the following line, we are choosing only the first
  # path returned by the query (with [0]). 
  # Change here to manage zero or multiple paths!
  dbpath = models.DbPath.objects.filter(parent=n1, child=n2)[0]
  # Print all nodes in the path
  print dbpath.expand()
