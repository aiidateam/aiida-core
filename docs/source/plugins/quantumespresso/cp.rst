CP
++

Description
-----------
Use the plugin to support inputs of Quantum Espresso cp.x executable.
Note that most of the options are the same of the pw.x plugin, so refer to 
:doc:`that page <pw>` for more details.

Supported codes
---------------
* tested from cp.x v5.0 onwards.

Inputs
------
* **pseudo**, class :py:class:`UpfData <aiida.orm.data.upf.UpfData>`
  One pseudopotential file per atomic species.
  
  Alternatively, pseudo for every atomic species can be set with the **use_pseudos_from_family**
  method, if a family of pseudopotentials has been installed..
  
* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of cp.x, as a nested dictionary, mapping the input of QE.
  Example::
    
      {"ELECTRONS":{"ecutwfc":"30","ecutrho":"100"},
      }
  
  A full list of variables and their meaning is found in the `cp.x documentation`_.

  .. _cp.x documentation: http://www.quantum-espresso.org/wp-content/uploads/Doc/INPUT_CP.html

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
  The initial ionic configuration of the CP molecular dynamics.
* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  An optional dictionary that activates non-default operations. Check the section
  :ref:`Advanced features (on the PW plugin documentation page)<pw-advanced-features>`
  to know which flags can be passed.
    
* **parent_folder**, class :py:class:`RemoteData <aiida.orm.data.parameter.ParameterData>` (optional)
  If specified, the scratch folder coming from a previous QE calculation is 
  copied in the scratch of the new calculation.
  
Outputs
-------
There are several output nodes that can be created by the plugin, according to the calculation details.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Contains the scalar properties. Example: energies (in eV) of the last configuration, 
  wall_time, warnings (possible error messages generated in the run).
  ``calculation.out.output_parameters`` can also be accessed by the ``calculation.res`` shortcut.
* output_trajectory_array :py:class:`TrajectoryData <aiida.orm.data.array.trajectory.TrajectoryData>`
  Contains vectorial properties, too big to be put in the dictionary, like
  energies, positions, velocities, cells, at every saved step.  
* output_structure :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
  Structure of the last step.

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible 
with the ``verdi calculation logshow`` command). 
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.
