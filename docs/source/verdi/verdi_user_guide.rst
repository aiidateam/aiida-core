######################
The ``verdi`` commands
######################

For some of the most common operations in AiiDA, you can work directly from the command line using the a set of ``verdi`` commands. You already used ``verdi install`` when installing the software. There are quite some more functionalities attached to this command; here's a list:

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
* :ref:`install<install>`:                      install/setup aiida for the current user/create a new profile
* :ref:`node<node>`:                            manage operations on AiiDA nodes
* :ref:`profile<profile>`:                      list and manage AiiDA profiles
* :ref:`run<run>`:                              execute an AiiDA script
* :ref:`shell<shell>`:                          run the interactive shell with the Django environment
* :ref:`user<user>`:                            list and configure new AiiDA users.
* :ref:`work<work>`:                            manage the AiiDA worflow manager
* :ref:`workflow<workflow>`:                    manage the AiiDA legacy worflow manager


Each command above can be preceded by the ``-p <profile>`` or ``--profile=<profile>``
option, as in::
  
  verdi -p <profile> calculation list

This allows to select a specific AiiDA profile, and therefore a specific database,
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

.. _calculation:

``verdi calculation``
+++++++++++++++++++++

  * **kill**: stop the execution on the cluster of a calculation.
  * **logshow**: shows the logs/errors produced by a calculation
  * **plugins**: lists the supported calculation plugins
  * **inputcat**: shows an input file of a calculation node.
  * **inputls**: shows the list of the input files of a calculation node.
  * **list**: list the AiiDA calculations. By default, lists only the running 
    calculations.
  * **outputcat**: shows an ouput file of a calculation node. 
  * **outputls**: shows the list of the output files of a calculation node.
  * **show**: shows the database information related to the calculation: 
    used code, all the input nodes and all the output nodes. 
  * **gotocomputer**: open a shell to the calc folder on the cluster
  * **label**: view / set the label of a calculation
  * **description**: view / set the description of a calculation
  * **res**: shows the calculation results (from calc.res).
  * **cleanworkdir**: cleans the work directory (remote folder) of AiiDA calculations


.. note:: When using gotocomputer, be careful not to change any file
  that AiiDA created,
  nor to modify the output files or resubmit the calculation, 
  unless you **really** know what you are doing, 
  otherwise AiiDA may get very confused!   


.. _code:

``verdi code``
++++++++++++++

  *  **show**: shows the information of the installed code.
  *  **list**: lists the installed codes
  *  **hide**: hide codes from `verdi code list`
  *  **reveal**: un-hide codes for `verdi code list`
  *  **setup**: setup a new code
  *  **rename**: change the label (name) of a code. If you like to load codes 
     based on their labels and not on their UUID's or PK's, take care of using
     unique labels!
  *  **update**: change (some of) the installation description of the code given
     at the moment of the setup. 
  *  **delete**: delete a code from the database. Only possible for disconnected 
     codes (i.e. a code that has not been used yet)


.. _comment:

``verdi comment``
+++++++++++++++++
There are various ways of attaching notes/comments to a node within AiiDA. In the first scripting examples, you might already have noticed the possibility of storing a ``label`` or a ``description`` to any AiiDA Node. However, these properties are defined when the Node is created, and it is not possible to modify them after the Node has been stored.

The Node ``comment`` provides a simple way to have a more dynamic management of comments, in which any user can write a comment on the Node, or modify it or delete it.

The ``verdi comment`` provides a set of methods that are used to manipulate the comments:

* **add**: add a new comment to a Node.
* **update**: modify a comment.
* **show**: show the existing comments attached to the Node.
* **remove**: remove a comment.



.. _completioncommand:

``verdi completioncommand``
+++++++++++++++++++++++++++

Prints the string to be copied and pasted to the bashrc in order to allow for
autocompletion of the verdi commands.


.. _computer:

``verdi computer``
++++++++++++++++++

  *  **setup**: creates a new computer object
  *  **configure**: set up some extra info that can be used in the connection with that computer.
  *  **test**: tests if the current user (or a given user) can connect to the computer and if basic operations perform as expected (file copy, getting the list of jobs in the scheduler queue, ...)
  *  **show**: shows the details of an installed computer
  *  **list**: list all installed computers
  *  **enable**: to enable a computer. If the computer is disabled, the daemon will not try to connect to the computer, so it will not retrieve or launch calculations. Useful if a computer is under mantainance. 
  *  **disable**: disable a computer (see enable for a larger description)
  *  **rename**: changes the name of a computer.
  * **update**: change configuration of a computer. Works only if the computer node is a disconnected node in the database (has not been used yet).
  *  **delete**: deletes a computer node. Works only if the computer node is a disconnected node in the database (has not been used yet)


.. _daemon:

``verdi daemon``
++++++++++++++++
Manages the daemon, i.e. the process that runs in background and that manages 
submission/retrieval of calculations.

  *  **status**: see the status of the daemon. Typically, it will either show ``Daemon not running`` or you will see two processes with state ``RUNNING``.
     
  *  **start**: starts the daemon.
    
  *  **stop**: stops the daemon
  
  *  **restart**: restarts the daemon.
  
  *  **configureuser**: sets the user which is running the daemon. See the installation guide for more details.
  
  *  **logshow**: show the last lines of the daemon log (use for debugging)
  
  
.. _data:

``verdi data``
++++++++++++++
Manages database data objects.

  * **upf**: handles the Pseudopotential Datas
  
    * **listfamilies**: list presently stored families of pseudopotentials
  
    * **uploadfamily**: install a new family (group) of pseudopotentials
  
    * **import**: create or return (if already present) a database node, having the contents of a supplied file
  
    * **exportfamily**: export a family of pseudopotential files into a folder
  
  * **structure**: handles the StructureData
  
    * **list**: list currently saved nodes of StructureData kind
  
    * **show**: use a third-party visualizer (like vmd or xcrysden) to graphically show the StructureData
  
    * **export**: export the node as a string of a specified format
  
    * **deposit**: deposit the node to a remote database
  
  * **parameter**: handles the ParameterData objects
  
    * **show**: output the content of the python dictionary in different formats. 
  
  * **cif**: handles the CifData objects
  
    * **list**: list currently saved nodes of CifData kind
  
    * **show**: use third-party visualizer (like jmol) to graphically show the CifData
  
    * **import**: create or return (if already present) a database node, having the contents of a supplied file
  
    * **export**: export the node as a string of a specified format
  
    * **deposit**: deposit the node to a remote database
  
  * **trajectory**: handles the TrajectoryData objects
  
    * **list**: list currently saved nodes of TrajectoryData kind
  
    * **show**: use third-party visualizer (like jmol) to graphically show the TrajectoryData
  
    * **export**: export the node as a string of a specified format
  
    * **deposit**: deposit the node to a remote database
  
  * **label**: view / set the label of a data
  
  * **description**: view / set the description of a data
  
  * **array**: handles :class:`aiida.orm.data.array.ArrayData` objects
  
    * **show**: visualizes the data object
  
  * **bands**:  handles :class:`aiida.orm.data.array.bands.BandsData` objects (band structure object)
  
    * **export**: export the node as a string of a specified format
  
    * **show**:   visualizes the data object
  
    * **list**:   list currently saved nodes of :class:`aiida.orm.data.array.bands.BandsData` kind


.. _devel:

``verdi devel``
+++++++++++++++

Here there are some functions that are in the development stage, and that might eventually find their way outside of this placeholder. 
As such, they are buggy, possibly difficult to use, not necessarily documented, and they might be subject to non back-compatible changes.

  * **delproperty**, **describeproperties**, **getproperty**, **listproperties**,  **setproperty**: handle the properties, see :doc:`here<properties>` for more information.


Type in ``verdi devel listproperties`` to get a list of all *set* properties, and ``verdi devel describeproperties`` to get a description of all properties that you can possibly set.
The command ``verdi devel getproperty [propertyname]`` will give you the set value for that propery, that can be changed with ``setproperty``.

.. _export:

``verdi export``
++++++++++++++++

 * **create**: Export a selection of nodes to an aiida export file. See also :ref:`import` and the :ref:`export-file-format`.
 * **migrate**: Migrate export archives between file format versions.

.. _graph:

``verdi graph``
+++++++++++++++

  * **generate**: generates a graph from a given root node either in a graphical or a  ``.dot`` format.


.. _group:

``verdi group``
+++++++++++++++

  *  **list**: list all the groups in the database.
  *  **description**: show or change the description of a group
  *  **show**: show the content of a group.
  *  **create**: create a new empty group.
  *  **rename**: change the name of a group.
  *  **delete**: delete an existing group (but not the nodes belonging to it).
  *  **addnodes**: add nodes to a group.
  *  **removenodes**: remove nodes from a group.


.. _import:

``verdi import``
++++++++++++++++

Import AiiDA export file into the AiiDA database.
See also :ref:`export` and the :ref:`export-file-format`.


.. _install:

``verdi install``
+++++++++++++++++

This command is deprecated, please use the :ref:`setup <setup>` command instead


.. _node:

``verdi node``
+++++++++++++++

  * **repo**: shows files and their contents in the local repository

  * **show**: shows basic node information (PK, UUID, class, inputs and
    outputs)
    
  * **tree**: shows a tree of the nodes

  * **delete**: Delete a node and everything that has a provenance from this node.


.. note:: **WARNING!** In order to preserve the provenance, this function
  will delete not only the list of specified nodes,
  but also all the children nodes! So please be sure to double check what
  is going to be deleted before running this function.
  Once delete, this is cannot be undone.


.. _profile:

``verdi profile``
+++++++++++++++++

  * **list**: Show the list of currently available profiles, indicating which
    one is the default one, and showing the current one with a ``>`` symbol

  * **setdefault**: Set the default profile, i.e. the one to be used when no 
    ``-p`` option is specified before the verdi command


.. _run:

``verdi run``
+++++++++++++

Run a python script for AiiDA. This is the command line equivalent of the verdi
shell. Has also features of autogroupin: by default, every node created in one
a call of verdi run will be grouped together.


.. _runserver:

``verdi runserver``
+++++++++++++++++++

Starts a lightweight Web server for development and also serves static files.
Currently in ongoing development.


.. _setup:

``verdi setup``
+++++++++++++++++

Used in the installation to configure the database.
If it finds an already installed database, it updates the tables migrating them 
to the new schema.

.. note:: One can also create a new profile with this command::

    verdi -p <new_profile_name> setup
    
  The setup procedure then works as usual, and one can select there a new database.
  See also the :ref:`profile<profile>` command.


.. _shell:

``verdi shell``
+++++++++++++++

Runs a Python interactive interpreter. 
Tries to use IPython or bpython, if one of them is available.
Loads on start a good part of the AiiDA infrastructure (see :doc:`here<properties>`
for information on how to customize it).

.. _user:

``verdi user``
++++++++++++++
Manages the AiiDA users. Two valid subcommands.

  *  **list**: list existing users configured for your AiiDA installation.
  *  **configure**: configure a new AiiDA user.

.. _work:

``verdi work``
++++++++++++++++++
Manage workflows, valid subcommands:

  * **checkpoint**: display the last recorded checkpoint of a workflow
  * **kill**: kill a workflow
  * **list**: list the workflows present in the database
  * **plugins**: show the registered workflow plugins
  * **report**: show the log messages for a workflow
  * **tree**: shows an ASCII tree for a workflow


.. _workflow:

``verdi workflow``
++++++++++++++++++
Manage legacy workflows, valid subcommands:

  * **report**: display the information on how the workflow is evolving
  * **kill**: kills a workflow
  * **list**: lists the workflows present in the database. By default, shows only the running ones
  * **logshow**: shows the log messages for the workflow
