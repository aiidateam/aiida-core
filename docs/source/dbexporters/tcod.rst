Exporting structures to TCOD
----------------------------

Export of
:py:class:`StructureData <aiida.orm.data.structure.StructureData>` and
:py:class:`CifData <aiida.orm.data.cif.CifData>` (or any other data type,
which can be converted to them) to the
`Theoretical Crystallography Open Database`_ (TCOD) can be divided into
following workflow steps:

=== =============================== ============= ============= ======= ============
No. Description                     Input         Output        Type    Implemented?
=== =============================== ============= ============= ======= ============
0   Conversion of the StructureData StructureData CifData       Instant \+
    to CifData
1   Detection of the symmetry and   CifData       CifData       Instant \+
    reduction to the unit cell
2   Niggli reduction of the unit    CifData       CifData       Instant ---
    cell
3   Addition of structure           CifData,      CifData       Instant PW and CP
    properties (total energy,       ParameterData
    residual forces)
4   Addition of the metadata for    CifData       CifData       Instant ~
    reproduction of the results
5   Depostition to the TCOD         CifData       ParameterData Job     \+
=== =============================== ============= ============= ======= ============

Type of each step's calculation (InstantCalculation of JobCalculation) is
defined in column *Type*. Each step is described in more detail below:

* Conversion of the StructureData to CifData
    Conversion between the
    :py:class:`StructureData <aiida.orm.data.structure.StructureData>` and
    :py:class:`CifData <aiida.orm.data.cif.CifData>` is done via
    ASE atoms object.
* Detection of the symmetry and reduction to the unit cell
    Detection of the symmetry and reduction to the unit cell is performed
    using `pyspglib.spglib.refine_cell() function`_.
* Niggli reduction of the unit cell
    Reduction of the unit cell to Niggli cell is a *nice to have* feature,
    as it would allow to represent structure as an unambiguously selected
    unit cell.
* Addition of structure properties (energy, remaining forces)
    The structure properties from the calculations, such as total energy
    and residual forces can be extracted from
    :py:class:`ParameterData <aiida.orm.data.parameter.ParameterData>`
    nodes and put into related `TCOD CIF dictionaries`_ tags.
* Addition of the metadata for reproduction of the results
    Current metadata, added for reproducibility, includes scripts for
    re-running of calculations, outputs from the calculations and exported
    subset of AiiDA database. It's not quite clear what/how to record the
    metadata for calculations of type InstantCalculation.
* Depostition to the TCOD
    Deposition of the final
    :py:class:`CifData <aiida.orm.data.cif.CifData>` to the TCOD is
    performed using
    :ref:`cif_cod_deposit script from cod-tools package <codtools_cifcoddeposit>`.

.. _Theoretical Crystallography Open Database: http://www.crystallography.net/tcod/
.. _pyspglib.spglib.refine_cell() function: http://spglib.sourceforge.net/api.html#spg-refine-cell
.. _TCOD CIF dictionaries: http://www.crystallography.net/tcod/cif/dictionaries/
