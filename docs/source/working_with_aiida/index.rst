======================
Command line interface
======================

The main way of interacting with AiiDA is through a command line interface tool called ``verdi``.
Below you will find an overview of all the commands that are available with a link to a more detailed explanation of their usage and available parameters.
But before you dive in, take a few minutes to read the :ref:`general concepts<cli_concepts>` that apply to the entire interface of ``verdi``.
This will make understanding and using ``verdi`` a lot easier!

.. _verdi_overview:

* :ref:`calcjob<verdi_calcjob>`:  Inspect and manage calcjobs.
* :ref:`code<verdi_code>`:  Setup and manage codes.
* :ref:`comment<verdi_comment>`:  Inspect, create and manage node comments.
* :ref:`completioncommand<verdi_completioncommand>`:  Return the bash code to activate completion.
* :ref:`computer<verdi_computer>`:  Setup and manage computers.
* :ref:`config<verdi_config>`:  Set, unset and get profile specific or global configuration options.
* :ref:`daemon<verdi_daemon>`:  Inspect and manage the daemon.
* :ref:`data<verdi_data>`:  Inspect, create and manage data nodes.
* :ref:`database<verdi_database>`:  Inspect and manage the database.
* :ref:`devel<verdi_devel>`:  Commands for developers.
* :ref:`export<verdi_export>`:  Create and manage export archives.
* :ref:`graph<verdi_graph>`:  Create visual representations of part of the provenance graph.
* :ref:`group<verdi_group>`:  Create, inspect and manage groups.
* :ref:`import<verdi_import>`:  Import one or multiple exported AiiDA archives
* :ref:`node<verdi_node>`:  Inspect, create and manage nodes.
* :ref:`plugin<verdi_plugin>`:  Inspect installed plugins for various entry point categories.
* :ref:`process<verdi_process>`:  Inspect and manage processes.
* :ref:`profile<verdi_profile>`:  Inspect and manage the configured profiles.
* :ref:`quicksetup<verdi_quicksetup>`:  Setup a new profile where the database is automatically created and configured.
* :ref:`rehash<verdi_rehash>`:  Recompute the hash for nodes in the database
* :ref:`restapi<verdi_restapi>`:  Run the AiiDA REST API server
* :ref:`run<verdi_run>`:  Execute an AiiDA script.
* :ref:`setup<verdi_setup>`:  Setup a new profile.
* :ref:`shell<verdi_shell>`:  Start a python shell with preloaded AiiDA environment.
* :ref:`status<verdi_status>`:  Print status of AiiDA services.
* :ref:`user<verdi_user>`:  Inspect and manage users.

.. END_OF_VERDI_OVERVIEW_MARKER

.. toctree::
    :maxdepth: 4

    ../verdi/verdi_user_guide.rst


=========
Scripting
=========

While many common functionalities are provided by either command-line tools 
(via ``verdi``) or the web interface, for fine tuning (or automatization) 
it is useful to directly access the python objects and call their methods.

This is possible in two ways, either via an interactive shell, or writing and 
running a script. Both methods are described below.

.. toctree::
    :maxdepth: 4

    scripting



==========
Data types
==========

.. toctree::
    :maxdepth: 4

    ../datatypes/index
    ../datatypes/kpoints
    ../datatypes/bands
    ../datatypes/functionality

======
Groups
======

.. toctree::
    :maxdepth: 4

    groups

==========
Schedulers
==========

As described in the section about calculations, ``CalcJobNode`` instances are submitted by the daemon to an external scheduler.
For this functionality to work, AiiDA needs to be able to interact with these schedulers.
Interfaces have been written for some of the most used schedulers.

.. toctree::
    :maxdepth: 4

    ../scheduler/index

=============
Querying data
=============

.. toctree::
    :maxdepth: 4

    ../querying/querybuilder/intro
    ../querying/querybuilder/append
    ../querying/querybuilder/queryhelp
    ../querying/backend

=======
Caching
=======

.. toctree::
    :maxdepth: 4

    caching.rst

==============
Result manager
==============

.. toctree::
    :maxdepth: 4

    resultmanager.rst


=======
Backups
=======

.. toctree::
    :maxdepth: 4

    ../backup/index.rst

===============
Troubleshooting
===============

.. toctree::
    :maxdepth: 4

    troubleshooting.rst

========
REST API
========

.. toctree::
    :maxdepth: 4

    ../restapi/index.rst

========
Cookbook
========

.. toctree::
    :maxdepth: 4

    cookbook.rst




