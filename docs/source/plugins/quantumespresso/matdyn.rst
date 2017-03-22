Matdyn
++++++

Description
-----------
Use the plugin to support inputs of Quantum Espresso matdyn.x executable.

Supported codes
---------------
* tested from matdyn.x v5.0 onwards.

Inputs
------
* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters of pw.x, as a nested dictionary, mapping the input of QE.
  Example::
    
      {"INPUT":{"ars":"simple"},
      }
  
  See the QE documentation for the full list of variables and their meaning. 
  Note: some keywords don't have to be specified or Calculation will enter 
  the SUBMISSIONFAILED state, and are already taken care of by AiiDA (are related 
  with the structure or with path to files)::
    
      'INPUT', 'flfrq': file with frequencies in output
      'INPUT', 'flvec': file with eigenvecors
      'INPUT', 'fldos': file with dos
      'INPUT', 'q_in_cryst_coord': for qpoints
      'INPUT', 'flfrc': input force constants
         
* **parent_calculation**, pass the parent q2r calculation of its FolderData as the **parent_folder**
  to pass the input force constants.

* **kpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>`
  Points on which to compute the interpolated frequencies. 
  Must contain a list of kpoints.

Outputs
-------
There are several output nodes that can be created by the plugin, according to the calculation details.
All output nodes can be accessed with the ``calculation.out`` method.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Contains warnings. ``calculation.out.output_parameters`` can also be accessed
  by the ``calculation.res`` shortcut.

* output_phonon_bands :py:class:`BandsData <aiida.orm.data.array.bands.BandsData>`
  Phonon frequencies as a function of qpoints.

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible 
with the ``verdi calculation logshow`` command). 
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.
