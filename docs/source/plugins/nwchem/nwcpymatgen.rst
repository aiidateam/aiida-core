nwchem.nwcpymatgen
++++++++++++++++++

Description
-----------
*pymatgen*-based input plugin for main *NWChem*'s ``nwchem`` executable.

Inputs
------
* :py:class:`StructureData <aiida.orm.data.structure.StructureData>` (optional)
    A structure.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    A dictionary with control variables.

Outputs
-------
* ``job_info``: :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    A dictionary of general parameters of the computation, like details of
    compilation, used time and memory.

May also contain one or more of the following:

* ``output``: :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    A dictionary describing the job. An example::

        {
          "basis_set": {}, 
          "corrections": {}, 
          "energies": [], 
          "errors": [], 
          "frequencies": null, 
          "has_error": false, 
          "job_type": "NWChem Geometry Optimization"
        }
    
* ``trajectory``: :py:class:`TrajectoryData <aiida.orm.data.array.trajectory.TrajectoryData>` (optional)
    A trajectory, made of structures, produced in the steps of geometry
    optimization.

    .. note:: Functionality to extract structures from *NWChem*'s output is
        not present in *pymatgen* 3.0.13 or earlier.

Errors
------
Errors are reported in the ``errors`` field of ``output``
:py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
dictionary. Additionally, there's a boolean flag ``has_error`` in the same
dictionary.
