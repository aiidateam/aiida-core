NEB
+++

Description
-----------
Plugin for the Quantum Espresso neb.x executable.

Supported codes
---------------
* tested from neb.x v5.2 onwards. 

Inputs
------
* **pseudo**, class :py:class:`UpfData <aiida.orm.data.upf.UpfData>`
  One pseudopotential file per atomic species.
  
  Alternatively, pseudo for every atomic species can be set with the **use_pseudos_from_family**
  method, if a family of pseudopotentials has been installed..
  
* **kpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Reciprocal space points on which to build the wavefunctions. Can either be 
  a mesh or a list of points with/without weights

* **neb_parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of neb.x, as a nested dictionary, mapping the input of QE.
  Example::
    
      {"PATH":{"num_of_images":6, "string_method": "neb", "nstep_path": 50},
      }
  
  See the QE documentation for the full list of variables and their meaning.
* **pw_parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Nested dictionary containing the input parameters in PW format common to all images.
  Example::
    
      {"CONTROL":{"calculation":"scf"},
       "ELECTRONS":{"ecutwfc":"30","ecutrho":"100"},
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
     
* **first_structure**, class :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
  Structure of the first image.
* **last_structure**, class :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
  Structure of the last image.
  
* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  An optional dictionary that activates non-default operations. Possible values are:
    
    *  **'CLIMBING_IMAGES'**: list of integers. Specify the indices of the climbing images. 
       Read only if the climbing image scheme is set to ``manual`` in ``neb_parameters``.
    *  **'FIXED_COORDS'**: a list Nx3 booleans, with N the number of atoms. If True,
       the atomic position is fixed.
    *  **'GAMMA_ONLY'**: boolean. If True and the kpoint mesh is gamma, activate 
       a speed up of the calculation.
    *  **'NAMELISTS'**: list of strings. Specify all the list of Namelists to be 
       printed in the input file.
    *  **'PARENT_FOLDER_SYMLINK'**: boolean. If True, create a symlnk to the scratch 
       of the parent folder, otherwise the folder is copied (default: False)
    *  **'CMDLINE'**: list of strings. parameters to be put after the executable in addition to `-input_images 2`. 
       Example: ["-npool","4"] will produce `neb.x -input_images 2 -npool 4 > aiida.out`
    *  **'ADDITIONAL_RETRIEVE_LIST'**: list of strings. Specify additional files to be retrieved.
       By default, the following files are already retrieved:
       *  NEB output file
       *  PATH output file containing the information on structures and gradients of each image at last iteration
       *  The calculated and interpolated energy profile as a function of the reaction coordinate (`.dat` and `.int`  files)
       *  The PW output and xml file for each image
    *  **'ALL_ITERATIONS'**: boolean. If true the energies and forces for each image at each intermediate 
       iteration are also parsed and stored in the output node ``iteration_array`` (default: False)
    
* **parent_folder**, class :py:class:`RemoteData <aiida.orm.data.parameter.ParameterData>` (optional)
  If specified, the scratch folder coming from a previous NEB calculation is 
  copied in the scratch of the new calculation.


Outputs
-------

There are several output nodes that can be created by the plugin, according to the calculation details.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` 
  (accessed by ``calculation.res``)
  Contains the data obtained by parsing the NEB output file. Information on the last iteration are only reported. 
  The parsed PW outputs of each image are also reported as a subdictionaries. 
* mep_array :py:class:`ArrayData <aiida.orm.data.array.ArrayData>`
  Contains the parsed data on the calculated and interpolated Minimim Energy Path (MEP), 
  i.e. the energy profile as a function of the reaction coordinate.
* output_trajectory :py:class:`ArrayData <aiida.orm.data.array.ArrayData>`
  Contains the structure of the images at the last iteration of the NEB calculation, 
  too big to be put in the dictionary.
* iteration_array :py:class:`ArrayData <aiida.orm.data.array.ArrayData>` , and other quantities at intermediate iterations.
  
  

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible 
with the ``verdi calculation logshow`` command). 
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.
