codtools.cifcodcheck
++++++++++++++++++++

Description
-----------
This plugin is specific for ``cif_cod_check`` script.

Supported codes
---------------
* cif_cod_check

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
    Contains lines of output messages and/or errors. For more information
    refer to
    :ref:`outputs for codtools.ciffilter plugin<codtools_ciffilter_outputs>`.

Errors
------
Run-time errors are returned line-by-line in the
:py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` object.
