###############
AiiDA internals
###############

Node
++++

The :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class is the basic class that represents all the possible objects at the AiiDA world. More precisely it is inherited by many classes including (among others) the :py:class:`~aiida.orm.node.process.process.ProcessNode` class, representing computations that convert data into a different form, the :py:class:`~aiida.orm.data.code.Code` class representing executables and file collections that are used by calculations and the :py:class:`~aiida.orm.data.Data` class which represents data that can be input or output of calculations.


Immutability concept
********************
A node can store information through attributes. Since AiiDA guarantees a certain level of provenance, these attributes become immutable as soon as the node is stored.
This means that as soon as a node is stored any attempt to alter its attributes, changing its value or deleting it altogether, shall be met with a raised exception.
Certain subclasses of nodes need to adapt this behavior however, as for example in the case of the :py:class:`~aiida.orm.node.process.process.ProcessNode` class (see `calculation updatable attributes`_), but since the immutability
of stored nodes is a core concept of AiiDA, this behavior is nonetheless enforced on the node level. This guarantees that any subclasses of the Node class will respect this behavior unless it is explicitly overriden.


Methods & properties
********************
In the sequel the most important methods and properties of the :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class will be described.

Node subclasses organization
============================
The :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class has two important variables:

* ``~aiida.orm.implementation.general.node.AbstractNode._plugin_type_string`` characterizes the class of the object.
* ``~aiida.orm.implementation.general.node.AbstractNode._query_type_string`` characterizes the class and all its subclasses (by pointing to the package or Python file that contain the class).

The convention for all the :py:class:`~aiida.orm.implementation.general.node.AbstractNode` subclasses is that if a ``class B`` is inherited by a ``class A`` then there should be a package ``A`` under ``aiida/orm`` that has a file ``__init__.py`` and a ``B.py`` in that directory (or a ``B`` package with the corresponding ``__init__.py``)

An example of this is the :py:class:`~aiida.orm.data.array.ArrayData` and the :py:class:`~aiida.orm.data.array.kpoints.KpointsData`. :py:class:`~aiida.orm.data.array.ArrayData` is placed in ``aiida/orm/data/array/__init__.py`` and :py:class:`~aiida.orm.data.array.kpoints.KpointsData` which inherits from :py:class:`~aiida.orm.data.array.ArrayData` is placed in ``aiida/orm/data/array/kpoints.py``

This is an implicit & quick way to check the inheritance of the :py:class:`~aiida.orm.implementation.general.node.AbstractNode` subclasses.

General purpose methods
=======================
- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.__init__`: The initialization of the Node class can be done by not providing any attributes or by providing a DbNode as initialization. E.g.::

    dbn = a_dbnode_object
    n = Node(dbnode=dbn.dbnode)

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.ctime` and :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.mtime` provide the creation and the modification time of the node.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.is_stored` informs whether a node is already stored to the database.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.query` queries the database by filtering for the results for similar nodes (if the used object is a subclass of :py:class:`~aiida.orm.implementation.general.node.AbstractNode`) or with no filtering if it is a :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class. Note that for this check ``_plugin_type_string`` should be properly set.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_computer` returns the computer associated to this node.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._validate` does a validation check for the node. This is important for :py:class:`~aiida.orm.implementation.general.node.AbstractNode` subclasses where various attributes should be checked for consistency before storing.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_user` returns the user that created the node.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._increment_version_number_db`: increment the version number of the node on the DB. This happens when adding an ``attribute`` or an ``extra`` to the node. This method should not be called by the users.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.uuid` returns the universally unique identifier (UUID) of the node.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.pk` returns the principal key (ID) of the node.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.dbnode` returns the corresponding Django object.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_computer` & :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.set_computer` get and set the computer to be used & is associated to the node.


Annotation methods
==================
The :py:class:`~aiida.orm.implementation.general.node.AbstractNode` can be annotated with labels, description and comments. The following methods can be used for the management of these properties.

*Label management:*

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.label` returns the label of the node. The setter method can be used for the update of the label.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._update_db_label_field` updates the label in the database. This is used by the setter method of the label.

*Description management:*

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.description`: the description of the node (more detailed than the label). There is also a setter method.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._update_db_description_field`: update the node description in the database.

*Comment management:*

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.add_comment` adds a comment.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_comments` returns a sorted list of the comments.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._get_dbcomments` is similar to :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_comments`, just the sorting changes.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._update_comment` updates the node comment. It can be done by ``verdi comment update``.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._remove_comment` removes the node comment. It can be done by ``verdi comment remove``.



Link management methods
=======================
:py:class:`~aiida.orm.implementation.general.node.AbstractNode` objects and objects of its subclasses can have ancestors and descendants. These are connected with links. The following methods exist for the processing & management of these links.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._has_cached_links` shows if there are cached links to other nodes.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.add_link_from` adds a link to the current node from the 'src' node with the given label. Depending on whether the nodes are stored or node, the linked are written to the database or to the cache.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._add_cachelink_from` adds a link to the cache.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._replace_link_from` replaces or creates an input link.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._remove_link_from` removes an input link that is stored in the database.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._replace_dblink_from` is similar to :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._replace_link_from` but works directly on the database.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._remove_dblink_from` is similar to :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._remove_link_from` but works directly on the database.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._add_dblink_from` adds a link to the current node from the given 'src' node. It acts directly on the database.

*Listing links example*

Assume that the user wants to see the available links of a node in order to understand the structure of the graph and maybe traverse it. In the following example, we load a specific node and we list its input and output links. The returned dictionaries have as keys the link name and as value the linked ``node``. Here is the code::

	In [1]: # Let's load a node with a specific pk

	In [2]: c = load_node(139168)

	In [3]: c.get_inputs_dict()
	Out[3]:
	{u'code': <Code: Remote code 'cp-5.1' on daint, pk: 75709, uuid: 3c9cdb7f-0cda-402e-b898-4dd0d06aa5a4>,
	 u'parameters': <ParameterData: uuid: 94efe64f-7f7e-46ea-922a-fe64a7fba8a5 (pk: 139166)>,
	 u'parent_calc_folder': <RemoteData: uuid: becb4894-c50c-4779-b84f-713772eaceff (pk: 139118)>,
	 u'pseudo_Ba': <UpfData: uuid: 5e53b22d-5757-4d50-bbe0-51f3b9ac8b7c (pk: 1905)>,
	 u'pseudo_O': <UpfData: uuid: 5cccd0d9-7944-4c67-b3c7-a39a1f467906 (pk: 1658)>,
	 u'pseudo_Ti': <UpfData: uuid: e5744077-8615-4927-9f97-c5f7b36ba421 (pk: 1660)>,
	 u'settings': <ParameterData: uuid: a5a828b8-fdd8-4d75-b674-2e2d62792de0 (pk: 139167)>,
	 u'structure': <StructureData: uuid: 3096f83c-6385-48c4-8cb2-24a427ce11b1 (pk: 139001)>}

	In [4]: c.get_outputs_dict()
	Out[4]:
	{u'output_parameters': <ParameterData: uuid: f7a3ca96-4594-497f-a128-9843a1f12f7f (pk: 139257)>,
	 u'output_parameters_139257': <ParameterData: uuid: f7a3ca96-4594-497f-a128-9843a1f12f7f (pk: 139257)>,
	 u'output_trajectory': <TrajectoryData: uuid: 7c5b65bc-22bb-4b87-ac92-e8a78cf145c3 (pk: 139256)>,
	 u'output_trajectory_139256': <TrajectoryData: uuid: 7c5b65bc-22bb-4b87-ac92-e8a78cf145c3 (pk: 139256)>,
	 u'remote_folder': <RemoteData: uuid: 17642a1c-8cac-4e7f-8bd0-1dcebe974aa4 (pk: 139169)>,
	 u'remote_folder_139169': <RemoteData: uuid: 17642a1c-8cac-4e7f-8bd0-1dcebe974aa4 (pk: 139169)>,
	 u'retrieved': <FolderData: uuid: a9037dc0-3d84-494d-9616-42b8df77083f (pk: 139255)>,
	 u'retrieved_139255': <FolderData: uuid: a9037dc0-3d84-494d-9616-42b8df77083f (pk: 139255)>}


*Understanding link names*

The nodes may have input and output links. Every input link of a ``node`` should have a unique name and this unique name is mapped to a specific ``node``. On the other hand, given a ``node`` ``c``, many output ``nodes`` may share the same output link name. To differentiate between the output nodes of ``c`` that have the same link name, the ``pk`` of the output node is added next to the link name (please see the input & output nodes in the above example).


Input/output related methods
============================
The input/output links of the node can be accessed by the following methods.

*Methods to get the input data*

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_inputs_dict` returns a dictionary where the key is the label of the input link.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_inputs` returns the list of input nodes

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.inp` returns a :py:meth:`~aiida.orm.implementation.general.node.NodeInputManager` object that can be used to access the node's parents.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.has_parents` returns true or false whether the node has parents

*Methods to get the output data*

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_outputs_dict` returns a dictionary where the key is the label of the output link, and the value is the output node.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_outputs` returns a list of output nodes.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.out` returns a :py:meth:`~aiida.orm.implementation.general.node.NodeOutputManager` object that can be used to access the node's children.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.has_children` returns true or false whether the node has children.

*Navigating in the ``node`` graph*

The user can easily use the :py:meth:`~aiida.orm.implementation.general.node.NodeInputManager` and the :py:meth:`~aiida.orm.implementation.general.node.NodeOutputManager` objects of a ``node`` (provided by the :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.inp` and :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.out` respectively) to traverse the ``node`` graph and access other connected ``nodes``. :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.inp` will give us access to the input ``nodes`` and :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.out` to the output ``nodes``. For example::

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
Each :py:meth:`~aiida.orm.implementation.general.node.AbstractNode` object can have attributes which are properties that characterize the node. Such properties can be the energy, the atom symbols or the lattice vectors. The following methods can be used for the management of the attributes.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._set_attr` adds a new attribute to the node. The key of the attribute is the property name (e.g. ``energy``, ``lattice_vectors`` etc) and the value of the attribute is the value of that property.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._del_attr` & :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._del_all_attrs` delete a specific or all attributes.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_attr` returns a specific attribute.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.iterattrs` returns an iterator over the attributes. The iterators returns tuples of key/value pairs.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.attrs` returns the keys of the attributes.


Extras related methods
======================
``Extras`` are additional information that are added to the calculations. In contrast to ``files`` and ``attributes``, ``extras`` are information added by the user (user specific).

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.set_extra` adds an ``extra`` to the database. To add a more ``extras`` at once, :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.set_extras` can be used.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_extra` and :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_extras` return a specific ``extra`` or all the available ``extras`` respectively. :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.extras` returns the keys of the ``extras``. :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.iterextras` returns an iterator (returning key/value tuples) of the ``extras``.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.del_extra` deletes an ``extra``.


Folder management
=================
``Folder`` objects represent directories on the disk (virtual or not) where extra information for the node are stored. These folders can be temporary or permanent.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.folder` returns the folder associated to the ``node``.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_folder_list` returns the list of files that are in the ``path`` sub-folder of the repository folder.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._repository_folder` returns the permanent repository folder.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._get_folder_pathsubfolder` returns the ``path`` sub-folder in the repository.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._get_temp_folder` returns the ``node`` folder in the temporary repository.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.remove_path` removes a file/directory from the repository.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.add_path` adds a file or directory to the repository folder.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.get_abs_path` returns the absolute path of the repository folder.


Store & deletion
================
- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.store_all` stores all the input ``nodes``, then it stores the current ``node`` and in the end, it stores the cached input links.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._store_input_nodes` stores the input ``nodes``.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._check_are_parents_stored` checks that the parents are stored.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode._store_cached_input_links` stores the input links that are in memory.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.store` method checks that the ``node`` data is valid, then check if ``node``'s parents are stored, then moves the contents of the temporary folder to the repository folder and in the end, it stores in the database the information that are in the cache. The latter happens with a database transaction. In case this transaction fails, then the data transfered to the repository folder are moved back to the temporary folder.

- :py:meth:`~aiida.orm.implementation.general.node.AbstractNode.__del__` deletes temporary folder and it should be called when an in-memory object is deleted.


DbNode
++++++

The :py:class:`~aiida.backends.djsite.db.models.DbNode` is the Django class that corresponds to the :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class allowing to store and retrieve the needed information from and to the database. Other classes extending the :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class, like :py:class:`~aiida.orm.data.Data`, :py:class:`~aiida.orm.node.process.process.ProcessNode` and :py:class:`~aiida.orm.data.code.Code` use the :py:class:`~aiida.backends.djsite.db.models.DbNode` code too to interact with the database.  The main methods are:

- :py:meth:`~aiida.backends.djsite.db.models.DbNode.get_aiida_class` which returns the corresponding AiiDA class instance.

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

- :py:meth:`~aiida.common.folders.RepositoryFolder.section` returns the section to which the ``folder`` belongs. This can be for the moment a ``workflow`` or ``node``.

- :py:meth:`~aiida.common.folders.RepositoryFolder.subfolder` returns the subfolder within the section/uuid folder.

- :py:meth:`~aiida.common.folders.RepositoryFolder.uuid` the UUID of the corresponding ``node`` or ``workflow``.


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
The :py:class:`~aiida.orm.node.process.process.ProcessNode` class is a subclass of the :py:class:`~aiida.orm.implementation.general.node.AbstractNode` class, which means that its attributes become immutable once stored.
However, for a ``Calculation`` to be runnable it needs to be stored, but that would mean that its state, which is stored in an attribute can no longer be updated.
To solve this issue the :py:class:`~aiida.orm.mixins.Sealable` mixin is introduced. This mixin can be used for subclasses of ``Node`` that need to have updatable attributes even after the node has been stored in the database.
The mixin defines the ``_updatable_attributes`` tuple, which defines the attributes that are considered to be mutable even when the node is stored.
It also allows the node to be *sealed*, after which even the updatable attributes become immutable.

ORM overview
++++++++++++

Below you find an overview of the main classes in the AiiDA object-relational mapping.
For the **complete** API documentation see :py:mod:`aiida.orm`.

.. toctree::
    :maxdepth: 2

    orm_overview
