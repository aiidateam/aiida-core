PW
++

Description
-----------
Use the plugin to support inputs of Quantum Espresso pw.x executable.

Supported codes
---------------
* tested from pw.x v5.0 onwards. Back compatibility is not guaranteed (although
  versions 4.3x might work most of the times).

Inputs
------
* **pseudo**, class :py:class:`UpfData <aiida.orm.data.upf.UpfData>`
  One pseudopotential file per atomic species.
  
  Alternatively, pseudo for every atomic species can be set with the **use_pseudos_from_family**
  method, if a family of pseudopotentials has been installed..
  
* **kpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Reciprocal space points on which to build the wavefunctions. Can either be 
  a mesh or a list of points with/without weights
* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of pw.x, as a nested dictionary, mapping the input of QE.
  Example::
    
      {"CONTROL":{"calculation":"scf"},
       "ELECTRONS":{"ecutwfc":30.,"ecutrho":100.},
      }
  
  See the QE documentation for the full list of variables and their meaning. 
  Note: some keywords don't have to be specified or Calculation will enter 
  the SUBMISSIONFAILED state, and are already taken care of by AiiDA (are related 
  with the structure or with path to files)::
    
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
     
* **structure**, class :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  An optional dictionary that activates non-default operations. Possible values are:
    
    *  **'FIXED_COORDS'**: a list Nx3 booleans, with N the number of atoms. If True,
       the atomic position is fixed (in relaxations/md).
    *  **'GAMMA_ONLY'**: boolean. If True and the kpoint mesh is gamma, activate 
       a speed up of the calculation.
    *  **'NAMELISTS'**: list of strings. Specify all the list of Namelists to be 
       printed in the input file.
    *  **'PARENT_FOLDER_SYMLINK'**: boolean # If True, create a symlnk to the scratch 
       of the parent folder, otherwise the folder is copied (default: False)
    *  **'CMDLINE'**: list of strings. parameters to be put after the executable and before the input file. 
       Example: ["-npool","4"] will produce `pw.x -npool 4 < aiida.in`
    *  **'ADDITIONAL_RETRIEVE_LIST'**: list of strings. Specify additional files to be retrieved.
       By default, the output file and the xml file are already retrieved. 
    *  **'ALSO_BANDS'**: boolean. If True, retrieves the band structure (default: False)
    *  **'FORCE_KPOINTS_LIST'**: If it is set to True and the KpointsData have a mesh set, it will pass the kpoints to
       QE as if they were a list of coordinates, generating a list of points. (at the moment used for wannier90)
    *  **'ENVIRON'**: dictionary. If present a separate input file for the ENVIRON module is created with the dictionary
       converted to a namelist. A proper flag is added to the CMDLINE to instruct QE to use ENVIRON, if not already present.
    
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
.. note:: The `output_parameters` has more parsed values in the EPFL version and `output_bands` is parsed only in the EPFL version.

There are several output nodes that can be created by the plugin, according to the calculation details.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` 
  (accessed by ``calculation.res``)
  Contains the scalar properties. Example: energy (in eV), 
  total_force (modulus of the sum of forces in eV/Angstrom),
  warnings (possible error messages generated in the run).
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
  Present only if parsing is activated with the **`ALDO_BANDS`** setting.
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
