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
    For more information refer to
    :ref:`inputs for codtools.ciffilter plugin<codtools_ciffilter_inputs>`.

Outputs
-------
* ParameterData
    Contains formulae in (`CIF datablock name`,`formula`) pairs. For
    example::

        print ParameterData.get_subclass_from_pk(1).get_dict()

    would print::

        {u'formulae': {
            u'4000001': u'C24 H17 F5 Fe',
            u'4000002': u'C24 H17 F5 Fe',
            u'4000003': u'C24 H17 F5 Fe',
            u'4000004': u'C22 H8 F10 Fe'
                      }})

    .. note:: ``data_`` is not prepended to the CIF datablock name -- the
       CIF file, used for the example above, contains CIF datablocks
       ``data_4000001``, ``data_4000002``, ``data_4000003`` and
       ``data_4000004``.
* ParameterData
    Contains lines of output messages and/or errors. For more information
    refer to
    :ref:`outputs for codtools.ciffilter plugin<codtools_ciffilter_outputs>`.

Errors
------
Run-time errors are returned line-by-line in the ParameterData object.
