TCOD database exporter
----------------------

TCOD database exporter is used to export computation results of
:py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`,
:py:class:`CifData <aiida.orm.nodes.data.cif.CifData>` and
:py:class:`TrajectoryData <aiida.orm.nodes.data.array.trajectory.TrajectoryData>`
(or any other data type, which can be converted to them) to the
`Theoretical Crystallography Open Database`_ (TCOD).

.. note:: The TCOD also accepts a number of code-specific outputs.
   The corresponding :py:mod:`~aiida.tools.dbexporters.tcod_plugins` live
   typically in other repositories, see e.g. the 
   `TCOD pluginf for Quantum ESPRESSO <http://aiida-quantumespresso.readthedocs.io/en/latest/module_guide/tcod_dbexporter.html#pw>`_.

Setup
+++++

To be able to export data to TCOD, one has to
:ref:`install the atomic_tools dependencies to enable CIF manipulation <install_optional_dependencies>`
as well as the `aiida-codtools <https://github.com/aiidateam/aiida-codtools>`_ plugin, and set up an
AiiDA :py:class:`Code <aiida.orm.nodes.data.code.Code>` for ``cif_cod_deposit`` script
from **cod-tools**.

How to deposit a structure
++++++++++++++++++++++++++

Best way to deposit data is to use the command line interface::

    verdi data DATATYPE deposit --database tcod
                                     [--type {published,prepublication,personal}]
                                     [--username USERNAME] [--password]
                                     [--user-email USER_EMAIL] [--title TITLE]
                                     [--author-name AUTHOR_NAME]
                                     [--author-email AUTHOR_EMAIL] [--url URL]
                                     [--code CODE_LABEL]
                                     [--computer COMPUTER_NAME]
                                     [--replace REPLACE] [-m MESSAGE]
                                     [--reduce-symmetry] [--no-reduce-symmetry]
                                     [--parameter-data PARAMETER_DATA]
                                     [--dump-aiida-database]
                                     [--no-dump-aiida-database]
                                     [--exclude-external-contents]
                                     [--no-exclude-external-contents] [--gzip]
                                     [--no-gzip]
                                     [--gzip-threshold GZIP_THRESHOLD]
                                     PK

Where:

* ``DATATYPE`` -- one of AiiDA structural data types (at the moment of
  writing, these are
  ``structure`` for :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`,
  ``cif`` for :py:class:`CifData <aiida.orm.nodes.data.cif.CifData>` and
  ``trajectory`` for :py:class:`TrajectoryData <aiida.orm.nodes.data.array.trajectory.TrajectoryData>`);
* ``TITLE`` -- the title of the publication, where the exported data
  is/will be published; in case of personal communication, the title
  should be chosen so as to reflect the exported dataset the best;
* ``CODE_LABEL`` -- label of AiiDA :py:class:`Code <aiida.orm.nodes.data.code.Code>`,
  associated with *cif_cod_deposit*;
* ``COMPUTER_NAME`` -- name of AiiDA
  :py:class:`Computer <aiida.orm.Computer>`, where
  *cif_cod_deposit* script is to be launched;
* ``REPLACE`` -- `TCOD ID`_ of the replaced entry in the event of
  redeposition;
* ``MESSAGE`` -- string to describe changes for redeposited structures;
* ``--reduce-symmetry``, ``--no-reduce-symmetry`` -- turn on/off symmetry
  reduction of the exported structure (on by default);
* ``--parameter-data`` -- specify the PK of
  :py:class:`Dict <aiida.orm.nodes.data.dict.Dict>`
  object, describing the result of the final (or single) calculation step
  of the workflow;
* ``--dump-aiida-database``, ``--no-dump-aiida-database`` -- turn on/off
  addition of relevant AiiDA database dump (on by default).

  .. warning:: Be aware that TCOD is an **open** database, thus **no
    copyright-protected data should be deposited** unless permission is
    given by the owner of the rights.

  .. note:: Data, which is deposited as pre-publication material, **will
    be kept private on TCOD server** and will not be disclosed to anyone
    without depositor's permission.

* ``--exclude-external-contents``, ``--no-exclude-external-contents`` --
  exclude contents of initial input files, that contain
  :py:class:`source <aiida.orm.nodes.data.data.Data.source>` property with
  definitions on how to obtain the contents from external resources (on
  by default);
* ``--gzip``, `--no-gzip`` -- turn on/off gzip compression for large
  files (off by default); ``--gzip-threshold`` sets the minimum file size
  to be compressed.

Other command line options correspond to the options of `cifcoddeposit` class of the `aiida-codtools plugin.
To ease the use of TCOD exporter, one can define persistent
parameters in :doc:`AiiDA properties <../verdi/properties>`. Corresponding
command line parameters and AiiDA properties are presented in the table:

======================  ===========================
Command line parameter  AiiDA property
======================  ===========================
``--author-email``      tcod.depositor_author_email
``--author-name``       tcod.depositor_author_name
``--user-email``        tcod.depositor_email
``--username``          tcod.depositor_password
``--password``          tcod.depositor_username
======================  ===========================

.. note:: ``--password`` does not accept any value; instead, the option
    will prompt the user to enter one's password in the terminal.

.. note:: Command line parameters can be used to override AiiDA
    properties even if properties are set.

Return values
+++++++++++++

The deposition process, which is of
:py:class:`CalcJobNode <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`
type, returns the output of ``cif_cod_deposit``, wrapped in
:py:class:`Dict <aiida.orm.nodes.data.dict.Dict>`.

Citing
++++++

If you use the TCOD database exporter, please cite the following work:

.. highlights:: Andrius Merkys, Nicolas Mounet, Andrea Cepellotti,
  Nicola Marzari, Saulius Gražulis and Giovanni Pizzi, *A posteriori
  metadata from automated provenance tracking: Integration of AiiDA
  and TCOD*, Journal of Cheminformatics 9, 56 (2017);
  http://doi.org/10.1186/s13321-017-0242-y.

.. _Theoretical Crystallography Open Database: http://www.crystallography.net/tcod/
.. _TCOD deposition type: http://wiki.crystallography.net/deposition_type/
.. _TCOD ID: http://wiki.crystallography.net/tcod_id/
