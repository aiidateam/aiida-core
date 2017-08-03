PH
++

Description
-----------
Plugin for the Quantum Espresso ph.x executable.

Supported codes
---------------
* tested from ph.x v5.0 onwards.

Inputs
------
* **parent_calculation**, can either be a PW calculation to get the ground state on which to compute 
  the phonons, or a PH calculation in case of restarts.
  
  Note: There are no direct links between calculations. The use_parent_calculation will set
  a link to the RemoteFolder attached to that calculation. Alternatively, the method **use_parent_folder**
  can be used to set this link directly.
  
* **qpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Reciprocal space points on which to build the dynamical matrices. Can either be 
  a mesh or a list of points. Note: up to QE 5.1 only either an explicit list
  of 1 qpoint (1 point only) can be provided, or a mesh (containing gamma).

* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of ph.x, as a nested dictionary, mapping the input of QE.
  Example::
    
      {"INPUTPH":{"ethr-ph":1e-16},
      }
  
  A full list of variables and their meaning is found in the `ph.x documentation`_.

  .. _ph.x documentation: http://www.quantum-espresso.org/wp-content/uploads/Doc/INPUT_PH.html

  Following keywords are already taken care of by AiiDA::
    
      'INPUTPH', 'outdir': scratch directory
      'INPUTPH', 'prefix': file prefix
      'INPUTPH', 'iverbosity': file prefix
      'INPUTPH', 'fildyn': file prefix
      'INPUTPH', 'ldisp': logic displacement
      'INPUTPH', 'nq1': q-mesh on b1
      'INPUTPH', 'nq2': q-mesh on b2
      'INPUTPH', 'nq3': q-mesh on b3
      'INPUTPH', 'qplot': flag for list of qpoints
     
* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  An optional dictionary that activates non-default operations. Possible values are:
    
    *  **'PARENT_CALC_OUT_SUBFOLDER'**: string. The subfolder of the parent 
       scratch to be copied in the new scratch.
    *  **'PREPARE_FOR_D3'**: boolean. If True, more files are created in 
       preparation of the calculation of a D3 calculation.
    *  **'NAMELISTS'**: list of strings. Specify all the list of Namelists to be 
       printed in the input file.
    *  **'PARENT_FOLDER_SYMLINK'**: boolean # If True, create a symlnk to the scratch 
       of the parent folder, otherwise the folder is copied (default: False)
    *  **'CMDLINE'**: list of strings. parameters to be put after the executable and before the input file. 
       Example: ["-npool","4"] will produce `ph.x -npool 4 < aiida.in`
    *  **'ADDITIONAL_RETRIEVE_LIST'**: list of strings. Extra files to be retrieved.
       By default, dynamical matrices, text output and main xml files are retrieved.

Outputs
-------
There are several output nodes that can be created by the plugin, according to the calculation details.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Contains small properties. Example: dielectric constant, 
  warnings (possible error messages generated in the run).
  ``calculation.out.output_parameters`` can also be accessed by the ``calculation.res`` shortcut.
  Furthermore, various ``dynamical_matrix_*`` keys are created, each is a dictionary containing
  the keys ``q_point`` and ``frequencies``.

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible 
with the ``verdi calculation logshow`` command). 
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.
