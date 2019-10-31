.. _UsingQueryBuilder:

About the QueryBuilder
----------------------

.. toctree::
   :maxdepth: 2

The QueryBuilder lets you query your AiiDA database independently of the backend used under the hood.
Before starting to write a query, it helps to:

*   know what you want to query for. In database-speek, you need to
    tell the backend what to *project*. For example, you might be
    interested in the label of a calculation and the pks of all its outputs.
*   know the relationships between entities you are interested in.
    Nodes of an AiiDA graph (vertices) are connected with links (edges).
    A *Node* can be either input or output of another *Node*, but also an
    ancestor or a descendant.
*   know how you want to filter the result.

Once you are clear about what you want and how you can get it,
the QueryBuilder will build an SQL-query for you.

There are two ways of using the QueryBuilder:

#.  In the :ref:`appender method <QueryBuilderAppend>`, you construct your query step by step using `QueryBuilder.append()`
#.  In the :ref:`queryhelp approach <QueryBuilderQueryhelp>`, you construct a dictionary first and pass it to the QueryBuilder

Both APIs provide the same functionality - the appender method may be more suitable
for everyday use in the ``verdi shell``, while the queryhelp method can be useful in scripting.
