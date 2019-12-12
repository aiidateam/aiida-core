sphinx-aiida demo
=================

This is a demo documentation to show off the features of the ``sphinx-aiida`` extension.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain


If you want to hide the inputs that are not stored as nodes in the database, use the ``:hide-unstored-inputs:`` option.

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain
    :hide-nondb-inputs:


The namespaces can be set to expand by default, using the ``:expand-namespaces:`` option.

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain
    :expand-namespaces:

The command is also hooked into ``sphinx.ext.autodoc``, so AiiDA processes will be properly documented using ``.. automodule::`` as well.

.. automodule:: demo_workchain
    :members:
