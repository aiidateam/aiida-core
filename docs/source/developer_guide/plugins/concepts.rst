AiiDA plugins
==============


What a Plugin Is
----------------

An AiiDA plugin is a `python package <packages>`_ that provides a set of
extensions to AiiDA.

AiiDA plugins can use :ref:`entry points <plugins.entry_points>` in order to 
make the ``aiida_core`` package aware of the extensions.

**Note:** In the python community, the term 'package' is used rather loosely.
Depending on context, it can refer to a collection of python modules or it may,
in addition, include the files necessary for building and installing the
package.

.. _packages: https://docs.python.org/2/tutorial/modules.html?highlight=package#packages

What a Plugin Can Do
--------------------

* add new classes to AiiDA's unified interface, including:

  - calculations
  - parsers
  - data types
  - schedulers
  - transports
  - db importers
  - db exporters
  - subcommands to some ``verdi`` commands
  - tests to be run using ``verdi devel tests``

  This typically involves subclassing the respective base class AiiDA provides for that purpose.
* install separate commandline and/or GUI executables
* depend on any number of other plugins (the required versions must
  not clash with AiiDA's requirements)


.. _plugins.maynot:

What a Plugin Should Not Do
---------------------------

An AiiDA plugin should not:

* change the database schema AiiDA uses
* use protected functions, methods or classes of AiiDA (those starting with an underscore ``_``)
* circumvent data provenance
* monkey patch anything within the ``aiida`` namespace (or the namespace itself)

Failure to comply will likely prevent your plugin
from being listed on the official `AiiDA plugin registry <registry>`_.

If you find yourself tempted to do any of the above, please open an issue on
the `AiiDA repository <aiida_core>`_ and explain why.
We will advise on how to proceed.

.. _aiida_core: https://github.com/aiidateam/aiida_core
.. _registry: https://github.com/aiidateam/aiida-registry
