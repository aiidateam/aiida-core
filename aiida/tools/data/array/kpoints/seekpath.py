# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tool to automatically determine k-points for a given structure using SeeK-path."""
import seekpath

from aiida.orm import Dict, KpointsData


def get_explicit_kpoints_path(structure, parameters):
    """
    Return the kpoint path for band structure (in scaled and absolute
    coordinates), given a crystal structure,
    using the paths proposed in the various publications (see description
    of the 'recipe' input parameter). The parameters are the same
    as get get_explicit_k_path in __init__, but here all structures are
    input and returned as AiiDA structures rather than tuples, and similarly
    k-points-related information as a AiiDA KpointsData class.

    :param structure: The AiiDA StructureData for which we want to obtain
        the suggested path.

    :param parameters: A dictionary whose key-value pairs are passed as
        additional kwargs to the ``seekpath.get_explicit_k_path`` function.

    :return: A dictionary with four nodes:

        - ``explicit_kpoints``: a KpointsData with the (explicit) kpoints
          (with labels set).

        - ``parameters``: a Dict, whose content is
          the same dictionary as returned by the ``seekpath.get_explicit_k_path`` function
          (see `seekpath documentation <https://seekpath.readthedocs.io/>`_),
          except that:

          - ``conv_lattice``, ``conv_positions``, ``conv_types``
            are removed and replaced by the ``conv_structure`` output node

          - ``primitive_lattice``, ``primitive_positions``, ``primitive_types``
            are removed and replaced by the `primitive_structure` output node

          - ``reciprocal_primitive_lattice``, ``explicit_kpoints_abs``,
            ``explicit_kpoints_rel`` and ``explicit_kpoints_labels`` are removed
            and replaced by the ``explicit_kpoints`` output node

        - ``primitive_structure``: A StructureData with the primitive structure

        - ``conv_structure``: A StructureData with the primitive structure
    """
    # pylint: disable=too-many-locals
    from aiida.tools.data.structure import spglib_tuple_to_structure, structure_to_spglib_tuple

    structure_tuple, kind_info, kinds = structure_to_spglib_tuple(structure)

    result = {}
    rawdict = seekpath.get_explicit_k_path(structure=structure_tuple, **parameters)

    # Replace primitive structure with AiiDA StructureData
    primitive_lattice = rawdict.pop('primitive_lattice')
    primitive_positions = rawdict.pop('primitive_positions')
    primitive_types = rawdict.pop('primitive_types')
    primitive_tuple = (primitive_lattice, primitive_positions, primitive_types)
    primitive_structure = spglib_tuple_to_structure(primitive_tuple, kind_info, kinds)

    # Replace conv structure with AiiDA StructureData
    conv_lattice = rawdict.pop('conv_lattice')
    conv_positions = rawdict.pop('conv_positions')
    conv_types = rawdict.pop('conv_types')
    conv_tuple = (conv_lattice, conv_positions, conv_types)
    conv_structure = spglib_tuple_to_structure(conv_tuple, kind_info, kinds)

    # Remove reciprocal_primitive_lattice, recalculated by kpoints class
    rawdict.pop('reciprocal_primitive_lattice')
    kpoints_abs = rawdict.pop('explicit_kpoints_abs')
    kpoints_labels = rawdict.pop('explicit_kpoints_labels')

    # set_kpoints expects labels like [[0,'X'],[34,'L'],...], so generate it here skipping empty labels
    labels = [[idx, label] for idx, label in enumerate(kpoints_labels) if label]
    kpoints = KpointsData()
    kpoints.set_cell_from_structure(primitive_structure)
    kpoints.set_kpoints(kpoints_abs, cartesian=True, labels=labels)

    result['parameters'] = Dict(dict=rawdict)
    result['explicit_kpoints'] = kpoints
    result['primitive_structure'] = primitive_structure
    result['conv_structure'] = conv_structure

    return result


def get_kpoints_path(structure, parameters):
    """
    Return the kpoint path information for band structure given a
    crystal structure, using the paths from the chosen recipe/reference.
    The parameters are the same
    as get get_path in __init__, but here all structures are
    input and returned as AiiDA structures rather than tuples.


    If you use this module, please cite the paper of the corresponding
    recipe (see documentation of seekpath).

    :param structure: The crystal structure for which we want to obtain
        the suggested path. It should be an AiiDA StructureData object.

    :param parameters: A dictionary whose key-value pairs are passed as
        additional kwargs to the ``seekpath.get_path`` function.

    :return: A dictionary with three nodes:

        - ``parameters``: a Dict, whose content is
          the same dictionary as returned by the ``seekpath.get_path`` function
          (see `seekpath documentation <https://seekpath.readthedocs.io/>`_),
          except that:

          - ``conv_lattice``, ``conv_positions``, ``conv_types``
            are removed and replaced by the ``conv_structure`` output node

          - ``primitive_lattice``, ``primitive_positions``, ``primitive_types``
            are removed and replaced by the ``primitive_structure`` output node

        - ``primitive_structure``: A StructureData with the primitive structure

        - ``conv_structure``: A StructureData with the primitive structure
    """
    from aiida.tools.data.structure import spglib_tuple_to_structure, structure_to_spglib_tuple

    structure_tuple, kind_info, kinds = structure_to_spglib_tuple(structure)

    result = {}
    rawdict = seekpath.get_path(structure=structure_tuple, **parameters)

    result['parameters'] = Dict(dict=rawdict)

    # Replace conv structure with AiiDA StructureData
    conv_lattice = rawdict.pop('conv_lattice')
    conv_positions = rawdict.pop('conv_positions')
    conv_types = rawdict.pop('conv_types')
    result['conv_structure'] = spglib_tuple_to_structure((conv_lattice, conv_positions, conv_types), kind_info, kinds)

    # Replace primitive structure with AiiDA StructureData
    primitive_lattice = rawdict.pop('primitive_lattice')
    primitive_positions = rawdict.pop('primitive_positions')
    primitive_types = rawdict.pop('primitive_types')
    result['primitive_structure'] = spglib_tuple_to_structure((primitive_lattice, primitive_positions, primitive_types),
                                                              kind_info, kinds)

    return result
