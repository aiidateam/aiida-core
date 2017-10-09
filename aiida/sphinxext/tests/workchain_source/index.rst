sphinx-aiida demo
=================

This is a demo documentation to show off the features of the ``sphinx-aiida`` extension.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. aiida-workchain:: demo_workchain.DemoWorkChain


You can add the ``:hidden-ports:`` option to also show inputs / outputs starting with ``_``:

.. aiida-workchain:: demo_workchain.DemoWorkChain
    :hidden-ports:
