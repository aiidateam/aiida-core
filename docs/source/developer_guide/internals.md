# AiiDA internals

## Node

All nodes in an AiiDA provenance graph inherit from the {py:class}`~aiida.orm.nodes.node.Node` class.
Among those are the {py:class}`~aiida.orm.nodes.data.data.Data` class, the {py:class}`~aiida.orm.nodes.process.process.ProcessNode` class representing computations that transform data, and the {py:class}`~aiida.orm.nodes.data.code.abstract.AbstractCode` class representing executables (and file collections that are used by calculations).

### Immutability concept

A node can store information in attributes.
Since AiiDA guarantees a certain level of provenance, these attributes become immutable as soon as the node is stored.
This means that as soon as a node is stored, any attempt to alter its attributes, changing its value or deleting it altogether, shall be met with a raised exception.
Certain subclasses of nodes need to adapt this behavior however, as for example in the case of the {py:class}`~aiida.orm.nodes.process.process.ProcessNode` class (see [updatable attributes](#updatable-attributes)), but since the immutability of stored nodes is a core concept of AiiDA, this behavior is nonetheless enforced on the node level.
This guarantees that any subclasses of the Node class will respect this behavior unless it is explicitly overridden.

### Entity methods

- {py:meth}`~aiida.orm.implementation.utils.clean_value` takes a value and returns an object which can be serialized for storage in the database.
  Such an object must be able to be subsequently deserialized without changing value.
  If a simple datatype is passed (integer, float, etc.), a check is performed to see if it has a value of `nan` or `inf`, as these cannot be stored.
  Otherwise, if a list, tuple, dictionary, etc., is passed, this check is performed for each value it contains.
  This is done recursively, automatically handling the case of nested objects.
  It is important to note that iterable type objects are converted to lists during this process, and mappings are converted to normal dictionaries.
  For efficiency reasons, the cleaning of attribute values is delayed to the last moment possible.
  This means that for an unstored entity, new attributes are not cleaned but simply set in the cache of the underlying database model.
  When the entity is then stored, all attributes are cleaned in one fell swoop and if successful the values are flushed to the database.
  Once an entity is stored, there no longer is such a cache and so the attribute values are cleaned straight away for each call.
  The same mechanism holds for the cleaning of the values of extras.

### Node methods and properties

In the following sections, the most important methods and properties of the {py:class}`~aiida.orm.nodes.node.Node` class will be described.

#### Node subclasses organization

The {py:class}`~aiida.orm.nodes.node.Node` class has two important attributes:

* {py:attr}`~aiida.orm.nodes.node.Node._plugin_type_string` characterizes the class of the object.
* {py:attr}`~aiida.orm.nodes.node.Node._query_type_string` characterizes the class and all its subclasses (by pointing to the package or Python file that contain the class).

The convention for all the {py:class}`~aiida.orm.nodes.node.Node` subclasses is that if a `class B` is inherited by a `class A` then there should be a package `A` under `aiida/orm` that has a file `__init__.py` and a `B.py` in that directory (or a `B` package with the corresponding `__init__.py`).

An example of this is the {py:class}`~aiida.orm.ArrayData` and the {py:class}`~aiida.orm.nodes.data.array.kpoints.KpointsData`.
{py:class}`~aiida.orm.ArrayData` is placed in `aiida/orm/data/array/__init__.py` and {py:class}`~aiida.orm.nodes.data.array.kpoints.KpointsData` which inherits from {py:class}`~aiida.orm.ArrayData` is placed in `aiida/orm/data/array/kpoints.py`.

This is an implicit and quick way to check the inheritance of the {py:class}`~aiida.orm.nodes.node.Node` subclasses.

#### General purpose methods

- {py:meth}`~aiida.orm.nodes.node.Node.__init__`: constructs a new unstored `Node`.
  Note that this cannot be used to load an existing node from the database.
- {py:meth}`~aiida.orm.nodes.node.Node.ctime` and {py:meth}`~aiida.orm.nodes.node.Node.mtime` provide the creation and the modification time of the node.
- {py:meth}`~aiida.orm.nodes.node.Node.computer` returns the computer associated to this node.
- {py:meth}`~aiida.orm.nodes.node.Node._validate` does a validation check for the node.
  This is important for {py:class}`~aiida.orm.nodes.node.Node` subclasses where various attributes should be checked for consistency before storing.
- {py:meth}`~aiida.orm.nodes.node.Node.user` returns the user that created the node.
- {py:meth}`~aiida.orm.nodes.node.Node.uuid` returns the universally unique identifier (UUID) of the node.

#### Annotation methods

The {py:class}`~aiida.orm.nodes.node.Node` can be annotated with labels, description, and comments.

*Label management:*

- {py:attr}`~aiida.orm.nodes.node.Node.label` returns the label of the node.
  It can also be used to *change* the label, e.g., `mynode.label = "new label"`.

*Description management:*

- {py:attr}`~aiida.orm.nodes.node.Node.description` returns the description of the node (more detailed than the label).
  It can also be used to *change* the description, e.g., `mynode.description = "new description"`.

*Comment management:*

- {py:meth}`~aiida.orm.nodes.node.Node.add_comment` adds a comment.
- {py:meth}`~aiida.orm.nodes.node.Node.get_comments` returns a sorted list of the comments.
- {py:meth}`~aiida.orm.nodes.node.Node.update_comment` updates the node comment (also via CLI: `verdi comment update`).
- {py:meth}`~aiida.orm.nodes.node.Node.remove_comment` removes the node comment (also via CLI: `verdi comment remove`).

#### Link management methods

{py:class}`~aiida.orm.nodes.node.Node` objects and objects of its subclasses can have ancestors and descendants.
These are connected with links.

- {py:meth}`~aiida.orm.nodes.node.Node.has_cached_links` shows if there are cached links to other nodes.
- {py:meth}`~aiida.orm.nodes.node.Node.add_incoming` adds a link to the current node from the `src` node with the given link label and link type.
  Depending on whether the nodes are stored or not, the link is written to the database or to the cache.
- {py:meth}`~aiida.orm.nodes.node.Node.get_incoming` returns the iterator of input nodes.
- {py:meth}`~aiida.orm.nodes.node.Node.get_outgoing` returns the iterator of output nodes.

*Listing links example:*

```ipython
In [1]: c = load_node(139168)  # Let's load a node with a specific pk

In [2]: c.get_incoming().all()
Out[2]:
[
  LinkTriple(link_type='inputlink', label='code', node=<Code: Remote code 'cp-5.1' on daint, pk: 75709, uuid: 3c9cdb7f-...>),
  LinkTriple(link_type='inputlink', label='parameters', node=<Dict: uuid: 94efe64f-... (pk: 139166)>),
  LinkTriple(link_type='inputlink', label='structure', node=<StructureData: uuid: 3096f83c-... (pk: 139001)>),
  ...
]

In [3]: c.get_outgoing().all()
Out[3]:
[
  LinkTriple(link_type='createlink', label='output_parameters', node=<Dict: uuid: f7a3ca96-... (pk: 139257)>),
  LinkTriple(link_type='createlink', label='remote_folder', node=<RemoteData: uuid: 17642a1c-... (pk: 139169)>),
  LinkTriple(link_type='createlink', label='retrieved', node=<FolderData: uuid: a9037dc0-... (pk: 139255)>),
  ...
]
```

The {py:meth}`~aiida.orm.nodes.node.Node.get_incoming` and {py:meth}`~aiida.orm.nodes.node.Node.get_outgoing` methods return a manager object that contains a collection of the incoming and outgoing links from the target node.
Each neighbor is defined by the node, the link label, and link type.
This set of three properties is referred to as a *link triple* and is implemented by the {py:class}`~aiida.orm.utils.links.LinkTriple` named tuple.

#### Attributes related methods

Each {py:class}`~aiida.orm.nodes.node.Node` object can have attributes which are properties that characterize the node.
Such properties can be the energy, the atom symbols, or the lattice vectors.
The methods for the management of the attributes are defined on the {py:class}`~aiida.orm.nodes.attributes.NodeAttributes` class.

#### Extras related methods

*Extras* are additional information that can be added to a node.
In contrast to repository files and attributes, extras are information added by the user and are not immutable, even when the node is stored.

- {py:meth}`~aiida.orm.nodes.node.Node.set_extra` and {py:meth}`~aiida.orm.nodes.node.Node.set_extra_many` add one or many new extras to the node.
- {py:meth}`~aiida.orm.nodes.node.Node.reset_extras` will replace all existing extras with a new set of extras.
- {py:meth}`~aiida.orm.nodes.node.Node.extras` is a property that returns all extras.
- {py:meth}`~aiida.orm.nodes.node.Node.get_extra` and {py:meth}`~aiida.orm.nodes.node.Node.get_extra_many` can be used to return a single or many specific extras.
- {py:meth}`~aiida.orm.nodes.node.Node.delete_extra` and {py:meth}`~aiida.orm.nodes.node.Node.delete_extra_many` delete one or multiple specific extras.
- {py:meth}`~aiida.orm.nodes.node.Node.clear_extras` will delete all existing extras.

#### Folder management

`Folder` objects represent directories on the disk (virtual or not) where extra information for the node is stored.
These folders can be temporary or permanent.

#### Store and deletion

- {py:meth}`~aiida.orm.nodes.node.Node.store_all` stores all the input nodes, then stores the current node, and finally stores the cached input links.
- {py:meth}`~aiida.orm.nodes.node.Node.verify_are_parents_stored` checks that the parents are stored.
- {py:meth}`~aiida.orm.nodes.node.Node.store` checks that the node data is valid, checks if the node's parents are stored, moves the contents of the temporary folder to the repository folder, and stores the database information in a transaction. If the transaction fails, data transferred to the repository folder is moved back to the temporary folder.

## Folders

AiiDA uses {py:class}`~aiida.common.folders.Folder` and its subclasses to add an abstraction layer between the functions and methods working directly on the file-system and AiiDA.
This is particularly useful when switching between different folder options (temporary, permanent, etc.) and storage options (plain local directories, compressed files, remote files and directories, etc.).

### Folder

This is the main class of the available `Folder` classes.
Apart from the abstraction provided to the OS operations needed by AiiDA, one of its main features is that it can restrict all the available operations within a given folder limit.

Key methods:

- {py:meth}`~aiida.common.folders.Folder.mode_dir` and {py:meth}`~aiida.common.folders.Folder.mode_file` return the mode with which folders and files should be writable.
- {py:meth}`~aiida.common.folders.Folder.get_subfolder` returns the subfolder matching the given name.
- {py:meth}`~aiida.common.folders.Folder.get_content_list` returns the contents matching a pattern.
- {py:meth}`~aiida.common.folders.Folder.insert_path` adds a file/folder to a specific location and {py:meth}`~aiida.common.folders.Folder.remove_path` removes a file/folder.
- {py:meth}`~aiida.common.folders.Folder.get_abs_path` returns the absolute path of a file/folder under a given folder and {py:meth}`~aiida.common.folders.Folder.abspath` returns the absolute path of the folder.
- {py:meth}`~aiida.common.folders.Folder.create_symlink` creates a symlink pointing to the given location inside the folder.
- {py:meth}`~aiida.common.folders.Folder.create_file_from_filelike` creates a file from the given contents.
- {py:meth}`~aiida.common.folders.Folder.open` opens a file in the folder.
- {py:meth}`~aiida.common.folders.Folder.exists` returns true or false depending on whether a folder exists.
- {py:meth}`~aiida.common.folders.Folder.isfile` and {py:meth}`~aiida.common.folders.Folder.isdir` return true or false depending on the existence of the given file/folder.
- {py:meth}`~aiida.common.folders.Folder.create` creates the folder, {py:meth}`~aiida.common.folders.Folder.erase` deletes the folder, and {py:meth}`~aiida.common.folders.Folder.replace_with_folder` copies/moves a given folder.

### SandboxFolder

{py:class}`~aiida.common.folders.SandboxFolder` objects correspond to temporary ("sandbox") folders.

- {py:meth}`~aiida.common.folders.SandboxFolder.__init__` creates a new temporary folder.
- {py:meth}`~aiida.common.folders.SandboxFolder.__exit__` destroys the folder on exit.

## Data

### Navigating inputs and outputs

- {py:meth}`~aiida.orm.Data.creator` returns either the {py:class}`~aiida.orm.CalculationNode` that created it or `None` if it was not created by a calculation.

## ProcessNode

### Navigating inputs and outputs

- {py:meth}`~aiida.orm.ProcessNode.caller` returns either the caller {py:class}`~aiida.orm.nodes.process.workflow.WorkflowNode` or `None` if it was not called by any process.

## CalculationNode

### Navigating inputs and outputs

- {py:meth}`~aiida.orm.CalculationNode.inputs` returns a {py:class}`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's incoming `INPUT_CALC` links.

  The `NodeLinksManager` can be used to quickly go from a node to a neighboring node.
  For example:

  ```ipython
  In [1]: c = load_node(139168)

  In [2]: c.inputs.
  c.inputs.code                c.inputs.parent_calc_folder  c.inputs.pseudo_O
  c.inputs.parameters          c.inputs.pseudo_Ba           c.inputs.pseudo_Ti

  In [3]: c.inputs.parent_calc_folder
  Out[3]: <RemoteData: uuid: becb4894-c50c-4779-b84f-713772eaceff (pk: 139118)>
  ```

  The `.inputs` manager for `WorkflowNode` and the `.outputs` manager for both `CalculationNode` and `WorkflowNode` work in the same way.

- {py:meth}`~aiida.orm.CalculationNode.outputs` returns a {py:class}`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's outgoing `CREATE` links.

(updatable-attributes)=
### Updatable attributes

The {py:class}`~aiida.orm.ProcessNode` class is a subclass of the {py:class}`~aiida.orm.nodes.node.Node` class, which means that its attributes become immutable once stored.
However, for a `Calculation` to be runnable it needs to be stored, but that would mean that its state, which is stored in an attribute, can no longer be updated.
To solve this issue the {py:class}`~aiida.orm.utils.mixins.Sealable` mixin is introduced.
This mixin can be used for subclasses of `Node` that need to have updatable attributes even after the node has been stored in the database.
The mixin defines the `_updatable_attributes` tuple, which defines the attributes that are considered to be mutable even when the node is stored.
It also allows the node to be *sealed*, after which even the updatable attributes become immutable.

## WorkflowNode

### Navigating inputs and outputs

- {py:meth}`~aiida.orm.nodes.process.workflow.WorkflowNode.inputs` returns a {py:class}`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's incoming `INPUT_WORK` links.
- {py:meth}`~aiida.orm.nodes.process.workflow.WorkflowNode.outputs` returns a {py:class}`~aiida.orm.utils.managers.NodeLinksManager` object that can be used to access the node's outgoing `RETURN` links.

## Changing the config.json structure

In general, changes to `config.json` should be avoided if possible.
However, if there is a need to modify it, the following procedure should be used to create a migration:

1. Determine whether the change will be backwards-compatible.
   This means that an older version of AiiDA will still be able to run with the new `config.json` structure.

2. In `aiida/manage/configuration/migrations/migrations.py`, increase the `CURRENT_CONFIG_VERSION` by one.
   If the change is **not** backwards-compatible, set `OLDEST_COMPATIBLE_CONFIG_VERSION` to the same value.

3. Write a function which transforms the old config dict into the new version.
   It is possible that you need user input for the migration, in which case this should also be handled in that function.

4. Add an entry in `_MIGRATION_LOOKUP` where the key is the version **before** the migration, and the value is a `ConfigMigration` object.
   The `ConfigMigration` is constructed from your migration function, and the **hard-coded** values of `CURRENT_CONFIG_VERSION` and `OLDEST_COMPATIBLE_CONFIG_VERSION`.
   If these values are not hard-coded, the migration will break as soon as the values are changed again.

5. Add tests for the migration.
   You can add two types of tests:

   * Tests that run the entire migration, using the `check_and_migrate_config` function.
     Make sure to run it with `store=False`, otherwise it will overwrite your `config.json` file.
   * Tests that run a single step in the migration, using the `ConfigMigration.apply` method.

## Daemon and signal handling

While the AiiDA daemon is running, interrupt signals (`SIGINT` and `SIGTERM`) are captured so that the daemon can shut down gracefully.
This is implemented using Python's `signal` module, as shown in the following example:

```python
import signal

def print_foo(*args):
    print('foo')

signal.signal(signal.SIGINT, print_foo)
```

You should be aware of this while developing code which runs in the daemon.
In particular, it's important when creating subprocesses.
When a signal is sent, the whole process group receives that signal.
As a result, the subprocess can be killed even though the Python main process captures the signal.
This can be avoided by creating a new process group for the subprocess, meaning that it will not receive the signal.
To do this, you need to pass `start_new_session=True` to the `subprocess` function:

```python
import subprocess

print(subprocess.check_output('sleep 3; echo bar', start_new_session=True))
```
