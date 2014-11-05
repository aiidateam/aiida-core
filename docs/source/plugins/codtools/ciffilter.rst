codtools.ciffilter
++++++++++++++++++

Description
-----------
This plugin is designed for filter-like codes from the **cod-tools**
package, but can be adapted to any command line utilities, accepting
CIF file as standard input and producing CIF file as standard output and
messages/errors in the standard output (if any), without modifications.

Supported codes
---------------
* cif_correct_tags
* cif_eval_numbers
* cif_filter
* cif_fix_values
* cif_mark_disorder
* cif_molecule
* cif_p1
* cif_reformat_AMCSD_author_names
* cif_reformat_pubmed_author_names
* cif_reformat_uppercase_author_names
* cif_select [#]_
* cif_set_value
* cif_symop_apply

.. _codtools_ciffilter_inputs:

Inputs
------
* CifData
    A CIF file.
* ParameterData (optional)
    Contains the command line parameters, specified in key-value fashion.
    Leading dashes (single or double) must be stripped from the keys.
    Values can be arrays with multiple items. Keys without values should
    point to boolean ``True`` value.

Outputs
-------
* CifData
    A CIF file.
* ParameterData (optional)
    Contains lines of output messages and/or errors.

Errors
------
Run-time errors are returned line-by-line in the ParameterData object.

.. rubric:: Footnotes

.. [#] Only with the ``--output-cif`` command line option.
