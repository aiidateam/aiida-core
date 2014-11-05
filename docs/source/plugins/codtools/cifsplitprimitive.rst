codtools.cifsplitprimitive
++++++++++++++++++++++++++

Description
-----------
This plugin is used by ``cif_split_primitive`` code from the **cod-tools**
package.

Supported codes
---------------
* cif_split_primitive

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
* List of CifData
    One or more CIF files.
* ParameterData (optional)
    Contains lines of output messages and/or errors.

Errors
------
Run-time errors are returned line-by-line in the ParameterData object.
