sphinx-aiida demo
=================

This is a demo documentation to show off the features of the ``sphinx-aiida`` extension.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain


You can add the ``:hidden-ports:`` option to also show inputs / outputs starting with ``_``:

.. aiida-workchain:: DemoWorkChain
    :module: demo_workchain
    :hidden-ports:

The command is also hooked into ``sphinx.ext.autodoc``, so you can also use that.

.. automodule:: demo_workchain
    :members:
