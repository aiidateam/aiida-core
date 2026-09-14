=================================
Structures and external databases
=================================

AiiDA support the automatic import and export of atomic structures from and to selected external databases.

Import
+++++++

The base class that defines the API for the importers can
be found here: :py:class:`~aiida.tools.dbimporters.baseclasses.DbImporter`.

Below is a list of available plugins:

.. toctree::
   :maxdepth: 4

   dbimporters/icsd
   dbimporters/cod
