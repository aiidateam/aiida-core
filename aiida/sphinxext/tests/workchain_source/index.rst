sphinx-aiida demo
=================

This is a demo documentation to show off the features of the ``sphinx-aiida`` extension.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain


You can use the ``:hide-unstored-inputs:`` option to not show the inputs which are not stored in the DB:

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain
    :hide-nondb-inputs:

The command is also hooked into ``sphinx.ext.autodoc``, so you can also use that.

.. automodule:: demo_workchain
    :members:
