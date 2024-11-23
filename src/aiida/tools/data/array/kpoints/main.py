###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Various utilities to deal with KpointsData instances or create new ones
(e.g. band paths, kpoints from a parsed input text file, ...)
"""

from aiida.orm import Dict, KpointsData

__all__ = ('get_explicit_kpoints_path', 'get_kpoints_path')


def get_kpoints_path(structure, method='seekpath', **kwargs):
    """Returns a dictionary whose contents depend on the method but includes at least the following keys

        * parameters: Dict node

    The contents of the parameters depends on the method but contains at least the keys

        * 'point_coords': a dictionary with 'kpoints-label': [float coordinates]
        * 'path': a list of length-2 tuples, with the labels of the starting
            and ending point of each label section

    The 'seekpath' method which is the default also returns the following additional nodes

        * primitive_structure: StructureData with the primitive cell
        * conv_structure: StructureData with the conventional cell

    Note that the generated kpoints for the seekpath method only apply on the returned primitive_structure
    and not on the input structure that was provided

    :param structure: a StructureData node
    :param method: the method to use for kpoint generation, options are 'seekpath' and 'legacy'.
        It is strongly advised to use the default 'seekpath' as the 'legacy' implementation is known to have
        bugs for certain structure cells
    :param kwargs: optional keyword arguments that depend on the selected method
    :returns: dictionary as described above in the docstring
    """
    if method not in _GET_KPOINTS_PATH_METHODS:
        raise ValueError(f"the method '{method}' is not implemented")

    method = _GET_KPOINTS_PATH_METHODS[method]

    return method(structure, **kwargs)


def get_explicit_kpoints_path(structure, method='seekpath', **kwargs):
    """Returns a dictionary whose contents depend on the method but includes at least the following keys

        * parameters: Dict node
        * explicit_kpoints: KpointsData node with explicit kpoints path

    The contents of the parameters depends on the method but contains at least the keys

        * 'point_coords': a dictionary with 'kpoints-label': [float coordinates]
        * 'path': a list of length-2 tuples, with the labels of the starting
            and ending point of each label section

    The 'seekpath' method which is the default also returns the following additional nodes

        * primitive_structure: StructureData with the primitive cell
        * conv_structure: StructureData with the conventional cell

    Note that the generated kpoints for the seekpath method only apply on the returned primitive_structure
    and not on the input structure that was provided

    :param structure: a StructureData node
    :param method: the method to use for kpoint generation, options are 'seekpath' and 'legacy'.
        It is strongly advised to use the default 'seekpath' as the 'legacy' implementation is known to have
        bugs for certain structure cells
    :param kwargs: optional keyword arguments that depend on the selected method
    :returns: dictionary as described above in the docstring
    """
    if method not in _GET_EXPLICIT_KPOINTS_PATH_METHODS:
        raise ValueError(f"the method '{method}' is not implemented")

    method = _GET_EXPLICIT_KPOINTS_PATH_METHODS[method]

    return method(structure, **kwargs)


def _seekpath_get_kpoints_path(structure, **kwargs):
    """Call the get_kpoints_path wrapper function for Seekpath

    :param structure: a StructureData node
    :param with_time_reversal: if False, and the group has no inversion
        symmetry, additional lines are returned
    :param recipe: choose the reference publication that defines the special points and paths.
       Currently, the following value is implemented:

       - ``hpkot``: HPKOT paper:
         Y. Hinuma, G. Pizzi, Y. Kumagai, F. Oba, I. Tanaka, Band structure
         diagram paths based on crystallography, Comp. Mat. Sci. 128, 140 (2017).
         DOI: 10.1016/j.commatsci.2016.10.015
    :param threshold: the threshold to use to verify if we are in
        and edge case (e.g., a tetragonal cell, but ``a==c``). For instance,
        in the tI lattice, if ``abs(a-c) < threshold``, a
        :py:exc:`~seekpath.hpkot.EdgeCaseWarning` is issued.
        Note that depending on the bravais lattice, the meaning of the
        threshold is different (angle, length, ...)
    :param symprec: the symmetry precision used internally by SPGLIB
    :param angle_tolerance: the angle_tolerance used internally by SPGLIB
    """
    from aiida.tools.data.array.kpoints import seekpath

    assert structure.pbc == (True, True, True), 'Seekpath only implemented for three-dimensional structures'

    recognized_args = ['with_time_reversal', 'recipe', 'threshold', 'symprec', 'angle_tolerance']
    unknown_args = set(kwargs).difference(recognized_args)

    if unknown_args:
        raise ValueError(f'unknown arguments {unknown_args}')

    return seekpath.get_kpoints_path(structure, kwargs)


def _seekpath_get_explicit_kpoints_path(structure, **kwargs):
    """Call the get_explicit_kpoints_path wrapper function for Seekpath

    :param structure: a StructureData node
    :param with_time_reversal: if False, and the group has no inversion
        symmetry, additional lines are returned
    :param reference_distance: a reference target distance between neighboring
        k-points in the path, in units of 1/ang. The actual value will be as
        close as possible to this value, to have an integer number of points in
        each path
    :param recipe: choose the reference publication that defines the special points and paths.
       Currently, the following value is implemented:

       - ``hpkot``: HPKOT paper:
         Y. Hinuma, G. Pizzi, Y. Kumagai, F. Oba, I. Tanaka, Band structure
         diagram paths based on crystallography, Comp. Mat. Sci. 128, 140 (2017).
         DOI: 10.1016/j.commatsci.2016.10.015
    :param threshold: the threshold to use to verify if we are in
        and edge case (e.g., a tetragonal cell, but ``a==c``). For instance,
        in the tI lattice, if ``abs(a-c) < threshold``, a
        :py:exc:`~seekpath.hpkot.EdgeCaseWarning` is issued.
        Note that depending on the bravais lattice, the meaning of the
        threshold is different (angle, length, ...)
    :param symprec: the symmetry precision used internally by SPGLIB
    :param angle_tolerance: the angle_tolerance used internally by SPGLIB
    """
    from aiida.tools.data.array.kpoints import seekpath

    assert structure.pbc == (True, True, True), 'Seekpath only implemented for three-dimensional structures'

    recognized_args = ['with_time_reversal', 'reference_distance', 'recipe', 'threshold', 'symprec', 'angle_tolerance']
    unknown_args = set(kwargs).difference(recognized_args)

    if unknown_args:
        raise ValueError(f'unknown arguments {unknown_args}')

    return seekpath.get_explicit_kpoints_path(structure, kwargs)


def _legacy_get_kpoints_path(structure, **kwargs):
    """Call the get_kpoints_path of the legacy implementation

    :param structure: a StructureData node
    :param bool cartesian: if set to true, reads the coordinates eventually passed in value as cartesian coordinates
    :param epsilon_length: threshold on lengths comparison, used to get the bravais lattice info
    :param epsilon_angle: threshold on angles comparison, used to get the bravais lattice info
    """
    from aiida.tools.data.array.kpoints import legacy

    args_recognized = ['cartesian', 'epsilon_length', 'epsilon_angle']
    args_unknown = set(kwargs).difference(args_recognized)

    if args_unknown:
        raise ValueError(f'unknown arguments {args_unknown}')

    point_coords, path, bravais_info = legacy.get_kpoints_path(cell=structure.cell, pbc=structure.pbc, **kwargs)

    parameters = {
        'bravais_info': bravais_info,
        'point_coords': point_coords,
        'path': path,
    }

    return {'parameters': Dict(parameters)}


def _legacy_get_explicit_kpoints_path(structure, **kwargs):
    """Call the get_explicit_kpoints_path of the legacy implementation

    :param structure: a StructureData node
    :param float kpoint_distance: parameter controlling the distance between kpoints. Distance is
        given in crystal coordinates, i.e. the distance is computed in the space of b1, b2, b3.
        The distance set will be the closest possible to this value, compatible with the requirement
        of putting equispaced points between two special points (since extrema are included).
    :param bool cartesian: if set to true, reads the coordinates eventually passed in value as cartesian coordinates
    :param float epsilon_length: threshold on lengths comparison, used to get the bravais lattice info
    :param float epsilon_angle: threshold on angles comparison, used to get the bravais lattice info
    """
    from aiida.tools.data.array.kpoints import legacy

    args_recognized = ['value', 'kpoint_distance', 'cartesian', 'epsilon_length', 'epsilon_angle']
    args_unknown = set(kwargs).difference(args_recognized)

    if args_unknown:
        raise ValueError(f'unknown arguments {args_unknown}')

    point_coords, path, bravais_info, explicit_kpoints, labels = legacy.get_explicit_kpoints_path(
        cell=structure.cell, pbc=structure.pbc, **kwargs
    )

    kpoints = KpointsData()
    kpoints.set_cell(structure.cell)
    kpoints.set_kpoints(explicit_kpoints)
    kpoints.labels = labels

    parameters = {
        'bravais_info': bravais_info,
        'point_coords': point_coords,
        'path': path,
    }

    return {'parameters': Dict(parameters), 'explicit_kpoints': kpoints}


_GET_KPOINTS_PATH_METHODS = {
    'legacy': _legacy_get_kpoints_path,
    'seekpath': _seekpath_get_kpoints_path,
}

_GET_EXPLICIT_KPOINTS_PATH_METHODS = {
    'legacy': _legacy_get_explicit_kpoints_path,
    'seekpath': _seekpath_get_explicit_kpoints_path,
}
