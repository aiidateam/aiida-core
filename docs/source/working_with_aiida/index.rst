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


======================
Command line interface
======================

One way of interacting with AiiDA is through the ``verdi`` command line interface (CLI).

Before checking out the individual commands below, start with a brief look at the :ref:`general concepts<cli_concepts>` that apply across all commands.

.. toctree::
    :maxdepth: 1
    :hidden:

    ../verdi/verdi_user_guide.rst

.. _verdi_overview:

* :ref:`calcjob<verdi_calcjob>`:  Inspect and manage calcjobs.
* :ref:`code<verdi_code>`:  Setup and manage codes.
* :ref:`comment<verdi_comment>`:  Inspect, create and manage node comments.
* :ref:`completioncommand<verdi_completioncommand>`:  Return the code to activate bash completion.
* :ref:`computer<verdi_computer>`:  Setup and manage computers.
* :ref:`config<verdi_config>`:  Configure profile-specific or global AiiDA options.
* :ref:`daemon<verdi_daemon>`:  Inspect and manage the daemon.
* :ref:`data<verdi_data>`:  Inspect, create and manage data nodes.
* :ref:`database<verdi_database>`:  Inspect and manage the database.
* :ref:`devel<verdi_devel>`:  Commands for developers.
* :ref:`export<verdi_export>`:  Create and manage export archives.
* :ref:`graph<verdi_graph>`:  Create visual representations of the provenance graph.
* :ref:`group<verdi_group>`:  Create, inspect and manage groups of nodes.
* :ref:`help<verdi_help>`:  Show help for given command.
* :ref:`import<verdi_import>`:  Import data from an AiiDA archive file.
* :ref:`node<verdi_node>`:  Inspect, create and manage nodes.
* :ref:`plugin<verdi_plugin>`:  Inspect AiiDA plugins.
* :ref:`process<verdi_process>`:  Inspect and manage processes.
* :ref:`profile<verdi_profile>`:  Inspect and manage the configured profiles.
* :ref:`quicksetup<verdi_quicksetup>`:  Setup a new profile in a fully automated fashion.
* :ref:`rehash<verdi_rehash>`:  Recompute the hash for nodes in the database.
* :ref:`restapi<verdi_restapi>`:  Run the AiiDA REST API server.
* :ref:`run<verdi_run>`:  Execute scripts with preloaded AiiDA environment.
* :ref:`setup<verdi_setup>`:  Setup a new profile.
* :ref:`shell<verdi_shell>`:  Start a python shell with preloaded AiiDA environment.
* :ref:`status<verdi_status>`:  Print status of AiiDA services.
* :ref:`user<verdi_user>`:  Inspect and manage users.

.. END_OF_VERDI_OVERVIEW_MARKER



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

Backups
=======

.. toctree::
    :maxdepth: 4

    ../backup/index.rst

Import and Export
=================

.. toctree::
    :maxdepth: 4

    ../import_export/main
    ../import_export/external_dbs

=======
Caching
=======

.. toctree::
    :maxdepth: 4

    caching.rst


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

