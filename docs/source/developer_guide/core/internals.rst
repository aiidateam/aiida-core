###############
AiiDA internals
###############

Node
++++

The :py:class:`~aiida.orm.nodes.Node` class is the basic class that represents all the possible objects at the AiiDA world. More precisely it is inherited by many classes including (among others) the :py:class:`~aiida.orm.nodes.process.ProcessNode` class, representing computations that convert data into a different form, the :py:class:`~aiida.orm.nodes.data.code.Code` class representing executables and file collections that are used by calculations and the :py:class:`~aiida.orm.nodes.data.data.Data` class which represents data that can be input or output of calculations.


Immutability concept
********************
A node can store information through attributes. Since AiiDA guarantees a certain level of provenance, these attributes become immutable as soon as the node is stored.
This means that as soon as a node is stored any attempt to alter its attributes, changing its value or deleting it altogether, shall be met with a raised exception.
Certain subclasses of nodes need to adapt this behavior however, as for example in the case of the :py:class:`~aiida.orm.nodes.process.ProcessNode` class (see `calculation updatable attributes`_), but since the immutability
of stored nodes is a core concept of AiiDA, this behavior is nonetheless enforced on the node level. This guarantees that any subclasses of the Node class will respect this behavior unless it is explicitly overriden.

Node methods
******************
- :py:meth:`~aiida.orm.utils.node.clean_value` takes a value and returns an object which can be serialized for storage in the database. Such an object must be able to be subsequently deserialized without changing value. If a simple datatype is passed (integer, float, etc.), a check is performed to see if it has a value of ``nan`` or ``inf``, as these cannot be stored. Otherwise, if a list, tuple, dictionary, etc., is  passed, this check is performed for each value it contains. This is done recursively, automatically handling the case of nested objects. It is important to note that iterable type objects are converted to lists during this process, and mappings, such as dictionaries, are converted to normal dictionaries. This cleaning process is used by default when setting node attributes via :py:meth:`~aiida.orm.nodes.Node.set_attribute` and :py:meth:`~aiida.orm.nodes.Node.append_to_attr`, although it can be disabled by setting ``clean=False``. Values are also cleaned when setting extras on a stored node using :py:meth:`~aiida.orm.nodes.Node.set_extras` or :py:meth:`~aiida.orm.nodes.Node.reset_extras`, but this cannot be disabled. 


Node methods & properties
*************************
In the following sections, the most important methods and properties of the :py:class:`~aiida.orm.nodes.Node` class will be described.

Node subclasses organization
============================
The :py:class:`~aiida.orm.nodes.Node` class has two important variables:

* ``~aiida.orm.nodes.Node._plugin_type_string`` characterizes the class of the object.
* ``~aiida.orm.nodes.Node._query_type_string`` characterizes the class and all its subclasses (by pointing to the package or Python file that contain the class).

The convention for all the :py:class:`~aiida.orm.nodes.Node` subclasses is that if a ``class B`` is inherited by a ``class A`` then there should be a package ``A`` under ``aiida/orm`` that has a file ``__init__.py`` and a ``B.py`` in that directory (or a ``B`` package with the corresponding ``__init__.py``)

An example of this is the :py:class:`~aiida.orm.nodes.data.array.ArrayData` and the :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData`. :py:class:`~aiida.orm.nodes.data.array.ArrayData` is placed in ``aiida/orm/data/array/__init__.py`` and :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData` which inherits from :py:class:`~aiida.orm.nodes.data.array.ArrayData` is placed in ``aiida/orm/data/array/kpoints.py``

This is an implicit & quick way to check the inheritance of the :py:class:`~aiida.orm.nodes.Node` subclasses.

General purpose methods
=======================
- :py:meth:`~aiida.orm.nodes.Node.__init__`: The initialization of the Node class can be done by not providing any attributes or by providing a DbNode as initialization. E.g.::

    dbn = a_dbnode_object
    n = Node(dbnode=dbn.dbnode)

- :py:meth:`~aiida.orm.nodes.Node.ctime` and :py:meth:`~aiida.orm.nodes.Node.mtime` provide the creation and the modification time of the node.

- :py:meth:`~aiida.orm.nodes.Node.computer` returns the computer associated to this node.

- :py:meth:`~aiida.orm.nodes.Node._validate` does a validation check for the node. This is important for :py:class:`~aiida.orm.nodes.Node` subclasses where various attributes should be checked for consistency before storing.

- :py:meth:`~aiida.orm.nodes.Node.user` returns the user that created the node.

- :py:meth:`~aiida.orm.nodes.Node.uuid` returns the universally unique identifier (UUID) of the node.


Annotation methods
==================
The :py:class:`~aiida.orm.nodes.Node` can be annotated with labels, description and comments. The following methods can be used for the management of these properties.

*Label management:*

- :py:meth:`~aiida.orm.nodes.Node.label` returns the label of the node and can be used as a setter property.

*Description management:*

- :py:meth:`~aiida.orm.nodes.Node.description`: the description of the node (more detailed than the label) and can be used as a setter property.

*Comment management:*

- :py:meth:`~aiida.orm.nodes.Node.add_comment` adds a comment.

- :py:meth:`~aiida.orm.nodes.Node.get_comments` returns a sorted list of the comments.

- :py:meth:`~aiida.orm.nodes.Node.update_comment` updates the node comment. It can be done by ``verdi comment update``.

- :py:meth:`~aiida.orm.nodes.Node.remove_comment` removes the node comment. It can be done by ``verdi comment remove``.



Link management methods
=======================
:py:class:`~aiida.orm.nodes.Node` objects and objects of its subclasses can have ancestors and descendants. These are connected with links. The following methods exist for the processing & management of these links.

- :py:meth:`~aiida.orm.nodes.Node.has_cached_links` shows if there are cached links to other nodes.

- :py:meth:`~aiida.orm.nodes.Node.add_incoming` adds a link to the current node from the 'src' node with the given label. Depending on whether the nodes are stored or node, the linked are written to the database or to the cache.

*Listing links example*

Assume that the user wants to see the available links of a node in order to understand the structure of the graph and maybe traverse it. In the following example, we load a specific node and we list its input and output links. The returned dictionaries have as keys the link name and as value the linked ``node``. Here is the code::

	In [1]: # Let's load a node with a specific pk

	In [2]: c = load_node(139168)

	In [3]: c.get_incoming()
	Out[3]:
	[Neighbor(link_type='inputlink', label='code',
	node=<Code: Remote code 'cp-5.1' on daint, pk: 75709, uuid: 3c9cdb7f-0cda-402e-b898-4dd0d06aa5a4>),
	Neighbor(link_type='inputlink', label='parameters',
	node=<Dict: uuid: 94efe64f-7f7e-46ea-922a-fe64a7fba8a5 (pk: 139166)>)
	Neighbor(link_type='inputlink', label='parent_calc_folder',
	node=<RemoteData: uuid: becb4894-c50c-4779-b84f-713772eaceff (pk: 139118)>)
	Neighbor(link_type='inputlink', label='pseudo_Ba',
	node=<UpfData: uuid: 5e53b22d-5757-4d50-bbe0-51f3b9ac8b7c (pk: 1905)>)
	Neighbor(link_type='inputlink', label='pseudo_O',
	node=<UpfData: uuid: 5cccd0d9-7944-4c67-b3c7-a39a1f467906 (pk: 1658)>)
	Neighbor(link_type='inputlink', label='pseudo_Ti',
	node=<UpfData: uuid: e5744077-8615-4927-9f97-c5f7b36ba421 (pk: 1660)>)
	Neighbor(link_type='inputlink', label='settings',
	node=<Dict: uuid: a5a828b8-fdd8-4d75-b674-2e2d62792de0 (pk: 139167)>)
	Neighbor(link_type='inputlink', label='structure',
	node=<StructureData: uuid: 3096f83c-6385-48c4-8cb2-24a427ce11b1 (pk: 139001)>)]

	In [4]: c.get_outgoing()
	Out[4]:
	[Neighbor(link_type='createlink', label='output_parameters',
	node=<Dict: uuid: f7a3ca96-4594-497f-a128-9843a1f12f7f (pk: 139257)>),
	Neighbor(link_type='createlink', label='output_parameters_139257',
	node=<Dict: uuid: f7a3ca96-4594-497f-a128-9843a1f12f7f (pk: 139257)>),
	Neighbor(link_type='createlink', label='output_trajectory',
	node=<TrajectoryData: uuid: 7c5b65bc-22bb-4b87-ac92-e8a78cf145c3 (pk: 139256)>),
	Neighbor(link_type='createlink', label='output_trajectory_139256',
	node=<TrajectoryData: uuid: 7c5b65bc-22bb-4b87-ac92-e8a78cf145c3 (pk: 139256)>),
	Neighbor(link_type='createlink', label='remote_folder',
	node=<RemoteData: uuid: 17642a1c-8cac-4e7f-8bd0-1dcebe974aa4 (pk: 139169)>),
	Neighbor(link_type='createlink', label='remote_folder_139169',
	node=<RemoteData: uuid: 17642a1c-8cac-4e7f-8bd0-1dcebe974aa4 (pk: 139169)>),
	Neighbor(link_type='createlink', label='retrieved',
	node=<FolderData: uuid: a9037dc0-3d84-494d-9616-42b8df77083f (pk: 139255)>),
	Neighbor(link_type='createlink', label='retrieved_139255',
	node=<FolderData: uuid: a9037dc0-3d84-494d-9616-42b8df77083f (pk: 139255)>)]


*Understanding link names*

The nodes may have input and output links. Every input link of a ``node`` should have a unique name and this unique name is mapped to a specific ``node``. On the other hand, given a ``node`` ``c``, many output ``nodes`` may share the same output link name. To differentiate between the output nodes of ``c`` that have the same link name, the ``pk`` of the output node is added next to the link name (please see the input & output nodes in the above example).


Input/output related methods
============================
The input/output links of the node can be accessed by the following methods.

*Methods to get the input data*

- :py:meth:`~aiida.orm.nodes.Node.get_incoming` returns the iterator of input nodes

- :py:meth:`~aiida.orm.nodes.Node.inp` returns a :py:meth:`~aiida.orm.utils.managers.NodeInputManager` object that can be used to access the node's parents.

*Methods to get the output data*

- :py:meth:`~aiida.orm.nodes.Node.get_outgoing` returns the iterator of output nodes.

- :py:meth:`~aiida.orm.nodes.Node.out` returns a :py:meth:`~aiida.orm.utils.managers.NodeOutputManager` object that can be used to access the node's children.

*Navigating in the ``node`` graph*

The user can easily use the :py:meth:`~aiida.orm.utils.managers.NodeInputManager` and the :py:meth:`~aiida.orm.utils.managers.NodeOutputManager` objects of a ``node`` (provided by the :py:meth:`~aiida.orm.nodes.Node.inp` and :py:meth:`~aiida.orm.nodes.Node.out` respectively) to traverse the ``node`` graph and access other connected ``nodes``. :py:meth:`~aiida.orm.nodes.Node.inp` will give us access to the input ``nodes`` and :py:meth:`~aiida.orm.nodes.Node.out` to the output ``nodes``. For example::

	In [1]: # Let's load a node with a specific pk

	In [2]: c = load_node(139168)

	In [3]: c
	Out[3]: <CpCalculation: uuid: 49084dcf-c708-4422-8bcf-808e4c3382c2 (pk: 139168)>

	In [4]: # Let's traverse the inputs of this node.

	In [5]: # By typing c.inp. we get all the input links

	In [6]: c.inp.
	c.inp.code                c.inp.parent_calc_folder  c.inp.pseudo_O            c.inp.settings
	c.inp.parameters          c.inp.pseudo_Ba           c.inp.pseudo_Ti           c.inp.structure

	In [7]: # We may follow any of these links to access other nodes. For example, let's follow the parent_calc_folder

	In [8]: c.inp.parent_calc_folder
	Out[8]: <RemoteData: uuid: becb4894-c50c-4779-b84f-713772eaceff (pk: 139118)>

	In [9]: # Let's assign to r the node reached by the parent_calc_folder link

	In [10]: r = c.inp.parent_calc_folder

	In [11]: r.inp.__dir__()
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
	 u'remote_folder']

	In [12]: r.out.
	r.out.parent_calc_folder         r.out.parent_calc_folder_139168

	In [13]: # By following the same link from node r, you will get node c

	In [14]: r.out.parent_calc_folder
	Out[14]: <CpCalculation: uuid: 49084dcf-c708-4422-8bcf-808e4c3382c2 (pk: 139168)>


Attributes related methods
==========================
Each :py:meth:`~aiida.orm.nodes.Node` object can have attributes which are properties that characterize the node. Such properties can be the energy, the atom symbols or the lattice vectors. The following methods can be used for the management of the attributes.

- :py:meth:`~aiida.orm.nodes.Node.set_attribute` adds a new attribute to the node. The key of the attribute is the property name (e.g. ``energy``, ``lattice_vectors`` etc) and the value of the attribute is the value of that property.

- :py:meth:`~aiida.orm.nodes.Node.delete_attribute` & :py:meth:`~aiida.orm.nodes.Node.delete_attributes` delete a specific or all attributes.

- :py:meth:`~aiida.orm.nodes.Node.get_attribute` returns a specific attribute.


Extras related methods
======================
``Extras`` are additional information that are added to the calculations. In contrast to ``files`` and ``attributes``, ``extras`` are information added by the user (user specific).

- :py:meth:`~aiida.orm.nodes.Node.set_extra` adds an ``extra`` to the database. To add a more ``extras`` at once, :py:meth:`~aiida.orm.nodes.Node.set_extras` can be used.

- :py:meth:`~aiida.orm.nodes.Node.get_extra` and :py:meth:`~aiida.orm.nodes.Node.get_extras` return a specific ``extra`` or all the available ``extras`` respectively.

- :py:meth:`~aiida.orm.nodes.Node.delete_extra` deletes an ``extra``.


Folder management
=================
``Folder`` objects represent directories on the disk (virtual or not) where extra information for the node are stored. These folders can be temporary or permanent.


Store & deletion
================
- :py:meth:`~aiida.orm.nodes.Node.store_all` stores all the input ``nodes``, then it stores the current ``node`` and in the end, it stores the cached input links.

- :py:meth:`~aiida.orm.nodes.Node.verify_are_parents_stored` checks that the parents are stored.

- :py:meth:`~aiida.orm.nodes.Node.store` method checks that the ``node`` data is valid, then check if ``node``'s parents are stored, then moves the contents of the temporary folder to the repository folder and in the end, it stores in the database the information that are in the cache. The latter happens with a database transaction. In case this transaction fails, then the data transfered to the repository folder are moved back to the temporary folder.


DbNode
++++++

The :py:class:`~aiida.backends.djsite.db.models.DbNode` is the Django class that corresponds to the :py:class:`~aiida.orm.nodes.Node` class allowing to store and retrieve the needed information from and to the database. Other classes extending the :py:class:`~aiida.orm.nodes.Node` class, like :py:class:`~aiida.orm.nodes.data.data.Data`, :py:class:`~aiida.orm.nodes.process.ProcessNode` and :py:class:`~aiida.orm.nodes.data.code.Code` use the :py:class:`~aiida.backends.djsite.db.models.DbNode` code too to interact with the database.  The main methods are:

- :py:meth:`~aiida.backends.djsite.db.models.DbNode.get_simple_name` which returns a string with the type of the class (by stripping the path before the class name).

- :py:meth:`~aiida.backends.djsite.db.models.DbNode.attributes` which returns the all the attributes of the specific node as a dictionary.

- :py:meth:`~aiida.backends.djsite.db.models.DbNode.extras` which returns all the extras of the specific node as a dictionary.



Folders
+++++++
AiiDA uses :py:class:`~aiida.common.folders.Folder` and its subclasses to add an abstraction layer between the functions and methods working directly on the file-system and AiiDA. This is particularly useful when we want to easily change between different folder options (temporary, permanent etc) and storage options (plain local directories, compressed files, remote files & directories etc).

:py:class:`~aiida.common.folders.Folder`
****************************************
This is the main class of the available ``Folder`` classes. Apart from the abstraction provided to the OS operations needed by AiiDA, one of its main features is that it can restrict all the available operations within a given folder limit. The available methods are:

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
Objects of this class correspond to the repository folders. The :py:class:`~aiida.common.folders.RepositoryFolder` specific methods are:

- :py:meth:`~aiida.common.folders.RepositoryFolder.__init__` initializes the object with the necessary folder names and limits.

- :py:meth:`~aiida.common.folders.RepositoryFolder.get_topdir` returns the top directory.

- :py:meth:`~aiida.common.folders.RepositoryFolder.section` returns the section to which the ``folder`` belongs. This can be for the moment only  ``node``.

- :py:meth:`~aiida.common.folders.RepositoryFolder.subfolder` returns the subfolder within the section/uuid folder.

- :py:meth:`~aiida.common.folders.RepositoryFolder.uuid` the UUID of the corresponding ``node``.


:py:class:`~aiida.common.folders.SandboxFolder`
***********************************************
:py:class:`~aiida.common.folders.SandboxFolder` objects correspond to temporary ("sandbox") folders. The main methods are:

- :py:meth:`~aiida.common.folders.SandboxFolder.__init__` creates a new temporary folder

- :py:meth:`~aiida.common.folders.SandboxFolder.__exit__` destroys the folder on exit.



Calculation
+++++++++++

.. _calculation updatable attributes:

Updatable attributes
********************
The :py:class:`~aiida.orm.nodes.process.ProcessNode` class is a subclass of the :py:class:`~aiida.orm.nodes.Node` class, which means that its attributes become immutable once stored.
However, for a ``Calculation`` to be runnable it needs to be stored, but that would mean that its state, which is stored in an attribute can no longer be updated.
To solve this issue the :py:class:`~aiida.orm.utils.mixins.Sealable` mixin is introduced. This mixin can be used for subclasses of ``Node`` that need to have updatable attributes even after the node has been stored in the database.
The mixin defines the ``_updatable_attributes`` tuple, which defines the attributes that are considered to be mutable even when the node is stored.
It also allows the node to be *sealed*, after which even the updatable attributes become immutable.

ORM overview
++++++++++++

Below you find an overview of the main classes in the AiiDA object-relational mapping.
For the **complete** API documentation see :py:mod:`aiida.orm`.

.. toctree::
    :maxdepth: 2

    orm_overview

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
 
   (of course replace the parts between ``< >`` symbols with the
   correct strings).

   The advantage of the method above is:

   - pycharm will still show the method crossed out
   - Our ``AiidaDeprecationWarning`` does not inherit from ``DeprecationWarning``, so it will not be "hidden" by python
   - User can disable our warnings (and only those) by using AiiDA
     properties with::
       
       verdi config warnings.showdeprecations False

Changing the config.json structure
++++++++++++++++++++++++++++++++++

In general, changes to ``config.json`` should be avoided if possible. However, if there is a need to modify it, the following procedure should be used to create a migration:

1. Determine whether the change will be backwards-compatible. This means that an older version of AiiDA will still be able to run with the new ``config.json`` structure. It goes without saying that it's preferable to change ``config.json`` in a backwards-compatible way.

2. In ``aiida/manage/configuration/migrations/migrations.py``, increase the ``CURRENT_CONFIG_VERSION`` by one. If the change is **not** backwards-compatible, set ``OLDEST_COMPATIBLE_CONFIG_VERSION`` to the same value.

3. Write a function which transforms the old config dict into the new version. It is possible that you need user input for the migration, in which case this should also be handled in that function.

4. Add an entry in ``_MIGRATION_LOOKUP`` where the key is the version **before** the migration, and the value is a ``ConfigMigration`` object. The ``ConfigMigration`` is constructed from your migration function, and the **hard-coded** values of ``CURRENT_CONFIG_VERSION`` and ``OLDEST_COMPATIBLE_CONFIG_VERSION``. If these values are not hard-coded, the migration will break as soon as the values are changed again.

5. Add tests for the migration, in ``aiida/backends/tests/manage/configuration/migrations/test_migrations.py``. You can add two types of tests:

    * Tests that run the entire migration, using the ``check_and_migrate_config`` function. Make sure to run it with ``store=False``, otherwise it will overwrite your ``config.json`` file. For these tests, you will have to update the reference files.
    * Tests that run a single step in the migration, using the ``ConfigMigration.apply`` method. This can be used if you need to test different edge cases of the migration.

  There are examples for both types of tests.

Daemon and signal handling
++++++++++++++++++++++++++

While the AiiDA daemon is running, interrupt signals (``SIGINT`` and ``SIGTERM``) are captured so that the daemon can shut down gracefully. This is implemented using Python's ``signal`` module, as shown in the following dummy example:

.. code:: python

    import signal

    def print_foo(*args):
        print('foo')

    signal.signal(signal.SIGINT, print_foo)

You should be aware of this while developing code which runs in the daemon. In particular, it's important when creating subprocesses. When a signal is sent, the whole process group receives that signal. As a result, the subprocess can be killed even though the Python main process captures the signal. This can be avoided by creating a new process group for the subprocess, meaning that it will not receive the signal. To do this, you need to pass ``preexec_fn=os.setsid`` to the ``subprocess`` function:

.. code:: python

    import os
    import subprocess

    print(subprocess.check_output('sleep 3; echo bar', preexec_fn=os.setsid))

