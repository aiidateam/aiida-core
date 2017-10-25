DbExporter documentation
========================

.. note:: This is the documentation of the general DbExporter class and the TCOD implementatation.
   TCOD itself accepts a number of plugins that know how to convert code-specific output to the TCOD
   format; these typically live in different repositories. For instance, you can find
   `here <http://aiida-quantumespresso.readthedocs.io/en/latest/module_guide/tcod_dbexporter.html#pw>`_ the
   extensions for Quantum ESPRESSO.

.. toctree::
   :maxdepth: 4

TCOD database exporter
----------------------
.. automodule:: aiida.tools.dbexporters.tcod
   :members:

TCOD parameter translator documentation
---------------------------------------

Base class
++++++++++
.. automodule:: aiida.tools.dbexporters.tcod_plugins
   :members:


