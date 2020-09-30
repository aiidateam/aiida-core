###############
AiiDA internals
###############

Node
++++

All nodes in an AiiDA provenance graph inherit from the :py:class:`~aiida.orm.nodes.node.Node` class.
Among those are the :py:class:`~aiida.orm.nodes.data.data.Data` class, the :py:class:`~aiida.orm.nodes.process.process.ProcessNode` class representing computations that transform data, and the :py:class:`~aiida.orm.nodes.data.code.Code` class representing executables (and file collections that are used by calculations).


Immutability concept
********************
A node can store information in attributes.
Since AiiDA guarantees a certain level of provenance, these attributes become immutable as soon as the node is stored.
This means that as soon as a node is stored, any attempt to alter its attributes, changing its value or deleting it altogether, shall be met with a raised exception.
Certain subclasses of nodes need to adapt this behavior however, as for example in the case of the :py:class:`~aiida.orm.nodes.process.process.ProcessNode` class (see `calculation updatable attributes`_), but since the immutability of stored nodes is a core concept of AiiDA, this behavior is nonetheless enforced on the node level.
This guarantees that any subclasses of the Node class will respect this behavior unless it is explicitly overriden.

Entity methods
******************
- :py:meth:`~aiida.orm.implementation.utils.clean_value` takes a value and returns an object which can be serialized for storage in the database.
  Such an object must be able to be subsequently deserialized without changing value.
  If a simple datatype is passed (integer, float, etc.), a check is performed to see if it has a value of ``nan`` or ``inf``, as these cannot be stored.
  Otherwise, if a list, tuple, dictionary, etc., is  passed, this check is performed for each value it contains.
  This is done recursively, automatically handling the case of nested objects.
  It is important to note that iterable type objects are converted to lists during this process, and mappings are converted to normal dictionaries.
  For efficiency reasons, the cleaning of attribute values is delayed to the last moment possible.
  This means that for an unstored entity, new attributes are not cleaned but simply set in the cache of the underlying database model.
  When the entity is then stored, all attributes are cleaned in one fell swoop and if successful the values are flushed to the database.
  Once an entity is stored, there no longer is such a cache and so the attribute values are cleaned straight away for each call.
  The same mechanism holds for the cleaning of the values of extras.


Node methods & properties
*************************
In the following sections, the most important methods and properties of the :py:class:`~aiida.orm.nodes.node.Node` class will be described.

Node subclasses organization
============================
The :py:class:`~aiida.orm.nodes.node.Node` class has two important attributes:

* :py:attr:`~aiida.orm.nodes.node.Node._plugin_type_string` characterizes the class of the object.

* :py:attr:`~aiida.orm.nodes.node.Node._query_type_string` characterizes the class and all its subclasses (by pointing to the package or Python file that contain the class).

The convention for all the :py:class:`~aiida.orm.nodes.node.Node` subclasses is that if a ``class B`` is inherited by a ``class A`` then there should be a package ``A`` under ``aiida/orm`` that has a file ``__init__.py`` and a ``B.py`` in that directory (or a ``B`` package with the corresponding ``__init__.py``)

An example of this is the :py:class:`~aiida.orm.nodes.data.array.ArrayData` and the :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData`.
:py:class:`~aiida.orm.nodes.data.array.ArrayData` is placed in ``aiida/orm/data/array/__init__.py`` and :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData` which inherits from :py:class:`~aiida.orm.nodes.data.array.ArrayData` is placed in ``aiida/orm/data/array/kpoints.py``

This is an implicit & quick way to check the inheritance of the :py:class:`~aiida.orm.nodes.node.Node` subclasses.

General purpose methods
=======================
- :py:meth:`~aiida.orm.nodes.node.Node.__init__`: Will construct a new unstored ``Node``.
  Note that this cannot be used to load an existing node from the database.

- :py:meth:`~aiida.orm.nodes.node.Node.ctime` and :py:meth:`~aiida.orm.nodes.node.Node.mtime` provide the creation and the modification time of the node.

- :py:meth:`~aiida.orm.nodes.node.Node.computer` returns the computer associated to this node.

- :py:meth:`~aiida.orm.nodes.node.Node._validate` does a validation check for the node.
  This is important for :py:class:`~aiida.orm.nodes.node.Node` subclasses where various attributes should be checked for consistency before storing.

- :py:meth:`~aiida.orm.nodes.node.Node.user` returns the user that created the node.

- :py:meth:`~aiida.orm.nodes.node.Node.uuid` returns the universally unique identifier (UUID) of the node.


Annotation methods
==================
The :py:class:`~aiida.orm.nodes.node.Node` can be annotated with labels, description and comments.
The following methods can be used for the management of these properties.

*Label management:*

- :py:attr:`~aiida.orm.nodes.node.Node.label` returns the label of the node.
  It can also be used to *change* the label, e.g. ``mynode.label = "new label"``.

*Description management:*

- :py:attr:`~aiida.orm.nodes.node.Node.description`: returns the description of the node (more detailed than the label).
  It can also be used to *change* the description, e.g. ``mynode.description = "new description"``.

*Comment management:*

- :py:meth:`~aiida.orm.nodes.node.Node.add_comment` adds a comment.

- :py:meth:`~aiida.orm.nodes.node.Node.get_comments` returns a sorted list of the comments.

- :py:meth:`~aiida.orm.nodes.node.Node.update_comment` updates the node comment.
  It can also be accessed through the CLI: ``verdi comment update``.

- :py:meth:`~aiida.orm.nodes.node.Node.remove_comment` removes the node comment.
  It can also be accessed through the CLI: ``verdi comment remove``.



Link management methods
=======================
:py:class:`~aiida.orm.nodes.node.Node` objects and objects of its subclasses can have ancestors and descendants.
These are connected with links.
The following methods exist for the management of these links.

- :py:meth:`~aiida.orm.nodes.node.Node.has_cached_links` shows if there are cached links to other nodes.

- :py:meth:`~aiida.orm.nodes.node.Node.add_incoming` adds a link to the current node from the 'src' node with the given link label and link type.
  Depending on whether the nodes are stored or not, the link is written to the database or to the cache.

- :py:meth:`~aiida.orm.nodes.node.Node.get_incoming` returns the iterator of input nodes

*Methods to get the output data*

- :py:meth:`~aiida.orm.nodes.node.Node.get_outgoing` returns the iterator of output nodes.

*Listing links example*

Assume that the user wants to see the available links of a node in order to understand the structure of the graph and maybe traverse it.
In the following example, we load a specific node and we list its incoming and outgoing links::

  In [1]: c = load_node(139168)  # Let's load a node with a specific pk

  In [2]: c.get_incoming().all()
  Out[2]:
  [
    LinkTriple(link_type='inputlink', label='code', node=<Code: Remote code 'cp-5.1' on daint, pk: 75709, uuid: 3c9cdb7f-0cda-402e-b898-4dd0d06aa5a4>),
    LinkTriple(link_type='inputlink', label='parameters', node=<Dict: uuid: 94efe64f-7f7e-46ea-922a-fe64a7fba8a5 (pk: 139166)>)
    LinkTriple(link_type='inputlink', label='parent_calc_folder', node=<RemoteData: uuid: becb4894-c50c-4779-b84f-713772eaceff (pk: 139118)>)
    LinkTriple(link_type='inputlink', label='pseudo_Ba', node=<UpfData: uuid: 5e53b22d-5757-4d50-bbe0-51f3b9ac8b7c (pk: 1905)>)
    LinkTriple(link_type='inputlink', label='pseudo_O', node=<UpfData: uuid: 5cccd0d9-7944-4c67-b3c7-a39a1f467906 (pk: 1658)>)
    LinkTriple(link_type='inputlink', label='pseudo_Ti', node=<UpfData: uuid: e5744077-8615-4927-9f97-c5f7b36ba421 (pk: 1660)>)
    LinkTriple(link_type='inputlink', label='settings', node=<Dict: uuid: a5a828b8-fdd8-4d75-b674-2e2d62792de0 (pk: 139167)>)
    LinkTriple(link_type='inputlink', label='structure', node=<StructureData: uuid: 3096f83c-6385-48c4-8cb2-24a427ce11b1 (pk: 139001)>)
  ]

  In [3]: c.get_outgoing().all()
  Out[3]:
  [
    LinkTriple(link_type='createlink', label='output_parameters', node=<Dict: uuid: f7a3ca96-4594-497f-a128-9843a1f12f7f (pk: 139257)>),
    LinkTriple(link_type='createlink', label='output_parameters_139257', node=<Dict: uuid: f7a3ca96-4594-497f-a128-9843a1f12f7f (pk: 139257)>),
    LinkTriple(link_type='createlink', label='output_trajectory', node=<TrajectoryData: uuid: 7c5b65bc-22bb-4b87-ac92-e8a78cf145c3 (pk: 139256)>),
    LinkTriple(link_type='createlink', label='output_trajectory_139256', node=<TrajectoryData: uuid: 7c5b65bc-22bb-4b87-ac92-e8a78cf145c3 (pk: 139256)>),
    LinkTriple(link_type='createlink', label='remote_folder', node=<RemoteData: uuid: 17642a1c-8cac-4e7f-8bd0-1dcebe974aa4 (pk: 139169)>),
    LinkTriple(link_type='createlink', label='remote_folder_139169', node=<RemoteData: uuid: 17642a1c-8cac-4e7f-8bd0-1dcebe974aa4 (pk: 139169)>),
    LinkTriple(link_type='createlink', label='retrieved', node=<FolderData: uuid: a9037dc0-3d84-494d-9616-42b8df77083f (pk: 139255)>),
    LinkTriple(link_type='createlink', label='retrieved_139255', node=<FolderData: uuid: a9037dc0-3d84-494d-9616-42b8df77083f (pk: 139255)>)
  ]

The :py:meth:`~aiida.orm.nodes.node.Node.get_incoming` and :py:meth:`~aiida.orm.nodes.node.Node.get_outgoing` methods return a manager object that contains a collection of the incoming and outgoing links from the target node.
The collection consists of all the neighboring nodes matched in the query.
Each neighbor is defined by the node, the link label and link type.
This set of three properties is referred to as a `link triple` and is implemented by the :py:class:`~aiida.orm.utils.links.LinkTriple` named tuple.
Through various methods on the link manager, these link triples can be returned.


Attributes related methods
==========================
Each :py:meth:`~aiida.orm.nodes.node.Node` object can have attributes which are properties that characterize the node.
Such properties can be the energy, the atom symbols or the lattice vectors.
The following methods can be used for the management of the attributes.

- :py:meth:`~aiida.orm.nodes.node.Node.set_attribute` and :py:meth:`~aiida.orm.nodes.node.Node.set_attribute_many` adds one or many new attributes to the node.
  The key of the attribute is the property name (e.g. ``energy``, ``lattice_vectors`` etc) and the value of the attribute is the value of that property.

- :py:meth:`~aiida.orm.nodes.node.Node.reset_attributes` will replace all existing attributes with a new set of attributes.

- :py:meth:`~aiida.orm.nodes.node.Node.attributes` is a property that returns all attributes.

- :py:meth:`~aiida.orm.nodes.node.Node.get_attribute` and :py:meth:`~aiida.orm.nodes.node.Node.get_attribute_many` can be used to return a single or many specific attributes.

- :py:meth:`~aiida.orm.nodes.node.Node.delete_attribute` & :py:meth:`~aiida.orm.nodes.node.Node.delete_attribute_many` delete one or multiple specific attributes.

- :py:meth:`~aiida.orm.nodes.node.Node.clear_attributes` will delete all existing attributes.


Extras related methods
======================
`Extras` are additional information that can be added to a node.
In contrast to repository files and attributes, extras are information added by the user and are not immutable, even when the node is stored.

- :py:meth:`~aiida.orm.nodes.node.Node.set_extra` and :py:meth:`~aiida.orm.nodes.node.Node.set_extra_many` adds one or many new extras to the node.
  The key of the extra is the property name (e.g. ``energy``, ``lattice_vectors`` etc) and the value of the extra is the value of that property.

- :py:meth:`~aiida.orm.nodes.node.Node.reset_extras` will replace all existing extras with a new set of extras.

- :py:meth:`~aiida.orm.nodes.node.Node.extras` is a property that returns all extras.

- :py:meth:`~aiida.orm.nodes.node.Node.get_extra` and :py:meth:`~aiida.orm.nodes.node.Node.get_extra_many` can be used to return a single or many specific extras.

- :py:meth:`~aiida.orm.nodes.node.Node.delete_extra` & :py:meth:`~aiida.orm.nodes.node.Node.delete_extra_many` delete one or multiple specific extras.

- :py:meth:`~aiida.orm.nodes.node.Node.clear_extras` will delete all existing extras.


Folder management
=================
``Folder`` objects represent directories on the disk (virtual or not) where extra information for the node are stored.
These folders can be temporary or permanent.


Store & deletion
================
- :py:meth:`~aiida.orm.nodes.node.Node.store_all` stores all the input ``nodes``, then it stores the current ``node`` and in the end, it stores the cached input links.

- :py:meth:`~aiida.orm.nodes.node.Node.verify_are_parents_stored` checks that the parents are stored.

- :py:meth:`~aiida.orm.nodes.node.Node.store` method checks that the ``node`` data is valid, then check if ``node``'s parents are stored, then moves the contents of the temporary folder to the repository folder and in the end, it stores in the database the information that are in the cache. The latter happens with a database transaction. In case this transaction fails, then the data transfered to the repository folder are moved back to the temporary folder.



Folders
+++++++
AiiDA uses :py:class:`~aiida.common.folders.Folder` and its subclasses to add an abstraction layer between the functions and methods working directly on the file-system and AiiDA.
This is particularly useful when we want to easily change between different folder options (temporary, permanent etc) and storage options (plain local directories, compressed files, remote files & directories etc).

:py:class:`~aiida.common.folders.Folder`
****************************************
This is the main class of the available ``Folder`` classes.
Apart from the abstraction provided to the OS operations needed by AiiDA, one of its main features is that it can restrict all the available operations within a given folder limit.
The available methods are:

- :py:meth:`~aiida.common.folders.Folder.mode_dir` and :py:meth:`~aiida.common.folders.Folder.mode_file` return the mode with which folders and files should be writable.

- :py:meth:`~aiida.common.folders.Folder.get_subfolder` returns the subfolder matching the given name

- :py:meth:`~aiida.common.folders.Folder.get_content_list` returns the contents matching a pattern.

- :py:meth:`~aiida.common.folders.Folder.insert_path` adds a file/folder to a specific location and :py:meth:`~aiida.common.folders.Folder.remove_path` removes a file/folder

- :py:meth:`~aiida.common.folders.Folder.get_abs_path` returns the absolute path of a file/folder under a given folder and :py:meth:`~aiida.common.folders.Folder.abspath` returns the absolute path of the folder.

- :py:meth:`~aiida.common.folders.Folder.create_symlink` creates a symlink pointing the given location inside the ``folder``.

- :py:meth:`~aiida.common.folders.Folder.create_file_from_filelike` creates a file from the given contents.

- :py:meth:`~aiida.common.folders.Folder.open` opens a file in the ``folder``.

- :py:meth:`~aiida.common.folders.Folder.folder_limit` returns the limit under which the creation of files/folders is restrained.

- :py:meth:`~aiida.common.folders.Folder.exists` returns true or false depending whether a folder exists or not.

- :py:meth:`~aiida.common.folders.Folder.isfile` and py:meth:`~aiida.common.folders.Folder.isdir` return true or false depending on the existence of the given file/folder.

- :py:meth:`~aiida.common.folders.Folder.create` creates the ``folder``, :py:meth:`~aiida.common.folders.Folder.erase` deletes the ``folder`` and :py:meth:`~aiida.common.folders.Folder.replace_with_folder` copies/moves a given folder.

:py:class:`~aiida.common.folders.RepositoryFolder`
**************************************************
Objects of this class correspond to the repository folders.
The :py:class:`~aiida.common.folders.RepositoryFolder` specific methods are:

- :py:meth:`~aiida.common.folders.RepositoryFolder.__init__` initializes the object with the necessary folder names and limits.

- :py:meth:`~aiida.common.folders.RepositoryFolder.get_topdir` returns the top directory.

- :py:meth:`~aiida.common.folders.RepositoryFolder.section` returns the section to which the ``folder`` belongs. This can be for the moment only  ``node``.

- :py:meth:`~aiida.common.folders.RepositoryFolder.subfolder` returns the subfolder within the section/uuid folder.

- :py:meth:`~aiida.common.folders.RepositoryFolder.uuid` the UUID of the corresponding ``node``.


:py:class:`~aiida.common.folders.SandboxFolder`
***********************************************
:py:class:`~aiida.common.folders.SandboxFolder` objects correspond to temporary ("sandbox") folders.
The main methods are:

- :py:meth:`~aiida.common.folders.SandboxFolder.__init__` creates a new temporary folder

- :py:meth:`~aiida.common.folders.SandboxFolder.__exit__` destroys the folder on exit.


Data
++++

Navigating inputs and outputs
*****************************
- :py:meth:`~aiida.orm.nodes.data.Data.creator` returns either the :py:class:`~aiida.orm.nodes.process.calculation.CalculationNode` that created it or ``None`` if it was not created by a calculation.


ProcessNode
+++++++++++

Navigating inputs and outputs
*****************************
- :py:meth:`~aiida.orm.nodes.process.ProcessNode.caller` returns either the caller :py:class:`~aiida.orm.nodes.process.workflow.WorkflowNode` or ``None`` if it was not called by any process.

CalculationNode
+++++++++++++++

Navigating inputs and outputs
*****************************
- :py:meth:`~aiida.orm.nodes.process.calculation.CalculationNode.inputs` returns a :py:meth:`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's incoming ``INPUT_CALC`` links.

  The ``NodeLinksManager`` can be used to quickly go from a node to a neighboring node.
  For example::

    In [1]: # Let's load a node with a specific pk

    In [2]: c = load_node(139168)

    In [3]: c
    Out[3]: <CpCalculation: uuid: 49084dcf-c708-4422-8bcf-808e4c3382c2 (pk: 139168)>

    In [4]: # Let's traverse the inputs of this node.

    In [5]: # By typing c.inputs.<TAB> we get all the input links

    In [6]: c.inputs.
    c.inputs.code                c.inputs.parent_calc_folder  c.inputs.pseudo_O            c.inputs.settings
    c.inputs.parameters          c.inputs.pseudo_Ba           c.inputs.pseudo_Ti           c.inputs.structure

    In [7]: # We may follow any of these links to access other nodes. For example, let's follow the parent_calc_folder

    In [8]: c.inputs.parent_calc_folder
    Out[8]: <RemoteData: uuid: becb4894-c50c-4779-b84f-713772eaceff (pk: 139118)>

    In [9]: # Let's assign to r the node reached by the parent_calc_folder link

    In [10]: r = c.inputs.parent_calc_folder

    In [11]: r.inputs.__dir__()
    Out[11]:
    ['__class__',
    '__delattr__',
    '__dict__',
    '__dir__',
    '__doc__',
    '__format__',
    '__getattr__',
    '__getattribute__',
    '__getitem__',
    '__hash__',
    '__init__',
    '__iter__',
    '__module__',
    '__new__',
    '__reduce__',
    '__reduce_ex__',
    '__repr__',
    '__setattr__',
    '__sizeof__',
    '__str__',
    '__subclasshook__',
    '__weakref__',
    'remote_folder']

  The ``.inputs`` manager for ``WorkflowNode`` and the ``.outputs`` manager both for ``CalculationNode`` and ``WorkflowNode`` work in the same way (see below).

- :py:meth:`~aiida.orm.nodes.process.calculation.CalculationNode.outputs` returns a :py:meth:`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's outgoing ``CREATE`` links.


.. _calculation updatable attributes:

Updatable attributes
********************
The :py:class:`~aiida.orm.nodes.process.ProcessNode` class is a subclass of the :py:class:`~aiida.orm.nodes.node.Node` class, which means that its attributes become immutable once stored.
However, for a ``Calculation`` to be runnable it needs to be stored, but that would mean that its state, which is stored in an attribute can no longer be updated.
To solve this issue the :py:class:`~aiida.orm.utils.mixins.Sealable` mixin is introduced.
This mixin can be used for subclasses of ``Node`` that need to have updatable attributes even after the node has been stored in the database.
The mixin defines the ``_updatable_attributes`` tuple, which defines the attributes that are considered to be mutable even when the node is stored.
It also allows the node to be *sealed*, after which even the updatable attributes become immutable.

WorkflowNode
++++++++++++

Navigating inputs and outputs
*****************************
- :py:meth:`~aiida.orm.nodes.process.workflow.WorkflowNode.inputs` returns a :py:meth:`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's incoming ``INPUT_WORK`` links.

- :py:meth:`~aiida.orm.nodes.process.workflow.WorkflowNode.outputs` returns a :py:meth:`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's outgoing ``RETURN`` links.


Deprecated features, renaming, and adding new methods
+++++++++++++++++++++++++++++++++++++++++++++++++++++
In case a method is renamed or removed, this is the procedure to follow:

1. (If you want to rename) move the code to the new function name.
   Then, in the docstring, add something like::

     .. versionadded:: 0.7
        Renamed from OLDMETHODNAME

2. Don't remove directly the old function, but just change the code to use
   the new function, and add in the docstring::

     .. deprecated:: 0.7
        Use :meth:`NEWMETHODNAME` instead.

   Moreover, at the beginning of the function, add something like::

     import warnings

     # If we call this DeprecationWarning, pycharm will properly strike out the function
     from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
     warnings.warn("<Deprecation warning here - MAKE IT SPECIFIC TO THIS DEPRECATION, as it will be shown only once per different message>", DeprecationWarning)

     # <REST OF THE FUNCTION HERE>

   (of course replace the parts between ``< >`` symbols with the correct strings).

   The advantage of the method above is:

   - pycharm will still show the method crossed out
   - Our ``AiidaDeprecationWarning`` does not inherit from ``DeprecationWarning``, so it will not be "hidden" by python
   - User can disable our warnings (and only those) by using AiiDA properties with::

       verdi config warnings.showdeprecations False

Changing the config.json structure
++++++++++++++++++++++++++++++++++

In general, changes to ``config.json`` should be avoided if possible.
However, if there is a need to modify it, the following procedure should be used to create a migration:

1. Determine whether the change will be backwards-compatible.
   This means that an older version of AiiDA will still be able to run with the new ``config.json`` structure.
   It goes without saying that it's preferable to change ``config.json`` in a backwards-compatible way.

2. In ``aiida/manage/configuration/migrations/migrations.py``, increase the ``CURRENT_CONFIG_VERSION`` by one.
   If the change is **not** backwards-compatible, set ``OLDEST_COMPATIBLE_CONFIG_VERSION`` to the same value.

3. Write a function which transforms the old config dict into the new version.
   It is possible that you need user input for the migration, in which case this should also be handled in that function.

4. Add an entry in ``_MIGRATION_LOOKUP`` where the key is the version **before** the migration, and the value is a ``ConfigMigration`` object.
   The ``ConfigMigration`` is constructed from your migration function, and the **hard-coded** values of ``CURRENT_CONFIG_VERSION`` and ``OLDEST_COMPATIBLE_CONFIG_VERSION``.
   If these values are not hard-coded, the migration will break as soon as the values are changed again.

5. Add tests for the migration, in ``aiida/backends/tests/manage/configuration/migrations/test_migrations.py``.
   You can add two types of tests:

    * Tests that run the entire migration, using the ``check_and_migrate_config`` function.
      Make sure to run it with ``store=False``, otherwise it will overwrite your ``config.json`` file.
      For these tests, you will have to update the reference files.
    * Tests that run a single step in the migration, using the ``ConfigMigration.apply`` method.
      This can be used if you need to test different edge cases of the migration.

  There are examples for both types of tests.

Daemon and signal handling
++++++++++++++++++++++++++

While the AiiDA daemon is running, interrupt signals (``SIGINT`` and ``SIGTERM``) are captured so that the daemon can shut down gracefully.
This is implemented using Python's ``signal`` module, as shown in the following dummy example:

.. code:: python

    import signal

    def print_foo(*args):
        print('foo')

    signal.signal(signal.SIGINT, print_foo)

You should be aware of this while developing code which runs in the daemon.
In particular, it's important when creating subprocesses.
When a signal is sent, the whole process group receives that signal.
As a result, the subprocess can be killed even though the Python main process captures the signal.
This can be avoided by creating a new process group for the subprocess, meaning that it will not receive the signal.
To do this, you need to pass ``start_new_session=True`` to the ``subprocess`` function:

.. code:: python

    import os
    import subprocess

    print(subprocess.check_output('sleep 3; echo bar', start_new_session=True))
