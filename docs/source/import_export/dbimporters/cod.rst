COD database importer
---------------------

COD database importer is used to import crystal structures from the `Crystallography Open Database <http://www.crystallography.net>`_ (COD) to AiiDA.

Setup
+++++

An instance of :py:class:`~aiida.tools.dbimporters.plugins.cod.CodDbImporter` is created as follows:

.. code-block:: python

    from aiida.tools.dbimporters.plugins.cod import CodDbImporter

    importer = CodDbImporter()

No additional parameters are required for standard queries on the main COD server.

How to do a query
+++++++++++++++++

A search is initiated by using the :py:meth:`~aiida.tools.dbimporters.plugins.cod.CodDbImporter.query` method, supplying statements using the ``keyword=value`` syntax:

.. code-block:: python

    results = importer.query(chemical_name="caffeine")

List of possible keywords can be listed using the method :py:meth:`~aiida.tools.dbimporters.plugins.cod.CodDbImporter.get_supported_keywords`:

.. code-block:: python

    importer.get_supported_keywords()

Values for most of the keywords can be encapsulated in a list.
In that case the query will return entries that match any of the values (binary `OR`) from the list.
Moreover, in the case of multiple keywords, entries that match all the conditions imposed by the keywords, will be returned (binary `AND`).

Example:

.. code-block:: python

    results = importer.query(chemical_name=["caffeine", "serotonin"], year=[2000, 2001])

is equivalent to the following SQL statement:

.. code-block:: sql

    results = SELECT * FROM data WHERE
                ( chemical_name == "caffeine" OR chemical_name == "serotonin" ) AND
                ( year = 2000 OR year = 2001 )

A query returns an instance of :py:class:`~aiida.tools.dbimporters.plugins.cod.CodSearchResults`, which can be used in the same way as a list of :py:class:`~aiida.tools.dbimporters.plugins.cod.CodEntry` instances:

.. code-block:: python


    print(len(results))

    for entry in results:
        print(entry)

Using data from :py:class:`~aiida.tools.dbimporters.plugins.cod.CodEntry`
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:py:class:`~aiida.tools.dbimporters.plugins.cod.CodEntry` has a few methods (inherited from :py:class:`~aiida.tools.dbimporters.baseclasses.CifEntry`) to access the contents of its instances:

* :py:meth:`~aiida.tools.dbimporters.baseclasses.CifEntry.get_aiida_structure`
* :py:meth:`~aiida.tools.dbimporters.baseclasses.CifEntry.get_ase_structure`
* :py:meth:`~aiida.tools.dbimporters.baseclasses.CifEntry.get_cif_node`
* :py:meth:`~aiida.tools.dbimporters.baseclasses.CifEntry.get_parsed_cif`
* :py:meth:`~aiida.tools.dbimporters.baseclasses.CifEntry.get_raw_cif`
