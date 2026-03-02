###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tools to operate on `CifData` nodes."""

import io

from aiida.engine import calcfunction
from aiida.orm import CifData
from aiida.orm.implementation.utils import clean_value


class InvalidOccupationsError(Exception):
    """An exception that will be raised if pymatgen fails to parse the structure from a
    cif because some site occupancies exceed the occupancy tolerance. This often happens
    for structures that have attached species, such as hydrogen, and specify a placeholder
    position for it, leading to occupancies greater than one. Pymatgen only issues a
    warning in this case and simply does not return a structure
    """


symmetry_tags = [
    '_symmetry_equiv_pos_site_id',
    '_symmetry_equiv_pos_as_xyz',
    '_symmetry_Int_Tables_number',
    '_symmetry_space_group_name_H-M',
    '_symmetry_space_group_name_Hall',
    '_space_group_symop_id',
    '_space_group_symop_operation_xyz',
    '_space_group_symop_sg_id',
    '_space_group_id',
    '_space_group_IT_number',
    '_space_group_name_H-M_alt',
    '_space_group_name_Hall',
]


def symop_string_from_symop_matrix_tr(matrix, tr=(0, 0, 0), eps=0):
    """Construct a CIF representation of symmetry operator plus translation.
    See International Tables for Crystallography Vol. A. (2002) for
    definition.

    :param matrix: 3x3 matrix, representing the symmetry operator
    :param tr: translation vector of length 3 (default 0)
    :param eps: epsilon parameter for fuzzy comparison x == 0
    :return: CIF representation of symmetry operator
    """
    import re

    axes = ['x', 'y', 'z']
    parts = ['', '', '']
    for i in range(3):
        for j in range(3):
            sign = None
            if matrix[i][j] > eps:
                sign = '+'
            elif matrix[i][j] < -eps:
                sign = '-'
            if sign:
                parts[i] = format(f'{parts[i]}{sign}{axes[j]}')
        if tr[i] < -eps or tr[i] > eps:
            sign = '+'
            if tr[i] < -eps:
                sign = '-'
            parts[i] = format(f'{parts[i]}{sign}{abs(tr[i])}')
        parts[i] = re.sub(r'^\+', '', parts[i])
    return ','.join(parts)


@calcfunction
def _get_aiida_structure_ase_inline(cif, **kwargs):
    """Creates :py:class:`aiida.orm.nodes.data.structure.StructureData` using ASE.

    .. note:: unable to correctly import structures of alloys.
    .. note:: requires ASE module.
    """
    from aiida.orm import Dict, StructureData

    parameters = kwargs.get('parameters', {})

    if isinstance(parameters, Dict):
        # Note, if `parameters` is unstored, it might contain stored `Node` instances which might slow down the parsing
        # enormously, because each time their value is used, a database call is made to refresh the value
        parameters = clean_value(parameters.get_dict())

    parameters.pop('occupancy_tolerance', None)
    parameters.pop('site_tolerance', None)

    return {'structure': StructureData(ase=cif.get_ase(**parameters))}


@calcfunction
def _get_aiida_structure_pymatgen_inline(cif, **kwargs):
    """Creates :py:class:`aiida.orm.nodes.data.structure.StructureData` using pymatgen.

    :param occupancy_tolerance: If total occupancy of a site is between 1 and occupancy_tolerance,
        the occupancies will be scaled down to 1.
    :param site_tolerance: This tolerance is used to determine if two sites are sitting in the same position,
        in which case they will be combined to a single disordered site. Defaults to 1e-4.

    .. note:: requires pymatgen module.
    """
    from pymatgen.io.cif import CifParser

    from aiida.orm import Dict, StructureData

    parameters = kwargs.get('parameters', {})

    if isinstance(parameters, Dict):
        # Note, if `parameters` is unstored, it might contain stored `Node` instances which might slow down the parsing
        # enormously, because each time their value is used, a database call is made to refresh the value
        parameters = clean_value(parameters.get_dict())

    constructor_kwargs = {}

    parameters['primitive'] = parameters.pop('primitive_cell', False)

    for argument in ['occupancy_tolerance', 'site_tolerance']:
        if argument in parameters:
            constructor_kwargs[argument] = parameters.pop(argument)

    with cif.open() as handle:
        # CifParser can only accept StringIO streams.
        parser = CifParser(io.StringIO(handle.read()), **constructor_kwargs)

    try:
        structures = parser.parse_structures(**parameters)
    except ValueError:
        # Verify whether the failure was due to wrong occupancy numbers
        try:
            constructor_kwargs['occupancy_tolerance'] = 1e10
            with cif.open() as handle:
                parser = CifParser(handle, **constructor_kwargs)
            structures = parser.get_structures(**parameters)
        except ValueError:
            # If it still fails, the occupancies were not the reason for failure
            raise ValueError('pymatgen failed to provide a structure from the cif file') from ValueError
        else:
            # If it now succeeds, non-unity occupancies were the culprit
            raise InvalidOccupationsError(
                'detected atomic sites with an occupation number larger than the occupation tolerance'
            ) from ValueError

    return {'structure': StructureData(pymatgen_structure=structures[0])}


@calcfunction
def refine_inline(node):
    """Refine (reduce) the cell of :py:class:`aiida.orm.nodes.data.cif.CifData`,
    find and remove symmetrically equivalent atoms.

    :param node: a :py:class:`aiida.orm.nodes.data.cif.CifData` instance.
    :return: dict with :py:class:`aiida.orm.nodes.data.cif.CifData`

    .. note:: can be used as inline calculation.
    """
    from aiida.orm.nodes.data.structure import StructureData, ase_refine_cell

    if len(node.values.keys()) > 1:
        raise ValueError(
            'CifData seems to contain more than one data ' 'block -- multiblock CIF files are not ' 'supported yet'
        )

    name = next(iter(node.values.keys()))

    original_atoms = node.get_ase(index=None)
    if len(original_atoms) > 1:
        raise ValueError(
            'CifData seems to contain more than one crystal ' 'structure -- such refinement is not supported ' 'yet'
        )

    original_atoms = original_atoms[0]

    refined_atoms, symmetry = ase_refine_cell(original_atoms)

    cif = CifData(ase=refined_atoms)
    if name != str(0):
        cif.values.rename(str(0), name)

    # Remove all existing symmetry tags before overwriting:
    for tag in symmetry_tags:
        cif.values[name].RemoveCifItem(tag)

    cif.values[name]['_symmetry_space_group_name_H-M'] = symmetry['hm']
    cif.values[name]['_symmetry_space_group_name_Hall'] = symmetry['hall']
    cif.values[name]['_symmetry_Int_Tables_number'] = symmetry['tables']
    cif.values[name]['_symmetry_equiv_pos_as_xyz'] = [
        symop_string_from_symop_matrix_tr(symmetry['rotations'][i], symmetry['translations'][i])
        for i in range(len(symmetry['rotations']))
    ]

    # Summary formula has to be calculated from non-reduced set of atoms.
    cif.values[name]['_chemical_formula_sum'] = StructureData(ase=original_atoms).get_formula(
        mode='hill', separator=' '
    )

    # If the number of reduced atoms multiplies the number of non-reduced
    # atoms, the new Z value can be calculated.
    if '_cell_formula_units_Z' in node.values[name].keys():
        old_Z = node.values[name]['_cell_formula_units_Z']  # noqa: N806
        if len(original_atoms) % len(refined_atoms):
            new_Z = old_Z * len(original_atoms) // len(refined_atoms)  # noqa: N806
            cif.values[name]['_cell_formula_units_Z'] = new_Z

    return {'cif': cif}
