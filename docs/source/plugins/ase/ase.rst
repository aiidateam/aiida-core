ASE
+++

Description
-----------
Use the plugin to support inputs of ASE structure optimizations and of total
energy calculations.
Requires the installation of ASE on the computer where AiiDA is running.

Supported codes
---------------
* tested on ASE v3.8.1 and on GPAW v0.10.0. 
  ASE back compatibility is not guaranteed.
  Calculators different from GPAW should work, if they follow the interface
  description of ASE calculators, but have not been tested.
  Usage requires the installation of both ASE and of the software used by the
  calculator.
  
Inputs
------

* **kpoints**, class :py:class:`KpointsData <aiida.orm.data.array.kpoints.KpointsData>` (optional)
  Reciprocal space points on which to build the wavefunctions. Only kpoints 
  meshes are currently supported.

* **parameters**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
  Input parameters that defines the calculations to be performed, and their
  parameters. 
  See the ASE documentation for more details.
     
* **structure**, class :py:class:`StructureData <aiida.orm.data.structure.StructureData>`

* **settings**, class :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
  An optional dictionary that activates non-default operations. Possible values are:
    
    *  **'CMDLINE'**: list of strings. parameters to be put after the executable and before the input file. 
       Example: ["-npool","4"] will produce `gpaw -npool 4 < aiida_input`
    *  **'ADDITIONAL_RETRIEVE_LIST'**: list of strings. Specify additional files to be retrieved.
       By default, the output file and the xml file are already retrieved. 

Outputs
-------
Actual output production depends on the input provided.

* output_parameters :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` 
  (accessed by ``calculation.res``)
  Contains the scalar properties. Example: energy (in eV) or
  warnings (possible error messages generated in the run).
* output_array :py:class:`ArrayData <aiida.orm.data.array.ArrayData>`
  Stores vectorial quantities (lists, tuples, arrays), if requested in output.
  Example: forces, stresses, positions.
  Units are those produced by the calculator.
* output_structure :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
  Present only if the structure is optimized.

Errors
------
Errors of the parsing are reported in the log of the calculation (accessible 
with the ``verdi calculation logshow`` command). 
Moreover, they are stored in the ParameterData under the key ``warnings``, and are
accessible with ``Calculation.res.warnings``.

Examples
--------
The following example briefly describe the usage of GPAW within AiiDA, assuming 
that both ASE and GPAW have been installed on the remote machine.
Note that ASE calculators, at times, require the definition of environment 
variables. Take your time to find them and make sure that they are loaded by the
submission script of AiiDA (use the prepend text fields of a Code, for example).
 
First of all install the AiiDA Code as usual, noting that, if you plan to use 
the serial version of GPAW (applies to all other calculators) the remote absolute
path of the code has to point to the python executable (i.e. the output of 
``which python`` on the remote machine, typically it might be ``/usr/bin/python``).
If the parallel version of GPAW is used, set instead the path to gpaw-python.

To understand the plugin, it is probably easier to try to run one test, to see
the python script which is produced and executed on the remote machine.
We describe in the following some example script, which can be called through 
the ``verdi run`` command (example: ``verdi run test_script.py``). You should 
see a folder ``submit_test`` created in the location from which you run
the command. Here there is the input script that is going to be executed in 
the remote machine, with the syntax of the ASE software.

In :download:`this first example script <test_gpaw_1.py>` and execute it with 
the ``verdi run`` command.
This is a minimal script that uses GPAW and a plane-wave basis to compute the 
total energy of a structure.
Note that for a serial calculation, it is necessary to run the 
``calculation.set_withmpi(False)`` method.
Note also, that by default, only the total energy of the structure is computed 
and retrieved.

:download:`This second example <test_gpaw_2.py>` instead shows a demo of all
possible options supported by the current plugin.
By specifying an optimizer key in the dictionary, the ASE optimizers are run.
In the example, the QuasiNewton algorithm is run to minimize the forces and find
the equilibrium structures.
By specifying the key "calculator_getters", the code will get from the 
calculator, the properties which are specified in the value, using the get 
method of the calculator; similar applies for the ``atoms_getters``, which will 
call the ``atoms.get`` method. 
``extra_lines`` and ``post_lines`` are used to insert python commands that are 
executed before or after the call to the calculators.
``extra_imports`` is used to specify the import of more modules.

Lastly, :download:`this script <test_gpaw_parallel.py>` is an example of how to 
run GPAW parallel. Essentially, nothing has to be changed in input, except that 
there is no need to call the method ``calculation.set_withmpi(False)``.



