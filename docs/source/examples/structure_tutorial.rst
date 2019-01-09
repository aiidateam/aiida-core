.. _structure_tutorial:

General comments
----------------

This section contains an example of how you can use the
:py:class:`~aiida.orm.data.structure.StructureData` object
to create complex crystals.

With the :py:class:`~aiida.orm.data.structure.StructureData` class we did not
try to have a full set of features to manipulate crystal structures.
Indeed, other libraries such as `ASE <https://wiki.fysik.dtu.dk/ase/>`_ exist,
and we simply provide easy
ways to convert between the ASE and the AiiDA formats. On the other hand, 
we tried to define a "standard" format for structures in AiiDA, that can be
used across different codes.


Tutorial
--------

Take a look at the following example::

  alat = 4. # angstrom
  cell = [[alat, 0., 0.,],
          [0., alat, 0.,],
          [0., 0., alat,],
         ]
  s = StructureData(cell=cell)
  s.append_atom(position=(0.,0.,0.), symbols='Fe')
  s.append_atom(position=(alat/2.,alat/2.,alat/2.), symbols='O')

With the commands above, we have created a crystal structure ``s`` with 
a cubic unit cell and lattice parameter of 4 angstrom, and two atoms in the
cell: one iron (Fe) atom in the origin, and one oxygen (O) at the center of 
the cube (this cell has been just chosen as an example and most probably does
not exist).

.. note:: As you can see in the example above, both the cell coordinates and
  the atom coordinates are expressed in angstrom, and the position of
  the atoms are given in a global absolute reference frame.
  
In this way, any periodic structure can be defined. If you want to import
from ASE in order to specify the coordinates, e.g., in terms of the crystal
lattice vectors, see the guide on the conversion to/from ASE below.

When using the :py:meth:`~aiida.orm.data.structure.StructureData.append_atom`
method, further parameters can be passed. In particular, one can specify 
the mass of the atom, particularly important if you want e.g. to run a
phonon calculation. If no mass is specified, the mass provided by
`NIST <http://www.nist.gov/pml/data/index.cfm>`_ (retrieved in October 2014)
is going to be used. The list of
masses is stored in the module :py:mod:`aiida.common.constants`, in the
``elements`` dictionary. 

Moreover, in the :py:class:`~aiida.orm.data.structure.StructureData` class
of AiiDA we also support the storage of crystal structures with alloys,
vacancies or partial occupancies. 
In this case, the argument of the parameter ``symbols``
should be a list of symbols, if you want to consider an alloy;
moreover, you must pass a ``weights`` list, with the same length as ``symbols``,
and with values between 0. (no occupancy) and 1. (full occupancy), to specify
the fractional occupancy of that site for each of the symbols specified
in the ``symbols`` list. The sum of
all occupancies must be lower or equal to one; if the sum is lower than one,
it means that there is a given probability of having a vacancy at that
specific site position.

As an example, you could use::

  s.append_atom(position=(0.,0.,0.),symbols=['Ba','Ca'],weights=[0.9,0.1])

to add a site at the origin of a structure ``s`` consisting of an alloy of
90% of Barium and 10% of Calcium (again, just an example).

The following line instead::

  s.append_atom(position=(0.,0.,0.),symbols='Ca',weights=0.9)

would create a site with 90% probability of being occupied by Calcium, and
10% of being a vacancy.

Utility methods ``s.is_alloy`` and ``s.has_vacancies`` can be used to
verify, respectively, if more than one element if given in the symbols list,
and if the sum of all weights is smaller than one.

.. note:: if you pass more than one symbol, the method ``s.is_alloy`` will 
  always return ``True``, even if only one symbol has occupancy 1. and 
  all others have occupancy zero::
    
    >>> s = StructureData(cell=[[4,0,0],[0,4,0],[0,0,4]])
    >>> s.append_atom(position=(0.,0.,0.), symbols=['Fe', 'O'], weights=[1.,0.])
    >>> s.is_alloy()
    True
 
   
Internals: Kinds and Sites
--------------------------
Internally, the :py:meth:`~aiida.orm.data.structure.StructureData.append_atom`
method works by manipulating the kinds and sites of the current structure.
Kinds are instances of the :py:class:`~aiida.orm.data.structure.Kind` class and
represent a chemical species, with given properties (composing element or 
elements, occupancies, mass, ...) and identified
by a label (normally, simply the element chemical symbol).

Sites are instances of the :py:class:`~aiida.orm.data.structure.Site` class
and represent instead each single site. Each site refers
to a :py:class:`~aiida.orm.data.structure.Kind`  to
identify its properties (which element it is, the mass, ...) and to its three
spatial coordinates.

The :py:meth:`~aiida.orm.data.structure.StructureData.append_atom` works in
the following way:

* It creates a new :py:class:`~aiida.orm.data.structure.Kind` 
  class with the properties passed as parameters 
  (i.e., all parameters except ``position``).

* It tries to identify if an identical Kind already exists in the list
  of kinds of the structure (e.g., in the same atom with the same mass was
  already previously added). Comparison of kinds is performed using
  :py:meth:`aiida.orm.data.structure.Kind.compare_with`, and in particular
  it returns ``True`` if the mass and the list of symbols and of weights are 
  identical (within a threshold). If an identical kind ``k`` is found,
  it simply adds a new site referencing to kind ``k`` and with the provided
  ``position``. Otherwise, it appends ``k`` to the list of kinds of the current
  structure and then creates the site referencing to ``k``. The name of the
  kind is chosen, by default, equal to the name of the chemical symbol (e.g.,
  "Fe" for iron).

* If you pass more than one species for the same chemical symbol, but e.g. with
  different masses, a new kind is created and the name is obtained postponing
  an integer to the chemical symbol name. For instance, the following lines::
  
    s.append_atom(position = [0,0,0], symbols='Fe', mass = 55.8)
    s.append_atom(position = [1,1,1], symbols='Fe', mass = 57)
    s.append_atom(position = [1,1,1], symbols='Fe', mass = 59)
  
  will automatically create three kinds, all for iron, with names ``Fe``,
  ``Fe1`` and ``Fe2``, and masses 55.8, 57. and 59. respecively.
  
* In case of alloys, the kind name is obtained concatenating all chemical 
  symbols names (and a X is the sum of weights is less than one). The same
  rules as above are used to append a digit to the kind name, if needed.

* Finally, you can simply specify the kind_name to automatically generate a 
  new kind with a specific name. This is the case if you want a name different
  from the automatically generated one, or for instance if you want to create
  two different species with the same properties (same mass, symbols, ...).
  This is for instance the case in Quantum ESPRESSO in order to describe an 
  antiferromagnetic cyrstal, with different magnetizations on the different
  atoms in the unit cell.
  
  In this case, you can for instance use::
  
    s.append_atom(position = [0,0,0], symbols='Fe', mass = 55.845, name='Fe1')
    s.append_atom(position = [2,2,2], symbols='Fe', mass = 55.845, name='Fe2')
  
  To create two species ``Fe1`` and ``Fe2`` for iron, with the same mass.
  
  .. note:: You do not need to specify explicitly the mass if the default one
    is ok for you. However, when you pass explicitly a name and it coincides
    with the name of an existing species, all properties that you
    specify must be identical to the ones of the existing species, or the 
    method will raise an exception.
  
  .. note:: If you prefer to work with the 
    internal :py:class:`~aiida.orm.data.structure.Kind` 
    and :py:class:`~aiida.orm.data.structure.Site` classes,
    you can obtain the same
    result of the two lines above with::
    
      from aiida.orm.data.structure import Kind, Site
      s.append_kind(Kind(symbols='Fe', mass=55.845, name='Fe1'))
      s.append_kind(Kind(symbols='Fe', mass=55.845, name='Fe1'))
      s.append_site(Site(kind_name='Fe1', position=[0.,0.,0.]))
      s.append_site(Site(kind_name='Fe2', position=[2.,2.,2.]))


Conversion to/from ASE
----------------------

If you have an AiiDA structure, you can get an ``ase.Atom`` object by
just calling the :py:class:`~aiida.orm.data.structure.StructureData.get_ase`
method::
    
    ase_atoms = aiida_structure.get_ase()

.. note:: As we support alloys and vacancies in AiiDA, while ``ase.Atom`` does not,
  it is not possible to export to ASE a structure with vacancies or alloys.

If instead you have as ASE Atoms object and you want to load the structure
from it, just pass it when initializing the class::

      StructureData = DataFactory('structure')
      # or:
      # from aiida.orm.data.structure import StructureData
      aiida_structure = StructureData(ase = ase_atoms)
      
Creating multiple species
+++++++++++++++++++++++++

We implemented the possibility of specifying different Kinds (species) in the
ase.atoms and then importing them. 

In particular, if you specify atoms with different mass in ASE, during the
import phase different kinds will be created::

  >>> import ase
  >>> StructureData = DataFactory("structure")
  >>> asecell = ase.Atoms('Fe2')
  >>> asecell[0].mass = 55.
  >>> asecell[1].mass = 56.
  >>> s = StructureData(ase=asecell)
  >>> for kind in s.kinds:
  >>>     print kind.name, kind.mass
  Fe 55.0
  Fe1 56.0
  
Moreover, even if the mass is the same, but you want to get different species,
you can use the ASE ``tags`` to specify the number to append to the element 
symbol in order to get the species name::

  >>> import ase
  >>> StructureData = DataFactory("structure")
  >>> asecell = ase.Atoms('Fe2')
  >>> asecell[0].tag = 1
  >>> asecell[1].tag = 2
  >>> s = StructureData(ase=asecell)
  >>> for kind in s.kinds:
  >>>     print kind.name
  Fe1
  Fe2
  
.. note:: in complicated cases (multiple tags, masses, ...),
  it is possible that exporting a AiiDA structure
  to ASE and then importing it again will not perfectly preserve the kinds and
  kind names.

Conversion to/from pymatgen
---------------------------

AiiDA structure can be converted to pymatgen's `Molecule`_ and
`Structure`_ objects by using, accordingly,
:py:class:`~aiida.orm.data.structure.StructureData.get_pymatgen_molecule`
and
:py:class:`~aiida.orm.data.structure.StructureData.get_pymatgen_structure`
methods::

    pymatgen_molecule  = aiida_structure.get_pymatgen_molecule()
    pymatgen_structure = aiida_structure.get_pymatgen_structure()

A single method
:py:class:`~aiida.orm.data.structure.StructureData.get_pymatgen` can be
used for both tasks: converting periodic structures (periodic boundary
conditions are met in all three directions) to pymatgen's Structure and
other structures to pymatgen's Molecule::

    pymatgen_object = aiida_structure.get_pymatgen()

It is also possible to convert pymatgen's Molecule and Structure
objects to AiiDA structures::

    StructureData = DataFactory("structure")
    from_mol      = StructureData(pymatgen_molecule=mol)
    from_struct   = StructureData(pymatgen_structure=struct)

Also in this case, a generic converter is provided::

    StructureData = DataFactory("structure")
    from_mol      = StructureData(pymatgen=mol)
    from_struct   = StructureData(pymatgen=struct)

.. note:: Converters work with version 3.0.13 or later of
  pymatgen. Earlier versions may cause errors.

.. _Molecule:  http://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Molecule
.. _Structure: http://pymatgen.org/pymatgen.core.html#pymatgen.core.structure.Structure
