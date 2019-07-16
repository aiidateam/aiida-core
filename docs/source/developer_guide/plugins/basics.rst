Basics
======


What a Plugin Is
----------------

An AiiDA plugin is a `python package <packages>`_ that provides a set of
extensions to AiiDA.

AiiDA plugins can use :ref:`entry points <plugins.entry_points>` in order to 
make the ``aiida-core`` package aware of the extensions.

**Note:** In the python community, the term 'package' is used rather loosely.
Depending on context, it can refer to a collection of python modules or it may,
in addition, include the files necessary for building and installing the
package.

.. _packages: https://docs.python.org/2/tutorial/modules.html?highlight=package#packages

Design guidelines
------------------

 * **Start simple.** Make use of existing classes like
   :py:class:`CalcJobNode <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`,
   :py:class:`Dict <aiida.orm.nodes.data.dict.Dict>`,
   :py:class:`SinglefileData <aiida.orm.nodes.data.singlefile.SinglefileData>`,
   ...
   Write only what is necessary to pass information from and to AiiDA. 
 * **Don't break data provenance.** Store what is needed for full reproducibility.
 * **Parse what you want to query for.** Think about which files to parse into the database and which files to keep on disk.
 * **Expose the full functionality.** 
   Don't artificially limit the power of a code you are wrapping - or your users
   will get frustrated. 
   If the code can do it, there should be *some* way to do it with your plugin.


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
* monkey patch anything within the ``aiida`` namespace (or the namespace itself)

Failure to comply will likely prevent your plugin
from being listed on the official `AiiDA plugin registry <registry>`_.

If you find yourself tempted to do any of the above, please open an issue on
the `AiiDA repository <core>`_ and explain why.
We will advise on how to proceed.


.. _core: https://github.com/aiidateam/aiida-core
.. _registry: https://github.com/aiidateam/aiida-registry
