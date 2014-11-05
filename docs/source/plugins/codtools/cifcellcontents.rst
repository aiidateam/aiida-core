codtools.cifcellcontents
++++++++++++++++++++++++

Description
-----------
This plugin is used for chemical formula calculations from the CIF files,
as being done by ``cif_cell_contents`` code from the **cod-tools** package.

Supported codes
---------------
* cif_cell_contents

Inputs
------
* CifData
    A CIF file.
* ParameterData (optional)
    Contains the command line parameters, specified in key-value fashion.
    For more information, refer to
    :ref:`inputs for codtools.ciffilter plugin<codtools_ciffilter_inputs>`.

Outputs
-------
* ParameterData
    Contains formula/formulae as well as the lines of output messages
    and/or errors.

Errors
------
Run-time errors are returned line-by-line in the ParameterData object.
