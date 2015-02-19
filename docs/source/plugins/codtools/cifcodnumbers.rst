codtools.cifcodnumbers
++++++++++++++++++++++

Description
-----------
This plugin is specific for ``cif_cod_numbers`` script.

Supported codes
---------------
* cif_cod_numbers

Inputs
------
* :py:class:`CifData <aiida.orm.data.cif.CifData>`
    A CIF file.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
    Contains the command line parameters, specified in key-value fashion.
    For more information refer to
    :ref:`inputs for codtools.ciffilter plugin<codtools_ciffilter_inputs>`.

Outputs
-------
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    Contains two subdictionaries: ``duplicates`` and ``errors``. In
    ``duplicates`` correspondence between the database and supplied file(s)
    is described. Example::

        {
          "duplicates": [
            {
              "codid": "4000099", 
              "count": 1, 
              "formula": "C50_H44_N2_Ni_O4"
            }
          ], 
          "errors": []
        }

    Here ``codid`` is numeric ID of a hit in the database, ``count`` is
    total number of hits for the particular datablock and ``formula`` is
    the summary formula of the described datablock.

Errors
------
Run-time errors are returned line-by-line in the
:py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` object.
