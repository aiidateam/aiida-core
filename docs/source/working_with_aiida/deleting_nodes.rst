.. _deleting_nodes:

Usage
=====

In order to delete a given set of nodes, you just need to run::

    verdi node delete [options] [nodes_id]
    verdi node delete --dry-run 1 2 3 4

For this you can use any valid AiiDA node identification number (id, uuid, pk, etc.).
The important thing to take into account is that, in order to keep a consistent provenance, AiiDA will not only delete the nodes explicitly requested, but other linked nodes as well.
To understand how the procedure works and the criteria for node inclusion, please read the :ref:`corresponding subsection<consistency>` of the :ref:`Provenance section<concepts_provenance>`.

