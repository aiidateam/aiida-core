codtools.cifsplitprimitive
++++++++++++++++++++++++++

Description
-----------
This plugin is used by ``cif_split`` and ``cif_split_primitive`` codes from
the **cod-tools** package.

Supported codes
---------------
* cif_split [#]_
* cif_split_primitive

Inputs
------
* :py:class:`CifData <aiida.orm.data.cif.CifData>`
    A CIF file.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
    Contains the command line parameters, specified in key-value fashion.
    For more information, refer to
    :ref:`inputs for codtools.ciffilter plugin<codtools_ciffilter_inputs>`.

Outputs
-------
* List of :py:class:`CifData <aiida.orm.data.cif.CifData>`
    One or more CIF files.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
    Contains lines of output messages and/or errors.

Errors
------
Run-time errors are returned line-by-line in the
:py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` object.

.. [#] Incompatible with ``--output-prefixed`` and ``--output-tar`` command
  line options.
