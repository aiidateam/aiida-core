##################
Working with AiiDA
##################

====================================
The ``verdi`` command line interface
====================================

The main way of interacting with AiiDA is through a command line interface tool called ``verdi``.
You have already used ``verdi`` when installing AiiDA, either through ``verdi quicksetup`` or ``verdi setup``.
But ``verdi`` is very versatile and provides a wealth of other functionalities; here is a list:

* :ref:`calculation<calculation>`:              query and interact with calculations
* :ref:`code<code>`:                            setup and manage codes to be used
* :ref:`comment<comment>`:                      manage general properties of nodes in the database
* :ref:`completioncommand<completioncommand>`:  return the bash completion function to put in ~/.bashrc
* :ref:`computer<computer>`:                    setup and manage computers to be used
* :ref:`daemon<daemon>`:                        manage the AiiDA daemon
* :ref:`data<data>`:                            setup and manage data specific types
* :ref:`devel<devel>`:                          AiiDA commands for developers
* :ref:`export<export>`:                        export nodes and group of nodes
* :ref:`graph<graph>`:                          create a graph from a given root node
* :ref:`group<group>`:                          setup and manage groups
* :ref:`import<import>`:                        export nodes and group of nodes
* :ref:`node<node>`:                            manage operations on AiiDA nodes
* :ref:`profile<profile>`:                      list and manage AiiDA profiles
* :ref:`run<run>`:                              execute an AiiDA script
* :ref:`runserver<runserver>`:                  run the AiiDA webserver on localhost
* :ref:`setup<setup>`:                          setup aiida for the current user/create a new profile
* :ref:`shell<shell>`:                          run the interactive shell with the Django environment
* :ref:`user<user>`:                            list and configure new AiiDA users.
* :ref:`workflow<workflow>`:                    manage the AiiDA worflow manager


Each command above can be preceded by the ``-p <profile>`` or ``--profile=<profile>``
option, as in::
  
  verdi -p <profile> calculation list

This allows one to select a specific AiiDA profile, and therefore a specific database,
on which the command is executed. Thus several databases can be handled and 
accessed simultaneously by AiiDA. To install a new profile, use the 
:ref:`install<install>` command.

.. note:: This profile selection has no effect on the ``verdi daemon`` commands.

Some ambiguity might arise when a certain ``verdi`` subcommand manages both positional arguments and at least one option which accepts an unspecified number of arguments. Make sure you insert the separator ``--`` between the last optional argument and the first positional argument. As an example, instead of typing::

  verdi export -g group1 group2 group3 export.aiida

rather type::

  verdi export -g group1 group2 group3 -- export.aiida

 The previous command will export the nodes belonging to groups ``group1``, ``group2``, and ``group3`` (specified by the option ``-g``) into the file ``export.aiida``, which is taken as a positional argument.

Below is a list with all the available subcommands.

.. toctree::
    :maxdepth: 4

    ../verdi/verdi_user_guide


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


========
Plug-ins
========
AiiDA plug-ins are input generators and output parsers, enabling the
integration of codes into AiiDA calculations and workflows.

The plug-ins are not meant to completely automatize the calculation of physical properties. An underlying knowledge of how each code works, which flags it requires, etc. is still required. A total automatization, if desired, has to be implemented at the level of a workflow.

Plugins live in different repositories than AiiDA.
You can find a list of existing plugins on the `AiiDA website <http://www.aiida.net/plugins/>`_ or on the
``aiida-registry`` (check the `JSON version <https://github.com/aiidateam/aiida-registry/blob/master/plugins.json>`_
or the `human-readable version <https://aiidateam.github.io/aiida-registry/>`_), the official location to register
and list plugins.


============
Calculations
============

.. toctree::
    :maxdepth: 4

    ../state/calculation_state
    ../orm/resultmanager

==========
Data types
==========

.. toctree::
    :maxdepth: 4

    ../datatypes/index
    ../datatypes/kpoints
    ../datatypes/functionality

==========
Schedulers
==========

As described in the section about calculations, ``JobCalculation`` instances are submitted by the daemon to an external scheduler.
For this functionality to work, AiiDA needs to be able to interact with these schedulers.
Interfaces have been written for some of the most used schedulers.

.. toctree::
    :maxdepth: 4

    ../scheduler/index

==========
Link types
==========

.. toctree::
    :maxdepth: 4

    ../link_types/index.rst

=============
Querying data
=============

.. toctree::
    :maxdepth: 4

    ../querying/index.rst


=========
Workflows
=========

.. toctree::
    :maxdepth: 4

    ../work/index.rst
    ../old_workflows/index.rst


=======
Backups
=======

.. toctree::
    :maxdepth: 4

    ../backup/index.rst