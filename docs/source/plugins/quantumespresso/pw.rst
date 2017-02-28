PW
++

Description
-----------
Use the plugin to support inputs of Quantum Espresso pw.x executable.

Supported codes
---------------
* tested from pw.x v5.0 onwards.

Inputs
------
* **pseudo**, class :py:class:`UpfData <aiida.orm.data.upf.UpfData>`
  One pseudopotential file per atomic species.
  
  Alternatively, pseudo for every atomic species can be set with the **use_pseudos_from_family**
  method, if a family of pseudopotentials has been installed.
  
* **kpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Reciprocal space points on which to build the wavefunctions. Can either be 
  a mesh or a list of points with/without weights
* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of pw.x, as a nested dictionary, mapping the input of QE.
  Example::
    
      {"CONTROL":{"calculation":"scf"},
       "ELECTRONS":{"ecutwfc":30.,"ecutrho":100.},
      }

  A full list of variables and their meaning is found in the `pw.x documentation`_.

  .. _pw.x documentation: http://www.quantum-espresso.org/wp-content/uploads/Doc/INPUT_PW.html

  Following keywords, related to the structure or to the file paths, are already taken care of by AiiDA::
    
      'CONTROL', 'pseudo_dir': pseudopotential directory
      'CONTROL', 'outdir': scratch directory
      'CONTROL', 'prefix': file prefix
      'SYSTEM', 'ibrav': cell shape
      'SYSTEM', 'celldm': cell dm
      'SYSTEM', 'nat': number of atoms
      'SYSTEM', 'ntyp': number of species
      'SYSTEM', 'a': cell parameters
      'SYSTEM', 'b': cell parameters
      'SYSTEM', 'c': cell parameters
      'SYSTEM', 'cosab': cell parameters
      'SYSTEM', 'cosac': cell parameters
      'SYSTEM', 'cosbc': cell parameters

  Those keywords should not be specified, otherwise the submission will fail.
     
* **structure**, class :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  An optional dictionary that activates non-default operations. For a list of possible
  values to pass, see the section on the :ref:`advanced features <pw-advanced-features>`.
* **parent_folder**, class :py:class:`RemoteData <aiida.orm.data.parameter.ParameterData>` (optional)
  If specified, the scratch folder coming from a previous QE calculation is 
  copied in the scratch of the new calculation.
* **vdw_table**, class :py:class:`SinglefileData <aiida.orm.data.singlefile.SinglefileData>` (optional)
  If specified, it should be a file for the van der Waals kernel table.
  The file is copied in the pseudo subfolder, without changing its name, and
  without any check, so it is your responsibility to select the correct file
  that you want to use.

Outputs
-------

There are several output nodes that can be created by the plugin, according to the calculation details.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Contains the scalar properties. Example: energy (in eV), 
  total_force (modulus of the sum of forces in eV/Angstrom),
  warnings (possible error messages generated in the run). ``calculation.out.output_parameters`` can also be
  accessed by the ``calculation.res`` shortcut.
* output_array :py:class:`ArrayData <aiida.orm.data.array.ArrayData>`
  Produced in case of calculations which do not change the structure, otherwise, 
  an ``output_trajectory`` is produced.
  Contains vectorial properties, too big to be put in the dictionary.
  Example: forces (eV/Angstrom), stresses, ionic positions.
  Quantities are parsed at every step of the ionic-relaxation / molecular-dynamics run.
* output_trajectory :py:class:`ArrayData <aiida.orm.data.array.ArrayData>`
  Produced in case of calculations which change the structure, otherwise an
  ``output_array`` is produced. Contains vectorial properties, too big to be put 
  in the dictionary. Example: forces (eV/Angstrom), stresses, ionic positions.
  Quantities are parsed at every step of the ionic-relaxation / molecular-dynamics run.
* output_band (non spin polarized calculations)) or output_band1 + output_band2 
  (spin polarized calculations) :py:class:`BandsData <aiida.orm.data.array.bands.BandsData>`
  Present only if parsing is activated with the **`ALSO_BANDS`** :ref:`setting <also-bands-setting>`.
  Contains the list of electronic energies for every kpoint.
  If calculation is a molecular dynamics or a relaxation run, bands refer only to the last ionic configuration.
* output_structure :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
  Present only if the calculation is moving the ions.
  Cell and ionic positions refer to the last configuration.
* output_kpoints :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Present only if the calculation changes the cell shape.
  Kpoints refer to the last structure.

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible 
with the ``verdi calculation logshow`` command). 
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.

.. _pw-advanced-features:

Additional advanced features (settings)
---------------------------------------

In this section we describe how to use some advanced functionality in the
Quantum ESPRESSO pw.x plugin (note that most of them apply also to the 
cp.x plugin).

While the input link with name 'parameters' is used for the content of the 
Quantum Espresso namelists, additional parameters can be specified in the 'settings' input, also as ParameterData.

After having defined the content of ``settings_dict``, you can use
it as input of a calculation ``calc`` by doing::

  calc.use_settings(ParameterData(dict=settings_dict))

The different options are described below.

.. _also-bands-setting:

Parsing band energies
.....................
During each scf or nscf run, QE stores the band energies at the k-points
of interest in .xml files in the output directory. If you want to retrieve
and parse them, you can set::

  settings_dict = {
      'also_bands': True
  }

Fixing some atom coordinates
............................
If you want to ask QE to keep some coordinates of some atoms fixed
(called ``if_pos`` in the QE documentation, and typically specified with
0 or 1 values after the atomic coordinates), you can specify the following
list of lists::

  settings_dict = {
      'fixed_coords': [
          [True,False,False],
          [True,True,True],
          [False,False,False],
          [False,False,False],
          [False,False,False],
          ],
  }

the list of lists (of booleans) must be of length N times 3, where N is the 
number of sites (i.e., atoms) in the input structure. ``False`` means that
the coordinate is free to move, ``True`` blocks that coordinate.

Passing an explicit list of kpoints on a grid
.............................................
Some codes (e.g., Wannier90) require that a QE calculation is run with 
an explicit grid of points (i.e., all points in a grid, even if they are
equivalent by symmetry). Instead of generating it manually, you can
pass a usual KpointsData specifying a mesh, and then pass the following 
variable::

  settings_dict = {  
      'force_kpoints_list': True,
  }

Gamma-only calculation
......................
If you are using only the Gamma point (a grid of 1x1x1 without offset), you
may want to use the following flag to tell QE to use the gamma-only routines
(typically twice faster)::

  settings_dict = {  
      'gamma_only': False,
  }

Initialization only
...................
Sometimes you want to run QE but stop it immediately after the initialisation
part (e.g. to parse the number of symmetries detected, the number of G vectors,
of k-points, ...)
In this case, by specifying::

  settings_dict = {  
      'only_initialization': True,
  }

a file named ``aiida.EXIT`` (where ``aiida`` is the prefix) will be also generated,
asking QE to exit cleanly after the initialisation.

Different set of namelists
..........................
The QE plugin will automatically figure out which namelists should be specified
(and in which order) depending con ``CONTROL.calculation`` (e.g. for SCF only
``CONTROL``, ``SYSTEM``, ``ELECTRONS``, but also ``IONS`` for RELAX, ...).
If you want to override the automatic list, you can specify the list
of namelists you want to produce as follows::

  settings_dict = {  
      'namelists': ['CONTROL', 'SYSTEM', 'ELECTRONS', 'IONS', 'CELL', 'OTHERNL'],
  }


Adding command-line options
...........................
If you want to add command-line options to the executable (particularly 
relevant e.g. to tune the parallelization level), you can pass each option 
as a string in a list, as follows::

  settings_dict = {  
      'cmdline': ['-nk', '4'],
  }

Using symlinks for the restarts
...............................
During a restart, the output directory of QE (stored by default in the subfolder
``./out``) containing charge density, wavefunctions, ...is copied over.
This is done in order to make sure one can perform multiple restarts of the 
same calculation without affecting it (QE often changes/replaces the content 
of that folder).

However, for big calculations this may take time at each restart, or fill the
scratch directory of your computing cluster. If you prefer to use symlinks, 
pass::


  settings_dict = {  
      'parent_folder_symlink': True,
  }

.. note:: Use this flag ONLY IF YOU KNOW WHAT YOU ARE DOING. In particular, 
  if you run a NSCF with this flag after a SCF calculation, the scratch directory
  of the SCF will change and you may have problems restarting other calculations 
  from the SCF.


Retrieving more files
.....................
If you know that your calculation is producing additional files that you want to
retrieve (and preserve in the AiiDA repository in the long term), you can add
those files as a list as follows (here in the case of a file named
``testfile.txt``)::

  settings_dict = {  
    'additional_retrieve_list': ['testfile.txt'],
  }



