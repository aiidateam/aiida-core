.. _get_started:

===============
Getting started
===============

.. toctree::
    :maxdepth: 1
    :hidden:

    ../get_started/index
    ../get_started/computers
    ../get_started/codes



================
Python interface
================

While the ``verdi`` CLI provides shortcuts for many common tasks, the AiiDA python API provides full access to the underlying AiiDA python objects and their methods.
This is possible via the interactive ``verdi shell`` and via python scripts:


.. toctree::
    :maxdepth: 4

    python_api
    scripting
    daemon_service

===========
Manage data
===========

Data types
==========

.. toctree::
    :maxdepth: 4

    ../datatypes/index
    ../datatypes/kpoints
    ../datatypes/bands
    ../datatypes/functionality

Groups
======

.. toctree::
    :maxdepth: 4

    groups

Querying data
=============

.. toctree::
    :maxdepth: 4

    ../querying/querybuilder/intro
    ../querying/querybuilder/append
    ../querying/querybuilder/queryhelp
    ../querying/backend

Result manager
==============

.. toctree::
    :maxdepth: 4

    resultmanager.rst

Deleting Nodes
==============
.. toctree::
    :maxdepth: 2

    deleting_nodes.rst

Provenance Graphs
=================
.. toctree::
    :maxdepth: 2

    visualising_graphs/visualising_graphs

Import and Export
=================

.. toctree::
    :maxdepth: 4

    ../import_export/main
    ../import_export/external_dbs


==========
Schedulers
==========

Instances of ``CalcJobNode`` instances are submitted by the daemon to an external scheduler.
For this functionality to work, AiiDA needs to be able to interact with these schedulers.
Interfaces have been written for some of the most used schedulers.

.. toctree::
    :maxdepth: 4

    ../scheduler/index

===============
Troubleshooting
===============

.. toctree::
    :maxdepth: 4

    troubleshooting.rst

========
Cookbook
========

.. toctree::
    :maxdepth: 4

    cookbook.rst
