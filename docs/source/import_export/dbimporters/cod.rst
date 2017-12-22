COD database importer
---------------------

COD database importer is used to import crystal structures from the
`Crystallography Open Database`_ (COD) to AiiDA.

Setup
+++++

An instance of
:py:class:`CodDbImporter <aiida.tools.dbimporters.plugins.cod.CodDbImporter>`
is created as follows::

    from aiida.tools.dbimporters.plugins.cod import CodDbImporter
    importer = CodDbImporter()

No additional parameters are required for standard queries on the main COD
server.

How to do a query
+++++++++++++++++

A search is initiated by supplying query statements using ``keyword=value``
syntax::

    results = importer.query(chemical_name="caffeine")

List of possible keywords can be listed using::

    importer.get_supported_keywords()

Values for the most of the keywords can be list. In that case the query
will return entries, that match any of the values (binary `OR`) from the
list. Moreover, in the case of multiple keywords, entries, that match all
the conditions imposed by the keywords, will be returned (binary `AND`).

Example::

    results = importer.query(chemical_name=["caffeine","serotonin"],
                             year=[2000,2001])

is equivalent to the following SQL statement::

    results = SELECT * FROM data WHERE
                ( chemical_name == "caffeine" OR chemical_name == "serotonin" ) AND
                ( year = 2000 OR year = 2001 )

A query returns an instance of
:py:class:`CodSearchResults <aiida.tools.dbimporters.plugins.cod.CodSearchResults>`,
which can be used in a same way as a list of
:py:class:`CodEntry <aiida.tools.dbimporters.plugins.cod.CodEntry>` instances::

    print len(results)

    for entry in results:
        print entry

Using data from :py:class:`CodEntry <aiida.tools.dbimporters.plugins.cod.CodEntry>`
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

:py:class:`CodEntry <aiida.tools.dbimporters.plugins.cod.CodEntry>` has a
few functions to access the contents of it's instances::

    CodEntry.get_aiida_structure()
    CodEntry.get_ase_structure()
    CodEntry.get_cif_node()
    CodEntry.get_parsed_cif()
    CodEntry.get_raw_cif()

.. _Crystallography Open Database: http://www.crystallography.net
