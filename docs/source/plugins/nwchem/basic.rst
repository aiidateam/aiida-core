nwchem.basic
++++++++++++

Description
-----------

A very simple plugin for main NWChem's ``nwchem`` executable.

Inputs
------
* :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
    A structure.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
    A dictionary with control variables. An example (default values)::

        {
          "abbreviation": "aiida_calc",               # Short name for the computation
          "title":        "AiiDA NWChem calculation", # Long name for the computation
          "basis":                                    # Basis per chemical type
            {
              "Ba": "library 6-31g",
              "Ti": "library 6-31g",
              "O":  "library 6-31g",
            },
          "task":         "scf",                      # Computation task
          "add_cell":     True,                       # Include cell parameters?
        }

Outputs
-------
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    A dictionary with energy values. For example::

        {
          "nuclear_repulsion_energy": "9.194980930276", 
          "one_electron_energy":      "-122.979939235872", 
          "total_scf_energy":         "-75.983997570474", 
          "two_electron_energy":      "37.800960735123"
        }
