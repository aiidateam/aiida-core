Introduction
============

The main way of interacting with AiiDA is through a command line interface tool called ``verdi``.
You have already used ``verdi`` when installing AiiDA, either through ``verdi quicksetup`` or ``verdi setup``.
But ``verdi`` is very versatile and provides a wealth of other functionalities; here is a list:

* :ref:`calculation<calculation>`:   Inspect and manage calculations.
* :ref:`code<code>`:                 Setup and manage codes.
* :ref:`comment<comment>`:           Inspect, create and manage comments.
* :ref:`computer<computer>`:         Setup and manage computers.
* :ref:`config<config>`:             Set, unset and get profile specific or global configuration options.
* :ref:`daemon<daemon>`:             Inspect and manage the daemon.
* :ref:`data<data>`:                 Inspect, create and manage data nodes.
* :ref:`devel<devel>`:               Commands for developers.
* :ref:`export<export>`:             Create and manage export archives.
* :ref:`graph<graph>`:               Create visual representations of the provenance graph.
* :ref:`group<group>`:               Inspect, create and manage groups.
* :ref:`import<import>`:             Import one or multiple exported AiiDA archives
* :ref:`node<node>`:                 Inspect, create and manage nodes.
* :ref:`process<process>`:           Inspect and manage processes.
* :ref:`profile<profile>`:           Inspect and manage the configured profiles.
* :ref:`quicksetup<quicksetup>`:     Quick setup for the most common usecase (1 user, 1 machine).
* :ref:`rehash<rehash>`:             Recompute the hash for nodes in the database
* :ref:`restapi<restapi>`:           Run the AiiDA REST API server
* :ref:`run<run>`:                   Execute an AiiDA script.
* :ref:`setup<setup>`:               Setup and configure a new profile.
* :ref:`shell<shell>`:               Start a python shell with preloaded AiiDA environment.
* :ref:`status<status>`:             Show service status overview.
* :ref:`user<user>`:                 Inspect and manage users.
* :ref:`work<work>`:                 Inspect and manage work calculations.


Concepts
========

In this section, a few basic concepts of the command line interface will be explained that will apply to all the ``verdi`` commands.

.. _cli_help_strings:

Help strings
------------
Each ``verdi`` command and any optional sub commands have automatically generated help strings that explain the command's functionality and usage.
To show the help string for any command, simply append the ``--help`` option.
For example ``verdi calculation kill --help`` will display::

  Usage: verdi calculation kill [OPTIONS] [CALCULATIONS]...

    Kill one or multiple running calculations.

  Options:
    -f, --force  do not ask for confirmation
    -h, --help   Show this message and exit.

All help strings have the same format and consist of three parts:

  * A usage line describing how to invoke and the accepted parameters
  * A description of the commands functionality
  * A list of the available options

The ``[OPTIONS]`` and ``[CALCULATIONS]...`` tags in the usage description, denote the 'parameters' that the command takes.
A more detailed description of the available options will be listed after the description of the commands functionality
The positional arguments will only be described in the command description itself.
For a more detailed explanation of the difference between options and arguments, see the section about command line :ref:`parameters<cli_parameters>`.


.. _cli_parameters:

Parameters
----------
Most of the ``verdi`` commands and their subcommands can take one or multiple parameters.
In the language of command line interfaces, these parameters come in two flavors:

  * Options
  * Arguments

Arguments are positional parameters, whereas options are indicated by a flag that precedes the value, typically of the form ``-f``, or ``--flag``.
The command line :ref:`help string<cli_help_strings>` section explained that each command will have a help string with a usage line, for example::

  Usage: verdi calculation kill [OPTIONS] [CALCULATIONS]...

The ``[OPTIONS]`` tag indicates that the command takes one or multiple options and one or multiple ``[CALCULATIONS]`` as arguments.
The square brackets in the usage line, indicate that the parameter is optional and not required.
Three dots ``...`` following a parameter indicate that it can not take just one, but also more than one values.


.. _cli_profile:

Profile
-------
AiiDA supports multiple profiles per installation, that can each be configured to use different databases.
One of these profiles will always be marked as the default profile.
To show the current default profile, execute the command::

  verdi profile list

The default profile will be highlighted.
By default, all ``verdi`` commands will always use the default profile.
Having to change the default profile, anytime one wants to apply the ``verdi`` command to another profile is cumbersome.
Therefore, each ``verdi`` command supports the ``-p/--profile`` option, that will force ``verdi`` to use the given profile.
For example, if you wanted to display the list of calculations for a profile that is not the current default, you can execute::

  verdi -p <profile> calculation list

Note that the specified profile will be used for this and only this command.
All subsequent commands, when no specific profile is given, will return to using the default profile.


.. _cli_identifiers:

Identifiers
-----------
Many commands will support arguments or options that serve to identify specific entities in the database, such as nodes, users, groups etc.
Any entity in AiiDA typically will have three different types of identifier:

  * ``ID``: the integer primary key in the database 
  * ``UUID``: the universally unique identifier, a dash-separated hexadecimal string
  * ``LABEL``: a custom string-based label

The ``ID`` and ``UUID`` identifiers follow the exact same rules for all the entities in AiiDA's data model.
However, the ``LABEL`` will vary from entity to entity.
For a ``Code`` instance it will be the ``label`` attribute, whereas for a ``Group`` instance, it will be its name.

All ``verdi`` command arguments and options that serve to pass an entity identifier, will automatically deduce the intended identifier type.
However, since the type of the value is lost over the command line (as each value will be passed as a string type), the command line will have to guess the type.
Each value will first be interpreted as an ``ID``.
If the value cannot be mapped to the ``ID`` of an entity, it will instead be considered a partial or full ``UUID``.
In the case where the identifier can be resolved to neither a valid ``ID`` nor a ``UUID``, the code will finally assume that the value should be interpreted as a ``LABEL``.
In almost all cases, this approach will be able to successfully and unambiguously determine the identifier type, however, there are exceptions.

Consider for example a database with the following three groups:

===  =====================================  ========
ID   UUID                                   LABEL
===  =====================================  ========
10   12dfb104-7b2b-4bca-adc0-1e4fd4ffcc88   group
11   deadbeef-62ba-444f-976d-31d925dac557   10
12   3df34a1e-5215-4e1a-b626-7f75b9586ef5   deadbeef
===  =====================================  ========

We would run into trouble if we wanted to identify the second group by its label ``10``, since it would first be interpreted as an ``ID``, which would return the first group instead.
Likewise, if we wanted to retrieve the third group by its label, we would get the second group instead, since the label ``deadbeef`` is also a valid partial UUID of the second group.
Finally, say we wanted to select the first group using its partial ``UUID`` ``12``, it would unfortunately match the third group on its ``ID`` instead.

Luckily, ``verdi`` provides the tools to break all of these ambiguities with guaranteed success.
The latter ambiguity, between an ``ID`` and ``UUID`` can always be resolved by passing a larger partial ``UUID``.
Inevitably, eventually a non-numeric character or a dash will be included in the partial ``UUID``, rendering it an invalid ``ID`` and the identifier will be cast to the right type.
The case of an identifier, that is intended to refer to a ``LABEL``, that just happens to also be a valid ``ID`` or ``UUID`` cannot be solved in this way.
For this case ``verdi`` reserves a special character, the exclamation mark ``!`` that can be appended to the identifier.
Before any type guessing is done, the command line will check for the presence of this marker, and if found will directly interpret the identifier as a ``LABEL``.
For example, to solve ambiguity problems of the first two examples given in this section, one would have had to pass ``10!`` and ``deadbeef!``.
The exclamation point would have forced them to be interpreted as a ``LABEL`` and ensured that the right group would be retrieved.

In summary, to guarantee correct identification of a specific type:

  * ``UUID``: include at least one non-numeric character or dash in the partial identifier
  * ``LABEL``: append an exclamation mark ``!`` at the end of the identifier


.. _cli_multi_value_options:

Multi value options
-------------------
The section on command line :ref:`parameters<cli_parameters>` explained that some commands support options and arguments that take one or multiple values.
This is fairly typical for command line arguments, but slightly more unorthodox for options, that typically only ever take one value, or none at all if it is a flag.
However, ``verdi`` has multiple commands where an option needs to be able to support options that take more than one value.
Take for example the ``verdi export create`` command, with part of its help string::

  Usage: verdi export create [OPTIONS] OUTPUT_FILE

    Export various entities, such as Codes, Computers, Groups and Nodes, to an
    archive file for backup or sharing purposes.

  Options:
    -X, --codes CODE...             one or multiple codes identified by their
                                    ID, UUID or label
    -Y, --computers COMPUTER...     one or multiple computers identified by
                                    their ID, UUID or label
    -G, --groups GROUP...           one or multiple groups identified by their
                                    ID, UUID or name
    -N, --nodes NODE...             one or multiple nodes identified by their ID
                                    or UUID

The file to which the export archive should be written is given by the argument ``OUTPUT_FILE`` and the command supports various identifier options, e.g. ``CODE...`` and ``NODE...``, that allow the user to specify which entities should be exported.
Note the terminal dots ``...`` that indicate that the options take one or more values.
In traditional command line interfaces, one would have to repeat the option flag if multiple values needed to be specified, e.g.::

  verdi export create -N 10 -N 11 -N 12 archive.aiida

However, for large numbers of values, this gets cumbersome, which is why ``verdi`` supports so-called multiple value options, that allow this to be rewritten as::

  verdi export create -N 10 11 12 archive.aiida

Unfortunately, this leads to an ambiguity, as the 'greedy' multi value option ``-N`` will interpret the argument ``archive.aiida`` as an option value.
This will cause the command to abort if the validation fails, but even worse it might be silently accepted.
The root of the problem is that the multi value option needs to necessarily be greedy and cannot distinguish which value belongs to it and which value is just another argument.
The typical solution for this problem is to use the so called 'endopts' marker, which is defined as two dashes ``--``, which can be used to mark the end of the options and clearly distinguish them from the arguments.
The previous command can therefore be made unambiguous as follows::

  verdi export create -N 10 11 12 -- archive.aiida

This time the parser will notice the ``--`` end options marker and correctly identify ``archive.aiida`` as the positional argument.

Commands
========

Below is a list with all the available subcommands.

.. _calculation:

``verdi calculation``
---------------------

  * **cleanworkdir**: cleans the work directory (remote folder) of AiiDA calculations
  * **gotocomputer**: open a shell to the calc folder on the cluster
  * **inputcat**: shows an input file of a calculation node
  * **inputls**: shows the list of the input files of a calculation node
  * **kill**: [deprecated: use ``verdi process kill`` instead] stop the execution on the cluster of a calculation
  * **list**: list the AiiDA calculations. By default, lists only the running calculations
  * **logshow**: shows the logs/errors produced by a calculation
  * **outputcat**: shows an ouput file of a calculation node
  * **outputls**: shows the list of the output files of a calculation node
  * **plugins**: lists the supported calculation plugins
  * **res**: shows the calculation results (from calc.res)
  * **show**: shows the database information related to the calculation: used code, all the input nodes and all the output nodes

.. warning:: When using gotocomputer, be careful not to change any file that AiiDA created,
  nor to modify the output files or resubmit the calculation, 
  unless you **really** know what you are doing, otherwise AiiDA may get very confused!   


.. _code:

``verdi code``
--------------
Setup and manage code objects.

  *  **delete**: delete a code from the database. Only possible for disconnected codes (i.e. a code that has not been used yet)
  *  **duplicate**: setup a new code, starting from the settings of an existing one
  *  **hide**: hide codes from `verdi code list`
  *  **list**: lists the installed codes
  *  **relabel**: change the label (name) of a code. If you like to load codes based on their labels and not on their UUID's or PK's, make sure to use unique labels!
  *  **reveal**: un-hide codes for `verdi code list`
  *  **setup**: setup a new code
  *  **show**: shows the information of the installed code

.. _comment:

``verdi comment``
-----------------
There are various ways of attaching notes/comments to a node within AiiDA. In the first scripting examples, you might already have noticed the possibility of storing a ``label`` or a ``description`` to any AiiDA Node.
However, these properties are defined when the Node is created, and it is not possible to modify them after the Node has been stored.
The Node ``comment`` provides a simple way to have a more dynamic management of comments, in which any user can write a comment on the Node, or modify it or delete it.
The ``verdi comment`` command provides a set of methods that are used to manipulate the comments:

  * **add**: add a new comment to a Node
  * **remove**: remove a comment
  * **show**: show the existing comments attached for a given Node
  * **update**: modify a comment


.. _computer:

``verdi computer``
------------------
Setup and manage computer objects.

  *  **configure**: set up some extra info that can be used in the connection with that computer
  *  **delete**: deletes a computer node. Works only if the computer node is a disconnected node in the database (has not been used yet)
  *  **disable**: disable a computer (see enable for a larger description)
  *  **enable**: to enable a computer. If the computer is disabled, the daemon will not try to connect to the computer, so it will not retrieve or launch calculations. Useful if a computer is under mantainance
  *  **list**: list all installed computers
  *  **rename**: changes the name of a computer
  *  **setup**: creates a new computer object
  *  **show**: shows the details of an installed computer
  *  **test**: tests if the current user (or a given user) can connect to the computer and if basic operations perform as expected (file copy, getting the list of jobs in the scheduler queue, ...)
  *  **duplicate**: setup a new computer, starting from the settings of an existing one
  *  **update**: [deprecated: use ``verdi computer duplicate`` instead] change configuration of a computer. Works only if the computer node is a disconnected node in the database (has not been used yet)


.. _config:

``verdi config``
----------------
This command allows you to set various configuration options that change how AiiDA works.
The options can be set for specific profiles or globally.
The command works just like ``git config`` does.
Only passing the option name as an argument will print its value, if it is set.
Passing a value as a second argument, will set that value for the given option.
With the ``--unset`` flag an option can be unset and by using ``--global`` the get, set or unset operation is applied globally instead of the default profile.


.. _daemon:

``verdi daemon``
----------------
Manage the daemon, i.e. the process that runs in background and that manages submission/retrieval of calculations and workflows.

  *  **decr**: decrease the number of workers of the daemon
  *  **incr**: increase the number of workers of the daemon
  *  **logshow**: show the last lines of the daemon log (use for debugging)
  *  **restart**: restarts the daemon
  *  **start**: starts the daemon
  *  **status**: see the status of the daemon
  *  **stop**: stops the daemon

  
.. _data:

``verdi data``
--------------
Manage ``Data`` nodes.

  * **array**: handles :class:`aiida.orm.nodes.data.array.ArrayData` objects

    * **show**: visualizes the data object

  * **bands**:  handles :class:`aiida.orm.nodes.data.array.bands.BandsData` objects (band structure object)

    * **export**: export the node as a string of a specified format
    * **list**:   list currently saved nodes of :class:`aiida.orm.nodes.data.array.bands.BandsData` kind
    * **show**:   visualizes the data object

  * **cif**: handles the CifData objects

    * **deposit**: deposit the node to a remote database
    * **export**: export the node as a string of a specified format
    * **import**: create or return (if already present) a database node, having the contents of a supplied file
    * **list**: list currently saved nodes of CifData kind
    * **show**: use third-party visualizer (like jmol) to graphically show the CifData

  * **parameter**: handles the Dict objects

    * **show**: output the content of the python dictionary in different formats.

  * **remote**: handle RemoteData objects

    * **cat**: output the content of a file in the RemoteData folder.
    * **ls**: list the contents of the RemoteData folder.
    * **show**: display general information about the RemoteData object.

  * **structure**: handles the StructureData

    * **deposit**: deposit the node to a remote database
    * **export**: export the node as a string of a specified format
    * **import**: import a StructureData node from file
    * **list**: list currently saved nodes of StructureData kind
    * **show**: use a third-party visualizer (like vmd or xcrysden) to graphically show the StructureData

  * **trajectory**: handles the TrajectoryData objects

    * **deposit**: deposit the node to a remote database
    * **export**: export the node as a string of a specified format
    * **list**: list currently saved nodes of TrajectoryData kind
    * **show**: use third-party visualizer (like jmol) to graphically show the TrajectoryData

  * **upf**: handles the Pseudopotential Datas

    * **exportfamily**: export a family of pseudopotential files into a folder
    * **import**: create or return (if already present) a database node, having the contents of a supplied file
    * **listfamilies**: list presently stored families of pseudopotentials
    * **uploadfamily**: install a new family (group) of pseudopotentials


.. _devel:

``verdi devel``
---------------
Commands intended for developers, such as setting :doc:`config properties<properties>` and running the unit test suite.

  * **run_daemon**: run an instance of the daemon runner in the current interpreter
  * **tests**: run the unittest suite


.. _export:

``verdi export``
----------------
Create and manage export archives.

 * **create**: export a selection of nodes to an aiida export file. See also :ref:`import` and the :ref:`export-file-format`.
 * **migrate**: migrate export archives between file format versions.


.. _graph:

``verdi graph``
---------------
Create graphical representations of part of the provenance graph.
Requires that `graphviz <https://graphviz.org/download>`_ be installed. 

  * **generate**: generates a graph from a given root node either in a graphical or a  ``.dot`` format.


.. _group:

``verdi group``
---------------
Create and manage group objects.

  *  **addnodes**: add nodes to a group.
  *  **list**: list all the groups in the database.
  *  **description**: show or change the description of a group
  *  **show**: show the content of a group.
  *  **create**: create a new empty group.
  *  **rename**: change the name of a group.
  *  **delete**: delete an existing group (but not the nodes belonging to it).
  *  **removenodes**: remove nodes from a group.


.. _help:

``verdi help``
--------------
This command is deprecated, please use ``verdi --help`` instead


.. _import:

``verdi import``
----------------
Import archive files that were created with ``verdi export create``.


.. _install:

``verdi install``
-----------------
This command is deprecated, please use the :ref:`setup <setup>` command instead


.. _node:

``verdi node``
--------------
Manage ``Node`` instances from the provenance graph.

  * **delete**: delete a node and all its descendants from the provenance graph
  * **description**: view or set the description of a node
  * **label**: view or set the label of a node
  * **repo**: shows files and their contents in the local repository
  * **show**: shows basic node information (PK, UUID, class, inputs and outputs)
  * **tree**: shows a tree represenatation in ASCII of the node and its links

.. warning:: In order to preserve the provenance, ``verdi node delete`` will delete not only the list of specified nodes, but also all the children nodes!
  So please be sure to double check what is going to be deleted before running this function.
  This command cannot be undone.


.. _process:

``verdi process``
-----------------
Inspect and manage processes.

 * **list**: Show a list of processes that are still running.
 * **kill**: Kill running processes.
 * **pause**: Pause running processes.
 * **play**: Play paused processes.
 * **watch**: Watch the state transitions for a process.


.. _profile:

``verdi profile``
-----------------
List and change the default profiles.

  * **delete**: delete a profile and the corresponding database and repository
  * **list**: show the list of currently available profiles and the current default profile
  * **setdefault**: set the default profile, i.e. the profile that is used for all ``verdi`` commands if not explicitly specified


.. _quicksetup:

``verdi quicksetup``
--------------------
Set up a sane aiida configuration with as little interaction as possible.


.. _rehash:

``verdi rehash``
----------------
Rehash all nodes in the database filtered by their identifier and/or based on their class.


.. _restapi:

``verdi restapi``
-----------------
Run an instance of the REST API server on localhost.


.. _run:

``verdi run``
-------------
Run a python script for AiiDA.
This is the command line equivalent of the verdi shell.
Has also features of autogrouping: by default, every node created in one a call of verdi run will be grouped together.


.. _setup:

``verdi setup``
---------------
Create and setup a new profile.


.. _shell:

``verdi shell``
---------------
Start a python shell with preloaded AiiDA environment.
Which modules will be preloaded can be configured through :doc:`properties<properties>` set in the configuration file.

.. _status:

``verdi status``
----------------
Show overview of status for services needed by AiiDA.
This can be helpful for pinning down potential problems during debugging.


.. _user:

``verdi user``
--------------
Configure and manage users

  *  **configure**: configure a new AiiDA user
  *  **list**: list existing users configured for your AiiDA installation


.. _work:

``verdi work``
--------------
Manage work calculations.

  * **list**: list the work calculations present in the database
  * **plugins**: show the registered work calculation plugins
  * **report**: show the log messages for a work calculation
  * **status**: shows an ASCII tree for a work calculation showing the status of itself and the calculations it called
  * **kill**: [deprecated: use ``verdi process kill`` instead] kill a work calculation
  * **pause**: [deprecated: use ``verdi process pause`` instead] pause a work calculation
  * **play**: [deprecated: use ``verdi process play`` instead] play a paused work calculation
  * **watch**: [deprecated: use ``verdi process watch`` instead] dynamically print the state transitions for the given work calculation
