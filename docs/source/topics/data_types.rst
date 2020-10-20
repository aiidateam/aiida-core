.. _topics:data_types:

**********
Data types
**********

AiiDA already ships with a number of useful data types.
This section details the most common, and some handy features/functionalities to work with them.

The different data types can be accessed through the :py:func:`~aiida.plugins.factories.DataFactory` function (also exposed from :py:mod:`aiida.plugins`) by passing the corresponding entry point as an argument, for example when working in the ``verdi shell``:

.. code-block:: ipython

  In [1]: ArrayData = DataFactory('array')

.. important::

  Many of the examples in this section will assume you are working inside the ``verdi shell``.
  If this is not the case, you will have to first load e.g. the :py:func:`~aiida.plugins.factories.DataFactory()` function:

  .. code-block:: python

    from aiida.plugins import DataFactory

    ArrayData = DataFactory('array')

A list of all the data entry points can be obtain running the command ``verdi plugin list aiida.data``.

For all data types, you can follow the link to the corresponding data class in the API reference to read more about the class and its methods. We also detail what is stored in the database (mostly as attributes, so the information can be easily queried e.g. with the :ref:`QueryBuilder <how-to:data:find>`) and what is stored as a raw file in the AiiDA file repository (providing access to the file contents, but not efficiently queryable: this is useful for e.g. big data files that don't need to be queried for).

If you need to work with some specific type of data, first check the list of data types/plugins below, and if you don't find what you need, give a look to :ref:`Adding support for custom data types <topics:data_types:plugin>`.

.. _topics:data_types:core:

Core data types
===============

Below is a list of the core data types already provided with AiiDA, along with their entry point and where the data is stored once the node is stored in the AiiDA database.

.. table::
  :widths: 20 20 45 45

  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | **Class**                                                 | **Entry point**   | **Stored in database**                            | **Stored in repository**          |
  +===========================================================+===================+===================================================+===================================+
  | :ref:`Int <topics:data_types:core:base>`                  | ``int``           | The integer value                                 | \\-                               |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`Float <topics:data_types:core:base>`                | ``float``         | The float value                                   | \\-                               |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`Str <topics:data_types:core:base>`                  | ``str``           | The string                                        | \\-                               |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`Bool <topics:data_types:core:base>`                 | ``bool``          | The boolean value                                 | \\-                               |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`List <topics:data_types:core:base:iterable>`        | ``list``          | The complete list                                 | \\-                               |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`Dict <topics:data_types:core:base:iterable>`        | ``dict``          | The complete dictionary                           | \\-                               |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`ArrayData <topics:data_types:core:array>`           | ``array``         | The array names and corresponding shapes          | The array data in ``.npy`` format |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`XyData <topics:data_types:core:array:xy>`           | ``array.xy``      | The array names and corresponding shapes          | The array data in ``.npy`` format |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`SinglefileData <topics:data_types:core:singlefile>` | ``singlefile``    | The filename                                      | The file                          |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`FolderData <topics:data_types:core:folder>`         | ``folder``        | \\-                                               | All files and folders             |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+
  | :ref:`RemoteData <topics:data_types:core:remote>`         | ``remote``        | The computer and the absolute path to the folder  | All files and folders             |
  +-----------------------------------------------------------+-------------------+---------------------------------------------------+-----------------------------------+

.. _topics:data_types:core:base:

Base types
----------

There are a number of useful classes that wrap base Python data types (:py:class:`~aiida.orm.nodes.data.int.Int`, :py:class:`~aiida.orm.nodes.data.float.Float`, :py:class:`~aiida.orm.nodes.data.str.Str`, :py:class:`~aiida.orm.nodes.data.bool.Bool`) so they can be stored in the provenance.
These are automatically loaded with the ``verdi shell``, and also directly exposed from :py:mod:`aiida.orm`.
They are particularly useful when you need to provide a single parameter to e.g. a :py:class:`~aiida.engine.processes.functions.workfunction`.

Each of these classes can most often be used in a similar way as their corresponding base type:

.. code-block:: ipython

  In [1]: total = Int(2) + Int(3)

If you need to access the bare value and not the whole AiiDA class, use the ``.value`` property:

.. code-block:: ipython

  In [2]: total.value
  Out[2]: 5

.. warning::

  While this is convenient if you need to do simple manipulations like multiplying two numbers, be very careful not to pass such nodes instead of the corresponding Python values to libraries that perform heavy computations with them.
  In fact, any operation on the value would be replaced with an operation creating new AiiDA nodes, that however can be orders of magnitude slower (see `this discussion <https://github.com/aiidateam/aiida-core/issues/3320>`_ on GitHub).
  In this case, remember to pass the node.value to the mathematical function instead.

.. _topics:data_types:core:base:iterable:

AiiDA has also implemented data classes for two basic Python iterables: :py:class:`~aiida.orm.nodes.data.list.List` and :py:class:`~aiida.orm.nodes.data.dict.Dict`. They can store any list or dictionary where elements can be a base python type (strings, floats, integers, booleans, None type):

.. code-block:: ipython

  In [1]: l = List(list=[1, 'a', False])

Note the use of the keyword argument ``list``, this is required for the constructor of the :py:class:`~aiida.orm.nodes.data.list.List` class. You can also store lists or dictionaries within the iterable, at any depth level. For example, you can create a dictionary where a value is a list of dictionaries:

.. code-block:: ipython

  In [2]: d = Dict(dict={'k': 0.1, 'l': [{'m': 0.2}, {'n': 0.3}]})

To obtain the Python ``list`` or ``dictionary`` from a :py:class:`~aiida.orm.nodes.data.list.List` or :py:class:`~aiida.orm.nodes.data.dict.Dict` instance, you have to use the :py:meth:`~aiida.orm.nodes.data.list.List.get_list()` or :py:meth:`~aiida.orm.nodes.data.dict.Dict.get_dict()` methods:

.. code-block:: ipython

  In [3]: l.get_list()
  Out[3]: [1, 'a', False]

  In [4]: d.get_dict()
  Out[4]: {'k': 0.1, 'l': [{'m': 0.2}, {'n': 0.3}]}

However, you can also use the list index or dictionary key to extract specific values:

.. code-block:: ipython

  In [5]: l[1]
  Out[5]: 'a'

  In [6]: d['k']
  Out[6]: 0.1

You can also use many methods of the corresponding Python base type, for example:

.. code-block:: ipython

  In [7]: l.append({'b': True})

  In [8]: l.get_list()
  Out[8]: [1, 'a', False, {'b': True}]

For all of the base data types, their value is stored in the database in the attributes column once you store the node using the :py:meth:`~aiida.orm.nodes.node.Node.store()` method.

.. warning::

  The :py:class:`~aiida.orm.nodes.data.list.List` and :py:class:`~aiida.orm.nodes.data.dict.Dict` only store the Python base types, not the corresponding AiiDA data type.
  These will be converted to their corresponding Python base type when storing the :py:class:`~aiida.orm.nodes.data.list.List` or :py:class:`~aiida.orm.nodes.data.dict.Dict` node in the database.

.. _topics:data_types:core:array:

ArrayData
---------

The :py:class:`~aiida.orm.nodes.data.array.ArrayData` class can be used to represent `numpy <https://numpy.org/>`_ arrays in the provenance.
Each array is assigned to a name specified by the user using the :py:meth:`~aiida.orm.nodes.data.array.ArrayData.set_array()` method:

.. code-block:: ipython

  In [1]: SinglefileData = DataFactory('singlefile'); import numpy as np

  In [2]: array = ArrayData()

  In [3]: array.set_array('matrix', np.array([[1, 2], [3, 4]]))

Note that one :py:class:`~aiida.orm.nodes.data.array.ArrayData` instance can store multiple arrays under different names:

.. code-block:: ipython

  In [4]: array.set_array('vector', np.array([[1, 2, 3, 4]]))

To see the list of array names stored in the :py:class:`~aiida.orm.nodes.data.array.ArrayData` instance, you can use the :py:meth:`~aiida.orm.nodes.data.array.ArrayData.get_arraynames()` method:

.. code-block:: ipython

  In [5]: array.get_arraynames()
  Out[5]: ['matrix', 'vector']

If you want the array corresponding to a certain name, simply supply the name to the :py:meth:`~aiida.orm.nodes.data.array.ArrayData.get_array()` method:

.. code-block:: ipython

  In [6]: array.get_array('matrix')
  Out[6]:
  array([[1, 2],
        [3, 4]])

As with all nodes, you can store the :py:class:`~aiida.orm.nodes.data.array.ArrayData` node using the :py:meth:`~aiida.orm.nodes.node.Node.store()` method. However, only the names and shapes of the arrays are stored to the database, the content of the arrays is stored to the repository in the `numpy format <https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html#npy-format>`_ (``.npy``).

.. _topics:data_types:core:array:xy:

XyData
------

In case you are working with arrays that have a relationship with each other, i.e. ``y`` as a function of ``x``, you can use the :py:class:`~aiida.orm.nodes.data.array.XyData` class:

.. code-block:: ipython

  In [1]: XyData = DataFactory('array.xy'); import numpy as np

  In [2]: xy = XyData()

This class is equipped with setter and getter methods for the ``x`` and ``y`` values specifically, and takes care of some validation (e.g. check that they have the same shape).
The user also has to specify the units for both ``x`` and ``y``:

.. code-block:: ipython

  In [3]: xy.set_x(np.array([10, 20, 30, 40]), 'Temperate', 'Celsius')

  In [4]: xy.set_y(np.array([1, 2, 3, 4]), 'Volume Expansion', '%')

Note that you can set multiple ``y`` values that correspond to the ``x`` grid.
Same as for the :py:class:`~aiida.orm.nodes.data.array.ArrayData`, the names and shapes of the arrays are stored to the database, the content of the arrays is stored to the repository in the `numpy format <https://numpy.org/doc/stable/reference/generated/numpy.lib.format.html#npy-format>`_ (``.npy``).

.. _topics:data_types:core:singlefile:

SinglefileData
--------------

In order to include a single file in the provenance, you can use the :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData` class.
This class can be initialized via the **absolute** path to the file you want to store:

.. code-block:: ipython

  In [1]: SinglefileData = DataFactory('singlefile')

  In [2]: single_file = SinglefileData('/absolute/path/to/file')

The contents of the file in string format can be obtained using the :py:meth:`~aiida.orm.nodes.data.singlefile.SinglefileData.get_content()` method:

.. code-block:: ipython

  In [3]: single_file.get_content()
  Out[3]: 'The file content'

When storing the node, the filename is stored in the database and the file itself is copied to the repository.

.. _topics:data_types:core:folder:

FolderData
----------

The :py:class:`~aiida.orm.nodes.data.folder.FolderData` class stores sets of files and folders (including its subfolders).
To store a complete directory, simply use the ``tree`` keyword:

.. code-block:: ipython

  In [1]: FolderData = DataFactory('folder')

  In [2]: folder = FolderData(tree='/absolute/path/to/directory')

Alternatively, you can construct the node first and then use the various repository methods to add objects from directory and file paths:

.. code-block:: ipython

  In [1]: folder = FolderData()

  In [2]: folder.put_object_from_tree('/absolute/path/to/directory')

  In [3]: folder.put_object_from_file('/absolute/path/to/file1.txt', path='file1.txt')

or from `file-like objects <https://docs.python.org/3/glossary.html#term-file-like-object>`_:

.. code-block:: ipython

  In [4]: folder.put_object_from_filelike(filelike_object, path='file2.txt')

Inversely, the content of the files stored in the :py:class:`~aiida.orm.nodes.data.folder.FolderData` node can be accessed using the :py:class:`~aiida.orm.nodes.node.Node.get_object_content()` method:

.. code-block:: ipython

  In [5]: folder.get_object_content('file1.txt')
  Out[5]: 'File 1 content\n'

To see the files that are stored in the :py:class:`~aiida.orm.nodes.data.folder.FolderData`, you can use the :py:class:`~aiida.orm.nodes.node.Node.list_object_names()` method:

.. code-block:: ipython

  In [6]: folder.list_object_names()
  Out[6]: ['subdir', 'file1.txt', 'file2.txt']

In this example, ``subdir`` was a sub directory of ``/absolute/path/to/directory``, whose contents where added above.
to list the contents of the ``subdir`` directory, you can pass its path to the :py:meth:`~aiida.orm.nodes.node.Node.list_object_names()` method:

.. code-block:: ipython

  In [7]: folder.list_object_names('subdir')
  Out[7]: ['file3.txt', 'module.py']

The content can once again be shown using the :py:meth:`~aiida.orm.nodes.node.Node.get_object_content()` method by passing the correct path:

.. code-block:: ipython

 In [8]: folder.get_object_content('subdir/file3.txt')
 Out[8]: 'File 3 content\n'

Since the :py:class:`~aiida.orm.nodes.data.folder.FolderData` node is simply a collection of files, it simply stores these files in the repository

.. _topics:data_types:core:remote:

RemoteData
----------

The :py:class:`~aiida.orm.nodes.data.remote.RemoteData` node represents a "symbolic link" to a specific folder on a remote computer.
Its main use is to allow users to persist the provenance when e.g. a calculation produces data in a raw/scratch folder, and the whole folder needs to be provided to restart/continue.
To create a :py:class:`~aiida.orm.nodes.data.remote.RemoteData` instance, simply pass the remote path to the folder and the computer on which it is stored:

.. code-block:: ipython

  In [1]: RemoteData = DataFactory('remote')

  In [2]: computer = load_computer(label='computer_label')

  In [3]: remote = RemoteData(remote_path='/absolute/path/to/remote/directory' computer=local)

You can see the contents of the remote folder by using the :py:meth:`~aiida.orm.nodes.data.remote.RemoteData.listdir()` method:

.. code-block:: ipython

  In [4]: remote.listdir()
  Out[4]: ['file2.txt', 'file1.txt', 'subdir']

To see the contents of a subdirectory, pass the relative path to the :py:meth:`~aiida.orm.nodes.data.remote.RemoteData.listdir()` method:

.. code-block:: ipython

  In [5]: remote.listdir('subdir')
  Out[5]: ['file3.txt', 'module.py']

.. todo::

  .. _topics:data_types:core:code:

  title: Code

.. _topics:data_types:materials:

Materials science data types
============================

Since AiiDA was first developed within the computational materials science community, `aiida-core` still contains several data types specific to this field.
This sections lists these data types and provides some important examples of their usage.

.. table::
  :widths: 20 20 55 35

  +-------------------------------------------------------------------+----------------------+---------------------------------------------------------------------------------+-----------------------------------+
  | **Class**                                                         | **Entry point**      | **Stored in database**                                                          | **Stored in repository**          |
  +===================================================================+======================+=================================================================================+===================================+
  | :ref:`StructureData <topics:data_types:materials:structure>`      | ``structure``        | The cell, periodic boundary conditions, atomic positions, species and kinds.    |  \\-                              |
  +-------------------------------------------------------------------+----------------------+---------------------------------------------------------------------------------+-----------------------------------+
  | :ref:`TrajectoryData <topics:data_types:materials:trajectory>`    | ``array.trajectory`` | The structure species and the shape of the cell, step and position arrays.      | The array data in numpy format.   |
  +-------------------------------------------------------------------+----------------------+---------------------------------------------------------------------------------+-----------------------------------+
  | :ref:`UpfData <topics:data_types:materials:upf>`                  | ``upf``              | The MD5 of the UPF and the element of the pseudopotential.                      | The pseudopotential file.         |
  +-------------------------------------------------------------------+----------------------+---------------------------------------------------------------------------------+-----------------------------------+
  | :ref:`KpointsData <topics:data_types:materials:kpoints>`          | ``array.kpoints``    | (as mesh) The mesh and offset.                                                  | \\-                               |
  |                                                                   |                      |                                                                                 |                                   |
  |                                                                   |                      | (as list) The "kpoints" array shape, labels and their indices.                  | The array data in numpy format.   |
  +-------------------------------------------------------------------+----------------------+---------------------------------------------------------------------------------+-----------------------------------+
  | :ref:`BandsData <topics:data_types:materials:bands>`              | ``array.bands``      | The units, labels and their numbers, and shape of the bands and kpoints arrays. | The array data in numpy format.   |
  +-------------------------------------------------------------------+----------------------+---------------------------------------------------------------------------------+-----------------------------------+

.. _topics:data_types:materials:structure:

StructureData
-------------

The :py:class:`~aiida.orm.nodes.data.structure.StructureData` data type represents a structure, i.e. a collection of sites defined in a cell.
The boundary conditions are periodic by default, but can be set to non-periodic in any direction.

As an example, say you want to create a :py:class:`~aiida.orm.nodes.data.structure.StructureData` instance for bcc Li.
Let's begin with creating the instance by defining its unit cell:

.. code-block:: ipython

  In [1]: StructureData = DataFactory('structure')

  In [2]: unit_cell = [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]

  In [3]: structure = StructureData(cell=unit_cell)

.. note::

    Default units for crystal structure cell and atomic coordinates in AiiDA are Å (Ångström).

Next, you can add the Li atoms to the structure using the :py:class:`~aiida.orm.nodes.data.structure.StructureData.append_atom()` method:

.. code-block:: ipython

  In [4]: structure.append_atom(position=(0.0, 0.0, 0.0), symbols="Li")

  In [5]: structure.append_atom(position=(1.5, 1.5, 1.5), symbols="Li")

You can check if the cell and sites have been set up properly by checking the ``cell`` and ``sites`` properties:

.. code-block:: ipython

  In [6]: structure.cell
  Out[6]: [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]

  In [7]: structure.sites
  Out[7]: [<Site: kind name 'Li' @ 0.0,0.0,0.0>, <Site: kind name 'Li' @ 1.5,1.5,1.5>]

From the :py:class:`~aiida.orm.nodes.data.structure.StructureData` node you can also obtain the formats of well-known materials science Python libraries such as `the Atomic Simulation Environment <https://wiki.fysik.dtu.dk/ase/index.html>`_ (ASE) and `pymatgen <https://pymatgen.org/index.html>`_:

.. code-block:: ipython

  In [8]: structure.get_ase()
  Out[8]: Atoms(symbols='Li2', pbc=True, cell=[3.5, 3.5, 3.5], masses=...)

  In [9]: structure.get_pymatgen()
  Out[9]:
  Structure Summary
  Lattice
      abc : 3.5 3.5 3.5
  angles : 90.0 90.0 90.0
  volume : 42.875
        A : 3.5 0.0 0.0
        B : 0.0 3.5 0.0
        C : 0.0 0.0 3.5
  PeriodicSite: Li (0.0000, 0.0000, 0.0000) [0.0000, 0.0000, 0.0000]
  PeriodicSite: Li (1.5000, 1.5000, 1.5000) [0.4286, 0.4286, 0.4286]

Exporting
^^^^^^^^^

The following export formats are available for :py:class:`~aiida.orm.nodes.data.structure.StructureData`:

* ``xsf`` (format supported by e.g. XCrySDen and other visualization software;
  supports periodic cells)
* ``xyz`` (classical xyz format, does not typically support periodic cells (even if
  the cell is indicated in the comment line)
* ``cif`` (export to CIF format, without symmetry reduction, i.e. always storing the
  structure as P1 symmetry)

The node can be exported using the verdi CLI, for example:

.. code-block:: console

    $ verdi data structure export --format xsf <IDENTIFIER> > Li.xsf

Where ``<IDENTIFIER>`` is one of the possible identifiers of the node, e.g. its PK or UUID.
This outputs the structure in ``xsf`` format and writes it to a file.

.. _topics:data_types:materials:trajectory:

TrajectoryData
--------------

The :py:class:`~aiida.orm.nodes.data.array.trajectory.TrajectoryData` data type represents a sequences of StructureData objects, where the number of atomic kinds and sites does not change over time.
Beside the coordinates, it can also optionally store velocities.
If you have a list of :py:class:`~aiida.orm.nodes.data.structure.StructureData` instances called ``structure_list`` that represent the trajectory of your system, you can create a :py:class:`~aiida.orm.nodes.data.array.trajectory.TrajectoryData` instance from this list:

.. code-block:: ipython

  In [1]: TrajectoryData = DataFactory('array.trajectory')

  In [2]: trajectory = TrajectoryData(structure_list)

Exporting
^^^^^^^^^

You can export the py:class:`~aiida.orm.nodes.data.array.trajectory.TrajectoryData` node with ``verdi data trajectory export``, which accepts a number of formats including ``xsf`` and  ``cif``, and additional parameters like ``--step NUM`` (to choose to export only a given trajectory step).

The following export formats are available:

* ``xsf`` (format supported by e.g. XCrySDen and other visualization software;
  supports periodic cells)
* ``cif`` (export to CIF format, without symmetry reduction, i.e. always storing the
  structures as P1 symmetry)

.. todo::

  Think of more example use cases.

.. _topics:data_types:materials:upf:

UpfData
-------

The :py:class:`~aiida.orm.nodes.data.upf.UpfData` data type represents a pseudopotential in the .UPF format (e.g. used by `Quantum ESPRESSO`_ - see also the `AiiDA Quantum ESPRESSO plugin`_).
Usually these will be installed as part of a pseudopotential family, for example via the `aiida-pseudo <https://github.com/aiidateam/aiida-pseudo>`_ package.

To see the pseudopotential families that have been installed in your AiiDA profile, you can use the verdi CLI:

.. code-block:: console

  $ verdi data upf listfamilies
  Success: * SSSP_v1.1_precision_PBE [85 pseudos]
  Success: * SSSP_v1.1_efficiency_PBE [85 pseudos]

.. _Quantum ESPRESSO: http://www.quantum-espresso.org
.. _AiiDA Quantum ESPRESSO plugin: http://aiida-quantumespresso.readthedocs.io/en/latest/

.. _topics:data_types:materials:kpoints:

KpointsData
-----------

The :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData` data type represents either a grid of k-points (in reciprocal space, for crystal structures), or explicit list of k-points (optionally with a weight associated to each one).

To create a :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData` instance that describes a regular (2 x 2 x 2) mesh of k-points, execute the following set of commands in the ``verdi shell``:

.. code-block:: ipython

  In [1]: KpointsData = DataFactory('array.kpoints')
     ...: kpoints_mesh = KpointsData()
     ...: kpoints_mesh.set_kpoints_mesh([2, 2, 2])

This will create a (2 x 2 x 2) mesh centered at the Gamma point (i.e. without offset).

Alternatively, you can also define a :py:class:`~aiida.orm.nodes.data.array.kpoints.KpointsData` node from a list of k-points using the :py:meth:`~aiida.orm.nodes.data.array.kpoints.KpointsData.set_kpoints()` method:

.. code-block:: ipython

  In [2]: kpoints_list = KpointsData()
     ...: kpoints_list.set_kpoints([[0, 0, 0], [0.5, 0.5, 0.5]])

In this case, you can also associate labels to (some of the) points, which is very useful for generating plots of the band structure (and storing them in a :py:class:`~aiida.orm.nodes.data.array.bands.BandsData` instance):

.. code-block:: ipython

  In [3]: kpoints_list.labels = [[0, "G"]]

  In [4]: kpoints_list.labels
  Out[4]: [(0, 'G')]

.. _topics:data_types:materials:kpoints:automatic:

Automatic computation of k-point paths
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

AiiDA provides a number of tools and wrappers to automatically compute k-point paths given a cell or a crystal structure.

The main interface is provided by the two methods :py:func:`aiida.tools.data.array.kpoints.get_kpoints_path` and :py:func:`aiida.tools.data.array.kpoints.get_explicit_kpoints_path`.

These methods are also conveniently exported directly as, e.g., ``aiida.tools.get_kpoints_path``.

The difference between the two methods is the following:

- :py:func:`~aiida.tools.data.array.kpoints.get_kpoints_path` returns a dictionary of k-point coordinates (e.g. ``{'GAMMA': [0. ,0. ,0. ], 'X': [0.5, 0., 0.], 'L': [0.5, 0.5, 0.5]}``, and then a list of tuples of endpoints of each segment, e.g. ``[('GAMMA', 'X'), ('X', 'L'), ('L', 'GAMMA')]`` for the :math:`\Gamma-X-L-\Gamma` path.
- :py:func:`~aiida.tools.data.array.kpoints.get_explicit_kpoints_path`, instead, returns a list of kpoints that follow that path, with some predefined (but user-customizable) distance between points, e.g. something like ``[[0., 0., 0.], [0.05, 0., 0.], [0.1, 0., 0.], ...]``.

Depending on how the underlying code works, one method might be preferred on the other.

The docstrings of the methods describe the expected parameters.
The general interface requires always a ``StructureData`` as the first parameter ``structure``, as well as a string for the method to use (by default this is `seekpath <https://github.com/giovannipizzi/seekpath/>`_, but also the ``legacy`` method implemented in earlier versions of AiiDA is available; see description below).

Additional parameters are passed as ``kwargs`` to the underlying implementation, that often accepts a different number of parameters.

.. _topics:data_types:materials:kpoints:seekpath:

Seekpath implementation
^^^^^^^^^^^^^^^^^^^^^^^

When specifying ``method='seekpath'``, the `seekpath <https://github.com/giovannipizzi/seekpath/>`_ library is used to generate the path.
Note that this requires  ``seekpath`` to be installed (this is not available by default, in order to reduce the dependencies of AiiDA core, but can be easily installed using ``pip install seekpath``).

For a full description of the accepted parameters, we refer to the docstring of the underlying methods :py:func:`aiida.tools.data.array.kpoints.seekpath.get_explicit_kpoints_path` and :py:func:`aiida.tools.data.array.kpoints.seekpath.get_kpoints_path`, and for more general information to the `seekpath documentation <https://seekpath.readthedocs.io/>`_.

If you use this implementation, please cite the `Hinuma paper <https://doi.org/10.1016/j.commatsci.2016.10.015>`_::

  Y. Hinuma, G. Pizzi, Y. Kumagai, F. Oba, I. Tanaka,
  Band structure diagram paths based on crystallography,
  Comp. Mat. Sci. 128, 140 (2017)
  DOI: 10.1016/j.commatsci.2016.10.015

.. dropdown:: Legacy implementation

  This refers to the implementation that has been available since the early versions of AiiDA.

  .. note:: In the 3D case (all three directions have periodic boundary conditions), this implementation expects that the structure is already standardized according to the Setyawan paper (see journal reference below).
    If this is not the case, the kpoints and band structure returned will be incorrect.
    The only case that is dealt correctly by the library is the case when axes are swapped, where the library correctly takes this swapping/rotation into account to assign kpoint labels and coordinates.

    We therefore suggest that you use the seekpath implementation, that is able to automatically correctly identify the standardized crystal structure (primitive and conventional) as described in the `Hinuma paper <https://doi.org/10.1016/j.commatsci.2016.10.015>`_.

  For a full description of the accepted parameters, we refer to the docstring of the underlying methods :py:func:`aiida.tools.data.array.kpoints.legacy.get_explicit_kpoints_path` and :py:func:`aiida.tools.data.array.kpoints.legacy.get_kpoints_path`, and for more general information to the `seekpath documentation <https://seekpath.readthedocs.io/>`_.

  If you use this implementation, please cite the correct reference from the following ones:

  - The 3D implementation is based on the `Setyawan paper <https://doi.org/10.1016/j.commatsci.2010.05.010>`_::

      W. Setyawan, S. Curtarolo,
      High-throughput electronic band structure calculations: Challenges and tools,
      Comp. Mat. Sci. 49, 299 (2010)
      DOI: 10.1016/j.commatsci.2010.05.010

  - The 2D implementation is based on the `Ramirez paper <https://doi.org/10.1002/qua.560300306>`_::

      R. Ramirez and M. C. Bohm,
      Simple geometric generation of special points in brillouin-zone integrations. Two-dimensional bravais lattices
      Int. J. Quant. Chem., XXX, 391-411 (1986)
      DOI: 10.1002/qua.560300306

.. _topics:data_types:materials:bands:

BandsData
---------

The :py:class:`~aiida.orm.nodes.data.array.bands.BandsData` data type is dedicated to store band structures of different types (electronic bands, phonons, or any other band-structure-like quantity that is a function of the k-points in the Brillouin zone).
In this section we describe the usage of the ``BandsData`` to store the  electronic band structure of silicon and some logic behind its methods.
The dropdown panels below explain some expanded use cases on how to create a :py:class:`~aiida.orm.nodes.data.array.bands.BandsData` node and plot the band structure.

.. dropdown:: Creating a ``BandsData`` instance manually

  To start working with the :py:class:`~aiida.orm.nodes.data.array.bands.BandsData` data type we should import it using the ``DataFactory`` and create an object of type ``BandsData``:

  .. code-block:: python

    from aiida.plugins import DataFactory
    BandsData = DataFactory('array.bands')
    bands_data = BandsData()

  To import the bands we need to make sure to have two arrays: one containing kpoints and another containing bands.
  The shape of the kpoints object should be ``nkpoints * 3``, while the shape of the bands should be ``nkpoints * nstates``.
  Let's assume the number of kpoints is 12, and the number of states is 5.
  So the kpoints and the bands array will look as follows:

  .. code-block:: python

    import numpy as np
    kpoints = np.array(
          [[0.    , 0.    , 0.    ], # array shape is 12 * 3
          [0.1   , 0.    , 0.1   ],
          [0.2   , 0.    , 0.2   ],
          [0.3   , 0.    , 0.3   ],
          [0.4   , 0.    , 0.4   ],
          [0.5   , 0.    , 0.5   ],
          [0.5   , 0.    , 0.5   ],
          [0.525 , 0.05  , 0.525 ],
          [0.55  , 0.1   , 0.55  ],
          [0.575 , 0.15  , 0.575 ],
          [0.6   , 0.2   , 0.6   ],
          [0.625 , 0.25  , 0.625 ]])

    bands = np.array(
      [[-5.64024889,  6.66929678,  6.66929678,  6.66929678,  8.91047649], # array shape is 12 * 5, where 12 is the size of the kpoints mesh
      [-5.46976726,  5.76113772,  5.97844699,  5.97844699,  8.48186734],  # and 5 is the numbe of states
      [-4.93870761,  4.06179965,  4.97235487,  4.97235488,  7.68276008],
      [-4.05318686,  2.21579935,  4.18048674,  4.18048675,  7.04145185],
      [-2.83974972,  0.37738276,  3.69024464,  3.69024465,  6.75053465],
      [-1.34041116, -1.34041115,  3.52500177,  3.52500178,  6.92381041],
      [-1.34041116, -1.34041115,  3.52500177,  3.52500178,  6.92381041],
      [-1.34599146, -1.31663872,  3.34867603,  3.54390139,  6.93928289],
      [-1.36769345, -1.24523403,  2.94149041,  3.6004033 ,  6.98809593],
      [-1.42050683, -1.12604118,  2.48497007,  3.69389815,  7.07537154],
      [-1.52788845, -0.95900776,  2.09104321,  3.82330632,  7.20537566],
      [-1.71354964, -0.74425095,  1.82242466,  3.98697455,  7.37979746]])

  To insert kpoints and bands in the ``bands_data`` object we should employ ``set_kpoints()`` and ``set_bands()`` methods:

  .. code-block:: python

    bands_data.set_kpoints(kpoints)
    bands_data.set_bands(bands, units='eV')

.. dropdown:: Plotting the band structure

  Next we want to visualize the band structure.
  Before doing so, one thing that we may want to add is the array of kpoint labels:

  .. code-block:: python

    labels = [(0, 'GAMMA'),
              (5, 'X'),
              (6, 'X'),
              (11, 'U')]

    bands_data.labels = labels
    bands_data.show_mpl() # to visualize the bands

  The resulting band structure will look as follows

  .. figure:: include/bands.png

  .. warning::

    As with any AiiDA node, once the ``bands_data`` object is stored (``bands_data.store()``) it won't accept any modifications.

  You may notice that depending on how you assign the kpoints labels the output of the ``show_mpl()`` method looks different.
  Please compare:

  .. code-block:: python

      bands_data.labels = [(0, 'GAMMA'),
                (5, 'X'),
                (6, 'Y'),
                (11, 'U')]
      bands_data.show_mpl()

      bands_data.labels = [(0, 'GAMMA'),
                (5, 'X'),
                (7, 'Y'),
                (11, 'U')]
      bands_data.show_mpl()

  In the first case two neighboring kpoints with ``X`` and ``Y`` labels will look like ``X|Y``, while in the second case they will be separated by a certain distance.
  The logic behind such a difference is the following.
  In the first case the plotting method discovers the two neighboring kpoints and assumes them to be a discontinuity point in the band structure (e.g. Gamma-X|Y-U).
  In the second case the kpoints labelled ``X`` and ``Y`` are not neighbors anymore, so they are plotted with a certain distance between them.
  The intervals between the kpoints on the X axis are proportional to the cartesian distance between them.

.. dropdown:: Dealing with spins

  The ``BandsData`` object can also deal with the results of spin-polarized calculations.
  Two provide different bands for two different spins you should just merge them in one array and import them again using the ``set_bands()`` method:

  .. code-block:: python

      bands_spins = [bands, bands-0.3] # to distinguish the bands of different spins we substitute 0.3 from the second band structure
      bands_data.set_bands(bands_spins, units='eV')
      bands_data.show_mpl()

  Now the shape of the bands array becomes ``nspins * nkpoints * nstates``

.. dropdown:: Exporting

  The :py:class:`~aiida.orm.nodes.data.array.bands.BandsData` data type can be exported with ``verdi data bands export``, which accepts a number of formats including (see also below) and additional parameters like ``--prettify-format FORMATNAME``, see valid formats below, or ``--y-min-lim``, ``--y-max-lim`` to specify the ``y``-axis limits.

  The following export formats are available:

  * ``agr``: export a Xmgrace .agr file with the band plot
  * ``agr_batch``: export a Xmgrace batch file together with an independent .dat file
  * ``dat_blocks``: export a .dat file, where each line has a data point (xy) and bands are separated in blocks with empty lines.
  * ``dat_multicolumn``: export a .dat file, where each line has all the values for a given x coordinate: ``x y1 y2 y3 y4 ...`` (``x`` being a linear coordinate along the band path and ``yN`` being the band energies).
  * ``gnuplot``: export a gnuplot file, together with a .dat file.
  * ``json``: export a json file with the bands divided into segments.
  * ``mpl_singlefile``: export a python file that when executed shows a plot using the ``matplotlib`` module.
    All data is included in the same python file as a multiline string containing the data in json format.
  * ``mpl_withjson``: As above, but the json data is stored separately in a different file.
  * ``mpl_pdf``: As above, but after creating the .py file it runs it to export the band structure in a PDF file (vectorial).
    **NOTE**: it requires that you have the python ``matplotlib`` module installed.
    If ``use_latex`` is true, it requires that you have LaTeX installed on your system to typeset the labels, as well as the ``dvipng`` binary.
  * ``mpl_png``: As above, but after creating the .py file it runs it to export the band structure in a PDF file (vectorial).
    **NOTE**: this format has the same dependencies as the ``mpl_pdf`` format above.

  AiiDA provides a number of functions to "prettify" the labels of band structures (if labels are present in the data node), i.e., replace ``GAMMA`` with :math:`\Gamma` or ``K_1`` with :math:`K_{1}` for instance.
  This makes sense for some output formats (e.g. Xmgrace, Gnuplot, matplotlib).

  The prettifier functions are defined as methods of the :py:class:`~aiida.common.utils.Prettifier` class and can be obtained calling :py:meth:`Prettifier.get_prettifiers()<aiida.common.utils.Prettifier.get_prettifiers>`.

  The prettifiers should be chosen depending on two aspects:

  1. How the raw labels are stored in the database.
     Two types exist currently: ``seekpath``, as used in the ``seekpath`` module, where Greek letters are written explicitly (e.g. ``GAMMA``) and underscores are used to indicate a subscript (``K_1``); and the "old" ``simple`` format, where :math:`\Gamma` is indicated with ``G`` and there is no underscore symbol).

  2. Depending on the output format: xmgrace has a specific syntax for Greek letters and subscripts, matplotlib uses LaTeX syntax, etc.

  Most export formats already decide which prettifier is best to use, but if you need
  to change it, you can do it passing the ``prettify_format`` parameter to the
  :py:meth:`~aiida.orm.nodes.data.data.Data.export()` method.
  Valid prettifiers include:

  * ``agr_seekpath``: format for Xmgrace, using ``seekpath`` raw label syntax.
  * ``agr_simple``: format for Xmgrace, using ``simple`` raw label syntax.
  * ``latex_simple``: format for LaTeX (including dollar signs), using ``seekpath`` raw label syntax.
  * ``latex_seekpath``: format for LaTeX (including dollar signs), using ``simple`` raw label syntax.
  * ``gnuplot_simple``: format for GNUPlot (Unicode for Greek letters, LaTeX syntax `without` dollar signs for underscores), using ``seekpath`` raw label syntax.
  * ``gnuplot_seekpath``: format for GNUPlot (Unicode for Greek letters, LaTeX syntax `without` dollar signs for underscores), using ``simple`` raw label syntax.
  * ``pass``: no-op prettifier: leaves all strings unchanged to their raw value.

.. todo::

  .. _topics:data_types:materials:cif:

  title: CifData

  .. _topics:data_types:materials:orbital:

  title: OrbitalData

  .. _topics:data_types:materials:projection:

  title: ProjectionData

.. _topics:data_types:export:

Exporting data nodes
====================

Next to the CLI commands described above, each data node has a :py:meth:`~aiida.orm.nodes.data.data.Data.export()` method that allows to export the given data node to file in a variety of available formats, e.g. to pass it to a visualization software.

The :py:meth:`~aiida.orm.nodes.data.data.Data.export()` method asks for a filename, and it will write to file the result.
It is possible that more than one file is written (for example, if you produce a gnuplot script, the data will typically be in a different .dat file).
The return value of the function is a list of files that have been created.

The list of export formats depends on the specific Data plugin.
The export format is typically inferred from the file extension, but if this is not possible (or you want to specify a given format), you can pass an additional ``fileformat`` parameter to :py:meth:`~aiida.orm.nodes.data.data.Data.export()`.
The list of all valid export formats can be obtained calling ``Data.get_export_formats()`` method, that returns a list of strings with all valid formats.

If you don't want to export directly to a file, but want to get simply the content of the file as a string, then you can call the :py:meth:`~aiida.orm.nodes.data.data.Data._exportcontent()` method, passing also a ``fileformat`` parameter.
The return value is a tuple of length 2: the first element is a string with the content of the "main" file, while the second is a dictionary (possibly empty) with a list of additional files that should be created/needed: the keys are filenames, and the values are the files content.

.. _topics:data_types:plugin:

Adding support for custom data types
====================================

The nodes in the :ref:`provenance graph<topics:provenance>` that are the inputs and outputs of processes are referred to as `data` and are represented by :class:`~aiida.orm.nodes.data.data.Data` nodes.
Since data can come in all shapes and forms, the :class:`~aiida.orm.nodes.data.data.Data` class can be sub classed.
AiiDA ships with some basic data types such as the :class:`~aiida.orm.nodes.data.int.Int` which represents a simple integer and the :class:`~aiida.orm.nodes.data.dict.Dict`, representing a dictionary of key-value pairs.
There are also more complex data types such as the :class:`~aiida.orm.nodes.data.array.array.ArrayData` which can store multidimensional arrays of numbers.
These basic data types serve most needs for the majority of applications, but more specific solutions may be useful or even necessary.
In the next sections, we will explain :ref:`how a new data type can be created<topics:data_types:plugin:create>` and what :ref:`guidelines<topics:data_types:plugin:design-guidelines>` should ideally be observed during the design process.

.. _topics:data_types:plugin:create:

Creating a data plugin
----------------------

Creating a new data type is as simple as creating a new sub class of the base :class:`~aiida.orm.nodes.data.data.Data` class.

.. code-block:: python

    from aiida.orm import Data

    class NewData(Data):
        """A new data type that wraps a single value."""

At this point, our new data type does nothing special.
Typically, one creates a new data type to represent a specific type of data.
For the purposes of this example, let's assume that the goal of our ``NewData`` type is to store a single numerical value.
To allow one to construct a new ``NewData`` data node with the desired ``value``, for example:

.. code-block:: python

    node = NewData(value=5)

we need to allow passing that value to the constructor of the node class.
Therefore, we have to override the constructor :meth:`~aiida.orm.nodes.node.Node.__init__`:

.. code-block:: python

    from aiida.orm import Data

    class NewData(Data):
        """A new data type that wraps a single value."""

        def __init__(self, **kwargs):
            value = kwargs.pop('value')
            super().__init__(**kwargs)
            self.set_attribute('value', value)

.. warning::

    For the class to function properly, the signature of the constructor **cannot be changed** and the constructor of the parent class **has to be called**.

Before calling the constructor of the base class, we have to remove the ``value`` keyword from the keyword arguments ``kwargs``, because the base class will not expect it and will raise an exception if left in the keyword arguments.
The final step is to actually *store* the value that is passed by the caller of the constructor.
A new node has two locations to permanently store any of its properties:

    * the database
    * the file repository

The section on :ref:`design guidelines<topics:data_types:plugin:design-guidelines>` will go into more detail what the advantages and disadvantages of each option are and when to use which.
For now, since we are storing only a single value, the easiest and best option is to use the database.
Each node has *attributes* that can store any key-value pair, as long as the value is JSON serializable.
By adding the value to the node's attributes, they will be queryable in the database once an instance of the ``NewData`` node is stored.

.. code-block:: python

    node = NewData(value=5)   # Creating new node instance in memory
    node.set_attribute('value', 6)  # While in memory, node attributes can be changed
    node.store()  # Storing node instance in the database

After storing the node instance in the database, its attributes are frozen, and ``node.set_attribute('value', 7)`` will fail.
By storing the ``value`` in the attributes of the node instance, we ensure that that ``value`` can be retrieved even when the node is reloaded at a later point in time.

Besides making sure that the content of a data node is stored in the database or file repository, the data type class can also provide useful methods for users to retrieve that data.
For example, with the current state of the ``NewData`` class, in order to retrieve the ``value`` of a stored ``NewData`` node, one needs to do:

.. code-block:: python

    node = load_node(<IDENTIFIER>)
    node.get_attribute('value')

In other words, the user of the ``NewData`` class needs to know that the ``value`` is stored as an attribute with the name 'value'.
This is not easy to remember and therefore not very user-friendly.
Since the ``NewData`` type is a class, we can give it useful methods.
Let's introduce one that will return the value that was stored for it:

.. code-block:: python

    from aiida.orm import Data

    class NewData(Data):
        """A new data type that wraps a single value."""

        ...

        @property
        def value(self):
            """Return the value stored for this instance."""
            return self.get_attribute('value')

The addition of the instance property ``value`` makes retrieving the value of a ``NewData`` node a lot easier:

.. code-block:: python

    node = load_node(<IDENTIFIER)
    value = node.value

As said before, in addition to their attributes, data types can also store their properties in the file repository.
Here is an example for a custom data type that needs to wrap a single text file:

.. code-block:: python

    import os
    from aiida.orm import Data


    class TextFileData(Data):
        """Data class that can be used to wrap a single text file by storing it in its file repository."""

        def __init__(self, filepath, **kwargs):
            """Construct a new instance and set the contents to that of the file.

            :param file: an absolute filepath of the file to wrap
            """
            super().__init__(**kwargs)

            filename = os.path.basename(filepath)  # Get the filename from the absolute path
            self.put_object_from_file(filepath, filename)  # Store the file in the repository under the given filename
            self.set_attribute('filename', filename)  # Store in the attributes what the filename is

        def get_content(self):
            """Return the content of the single file stored for this data node.

            :return: the content of the file as a string
            """
            filename = self.get_attribute('filename')
            return self.get_object_content(filename)

To create a new instance of this data type and get its content:

.. code-block:: python

    node = TextFileData(filepath='/some/absolute/path/to/file.txt')
    node.get_content()  # This will return the content of the file

This example is a simplified version of the :class:`~aiida.orm.nodes.data.singlefile.SinglefileData` data class that ships with ``aiida-core``.
If this happens to be your use case (or very close to it), it is of course better to use that class, or you can sub class it and adapt it where needed.

The just presented examples for new data types are of course trivial, but the concept is always the same and can easily be extended to more complex custom data types.
The following section will provide useful guidelines on how to optimally design new data types.

.. _topics:data_types:plugin:design-guidelines:

Database or repository?
-----------------------

When deciding where to store a property of a data type, one has the option to choose between the database and the file repository.
All node properties that are stored in the database (such as the attributes), are directly searchable as part of a database query, whereas data stored in the file repository cannot be queried for.
What this means is that, for example, it is possible to search for all nodes where a particular database-stored integer attribute falls into a certain value range, but the same value stored in a file within the file repository would not be directly searchable in this way.
However, storing large amounts of data within the database comes at the cost of slowing down database queries.
Therefore, big data (think large files), whose content does not necessarily need to be queried for, is better stored in the file repository.
A data type may safely use both the database and file repository in parallel for individual properties.
Properties stored in the database are stored as *attributes* of the node.
The node class has various methods to set these attributes, such as :py:meth:`~aiida.orm.entities.EntityAttributesMixin.set_attribute` and :py:meth:`~aiida.orm.entities.EntityAttributesMixin.set_attribute_many`.
