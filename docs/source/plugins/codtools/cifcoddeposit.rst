.. _codtools_cifcoddeposit:

codtools.cifcoddeposit
++++++++++++++++++++++

Description
-----------
This plugin is specific for ``cif_cod_deposit`` script.

Supported codes
---------------
* cif_cod_deposit

Inputs
------
* :py:class:`CifData <aiida.orm.data.cif.CifData>`
    A CIF file.
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    Contains deposition information, such as user name, password and
    deposition type:

  * ``username``: depositor's user name to access the \*COD deposition
    interface;
  * ``password``: depositor's password to access the \*COD deposition
    interface;
  * ``deposition-type``: determines a type of the deposited CIF file,
    which can be one of the following:

    * ``published``: CIF file is already published in a scientific
      paper;
    * ``prepublication``: CIF file is a prepublication material and
      should not be revealed to the public until the publication of
      a scientific paper. In this case, a ``hold_period`` also has
      to be specified;
    * ``personal``: CIF file is personal communication.

  * ``url``: URL of \*COD deposition API (optional, default URL is
    http://test.crystallography.net/cgi-bin/cif-deposit.pl);
  * ``journal``: name of the journal, where the CIF is/will be
    published;
  * ``user_email``: depositor's e-mail address;
  * ``author_name``: name of the CIF file author;
  * ``author_email``: e-mail of the CIF file author;
  * ``hold_period``: a period (in number months) for the structure to
    be kept on-hold (only for ``deposition_type == 'prepublication'``).

Outputs
-------
* :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    Contains the result of deposition:

  * ``output_messages``: lines of output messages and/or errors. For
    more information refer to
    :ref:`outputs for codtools.ciffilter plugin<codtools_ciffilter_outputs>`.
  * ``status``: a string, one of the following:

    * ``SUCCESS``: a deposition is successful, newly assigned \*COD
      number(s) is/are present in ``output_messages`` field;
    * ``DUPLICATE``: submitted data is already in the \*COD database
      thus is not deposited once more;
    * ``UNCHANGED``: the redeposition of the data is unnecessary, as
      nothing was changed in the contents of file to be replaced;
    * ``INPUTERROR``: an error, related to the input, has occurred,
      detailed reason may be present in ``output_messages`` field;
    * ``SERVERERROR``: an internal server error has occurred, detailed
      reason may be present in ``output_messages`` field;
    * ``UNKNOWN``: the result of the deposition is unknown.

Errors
------
Run-time errors are returned line-by-line in the ``output_messages`` field
of :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>` object.
