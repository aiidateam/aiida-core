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
* cif_adjust_journal_name_volume
* cif_CODify
* cif_correct_tags
* cif_create_AMCSD_pressure_temp_tags
* cif_estimate_spacegroup
* cif_eval_numbers
* cif_fillcell
* cif_filter
* cif_fix_values
* cif_hkl_check
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
* :py:class:`CifData <aiida.orm.data.cif.CifData>`
    A CIF file.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
    Contains the command line parameters, specified in key-value fashion.
    Leading dashes (single or double) must be stripped from the keys.
    Values can be arrays with multiple items. Keys without values should
    point to boolean ``True`` value. In example::

        calc = Code.get_from_string('cif_filter').new_calc()
        calc.use_parameters(ParameterData(dict={
                's'                       : True,
                'exclude-empty-tags'      : True,
                'dont-reformat-spacegroup': True,
                'add-cif-header'          : [ 'standard.txt', 'user.txt' ],
                'bibliography'            : 'bibliography.cif',
            }))

    is equivallent to command line::

        cif_filter \
            -s \
            --exclude-empty-tags \
            --dont-reformat-spacegroup \
            --add-cif-header standard.txt \
            --add-cif-header user.txt \
            --bibliography bibliography.cif

    .. note:: it should be kept in mind that no escaping of Shell
      metacharacters are performed by the plugin. AiiDA encloses each
      command line argument with single quotes and that's being relied on.

.. _codtools_ciffilter_outputs:

Outputs
-------
* :py:class:`CifData <aiida.orm.data.cif.CifData>`
    A CIF file.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` (optional)
    Contains lines of output messages and/or errors. For example::

        print load_node(1, parent_class=ParameterData).get_dict()

    would print::

        {u'output_messages': [u'cif_cod_check: test.cif data_4000000: _publ_section_title is undefined']}

Errors
------
Run-time errors are returned line-by-line in the
:py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` object.

.. rubric:: Footnotes

.. [#] Only with the ``--output-cif`` command line option.
