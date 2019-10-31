.. _DataTypes:

================
AiiDA data types
================

There are a number of data types distributed with AiiDA.

We summarize here the most common, and some useful features/functionalities to work with them.


Most common datatypes
---------------------

Here follows a short summary of common datatypes already provided with AiiDA. This list is not
complete, see also inside :py:mod:`aiida.orm.nodes.data` for the list of all available plugins.

We also mention, when relevant, what is stored in the database (as attributes, so that
it can be easily queried e.g. with the :ref:`QueryBuilder <UsingQueryBuilder>`) and what is
stored in the file repository (providing access to the file contents, but not efficiently
queryable: this is useful for e.g. big data files that don't need to be queried for).

For all data types, you can follow the link to the data class to read more about
the methods provided, how to access them, and so on.

If you need to work with some specific type of data, first check the list of data types/plugins
below, and if you don't find what you need, give a look to
:ref:`how to write a new data plugin <working_data_creating_new_types>`.

Base types
++++++++++
In the :py:mod:`aiida.orm.nodes.data.base` module there are a number of useful classes
that wrap base python datatypes (like :py:class:`~aiida.orm.nodes.data.int.Int`,
:py:class:`~aiida.orm.nodes.data.float.Float`, :py:class:`~aiida.orm.nodes.data.str.Str`, ...).
These are automatically loaded with the verdi shell, and also directly exposed from :py:mod:`aiida.orm`.
These classes are particularly useful when you need to provide a single parameter to e.g. a
:py:class:`~aiida.engine.processes.functions.workfunction`.

Each of these classes can most often be used transparently (e.g. you can sum two
:py:class:`~aiida.orm.nodes.data.int.Int` objects, etc.). If you need to access the bare
value and not the whole AiiDA class, use the ``.value`` property.

In the same module, there is also a :py:class:`~aiida.orm.nodes.data.list.List` class to
store a list of base data types.

The different datatypes can be accessed through the :py:func:`~aiida.plugins.factories.DataFactory` function
(also exposed from :py:mod:`aiida.plugins`) by passing an entry point to it as an argument. A list of all the data entry points
can be obtain running the command ``verdi plugin list aiida.data``.

Dict
+++++++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.dict.Dict`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``dict``
* **Aim**: store a dictionary of python base types in the database.
  It can store any dictionary where elements can be a base python type (strings, floats,
  integers, booleans, None type, datetime objects) and lists or dictionaries of them, at
  any depth level (e.g. a dictionary where a value is a list of dictionaries of
  strings and floats).
* **What is stored in the database**: all key/values pairs as attributes
* **What is stored in the file repository**: ---

StructureData
+++++++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.structure.StructureData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``structure``
* **Aim**: store a crystal structure to be used by atomistic codes
* **What is stored in the database**: all atomic positions, species, kinds,
* **What is stored in the file repository**: ---
* **Additional functionality**:

  * :ref:`Export to a number of formats (xsf, cif, ...)<ExportDataNodes>`

UpfData
+++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.upf.UpfData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``upf``
* **Aim**: store a pseudopotential in the .UPF format (e.g. used by `Quantum ESPRESSO`_ - see also the `AiiDA Quantum ESPRESSO plugin`_)
* **What is stored in the database**: the MD5 of the UPF; the element the pseudopotential
  is associated to
* **What is stored in the file repository**: the pseudopotential file

.. _Quantum ESPRESSO: http://www.quantum-espresso.org
.. _AiiDA Quantum ESPRESSO plugin: http://aiida-quantumespresso.readthedocs.io/en/latest/

ArrayData
+++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.array.ArrayData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``array``
* **Aim**: store generic numeric arrays
* **What is stored in the database**: the shape of the arrays and the name of the arrays
* **What is stored in the file repository**: the array data in numpy format

TrajectoryData
++++++++++++++
* **Class**: :py:class:`~aiida.orm.nodes.data.array.trajectory.TrajectoryData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``array.trajectory``
* **Aim**: store molecular trajectories (i.e. sequences of StructureData objects, where
  then number of atomic kinds and sites does not change over time).
  beside the coordinates, it can also optionally store velocities.
* **What is stored in the database**: like ``ArrayData``
* **What is stored in the file repository**: the array data in numpy format: cells over
  time, integer indices over time, atomic positions over time, the list of kinds, ...
* **Additional functionality**:

  * :ref:`Export to a number of formats (xsf, cif, ...)<ExportDataNodes>`

KpointsData
+++++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``array.kpoints``
* **Aim**: store grids of k-points (in reciprocal space, for crystal structures), or
  explicit list of k-points (optionally with a weight associated to each one). Can also
  associate labels to (some of the) points, which is very useful for later plottings
  band structures (and store them in ``BandsData`` objects).
* **What is stored in the database**: like ``ArrayData``, the shape of the arrays and the name of the arrays
* **What is stored in the file repository**:  like ``ArrayData``, the array data in numpy format
* **Additional functionality**:

  * :ref:`Automatically compute k-points path given a crystal structure<AutomaticKpoints>`

BandsData
+++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.array.bands.BandsData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``array.bands``
* **Aim**: store electronic structure bands (of phonon bands)
* **What is stored in the database**: like ``ArrayData``, the shape of the arrays and the name of the arrays
* **What is stored in the file repository**:  like ``ArrayData``, the array data in numpy format
* **Additional functionality**:

  * :ref:`Export to a number of formats (xmgrace, gnuplot, png, pdf, ...)<ExportDataNodes>`

XyData
++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.array.xy.XyData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``array.xy``
* **Aim**: store data for a 2D (xy) plot
* **What is stored in the database**: like ``ArrayData``, the shape of the arrays and the name of the arrays
* **What is stored in the file repository**:  like ``ArrayData``, the array data in numpy format

FolderData
++++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.folder.FolderData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``folder``
* **Aim**: store a set of files/folders (with possibly a folder/subfolder structure)
* **What is stored in the database**: ---
* **What is stored in the file repository**: all files and folders

SinglefileData
++++++++++++++
* **Class**: :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``singlefile``
* **Aim**: the same as ``FolderData``, but allows to store only one single file.
* **What is stored in the database**: the filename
* **What is stored in the file repository**: the file

RemoteData
++++++++++

* **Class**: :py:class:`~aiida.orm.nodes.data.remote.RemoteData`
* **String to pass to the** :py:func:`~aiida.plugins.factories.DataFactory`: ``remote``
* **Aim**: this basically represents a "symbolic link" to a specific folder on
  a remote computer.
  Its main use is to allow users to persist the provenance when e.g. a calculation
  produces data in a raw/scratch folder, and the whole folder needs to be provided
  to restart/continue.
* **What is stored in the database**: the path of the folder (and the remote computer
  as a `.computer` property, not as an attribute)
* **What is stored in the file repository**: ---


