# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tool to automatically determine k-points for a given structure using legacy custom implementation."""
# pylint: disable=too-many-lines,fixme,invalid-name,too-many-arguments,too-many-locals,eval-used,use-a-generator
import numpy

_default_epsilon_length = 1e-5
_default_epsilon_angle = 1e-5


def change_reference(reciprocal_cell, kpoints, to_cartesian=True):
    """
    Change reference system, from cartesian to crystal coordinates (units of b1,b2,b3) or viceversa.

    :param reciprocal_cell: a 3x3 array representing the cell lattice vectors in reciprocal space
    :param kpoints: a list of (3) point coordinates
    :return kpoints: a list of (3) point coordinates in the new reference
    """
    if not isinstance(kpoints, numpy.ndarray):
        raise ValueError('kpoints must be a numpy.array')

    transposed_cell = numpy.transpose(numpy.array(reciprocal_cell))
    if to_cartesian:
        matrix = transposed_cell
    else:
        matrix = numpy.linalg.inv(transposed_cell)

    # note: kpoints is a list Nx3, matrix is 3x3.
    # hence, first transpose kpoints, then multiply, finally transpose it back
    return numpy.transpose(numpy.dot(matrix, numpy.transpose(kpoints)))


def analyze_cell(cell=None, pbc=None):
    """
    A function executed by the __init__ or by set_cell.
    If a cell is set, properties like a1, a2, a3, cosalpha, reciprocal_cell are
    set as well, although they are not stored in the DB.
    :note: units are Angstrom for the cell parameters, 1/Angstrom for the
    reciprocal cell parameters.
    """
    if pbc is None:
        pbc = [True, True, True]

    dimension = sum(pbc)

    if cell is None:
        return {'reciprocal_cell': None, 'dimension': dimension, 'pbc': pbc}

    the_cell = numpy.array(cell)
    reciprocal_cell = 2. * numpy.pi * numpy.linalg.inv(the_cell).transpose()
    a1 = numpy.array(the_cell[0, :])  # units = Angstrom
    a2 = numpy.array(the_cell[1, :])  # units = Angstrom
    a3 = numpy.array(the_cell[2, :])  # units = Angstrom
    a = numpy.linalg.norm(a1)  # units = Angstrom
    b = numpy.linalg.norm(a2)  # units = Angstrom
    c = numpy.linalg.norm(a3)  # units = Angstrom
    b1 = reciprocal_cell[0, :]  # units = 1/Angstrom
    b2 = reciprocal_cell[1, :]  # units = 1/Angstrom
    b3 = reciprocal_cell[2, :]  # units = 1/Angstrom
    cosalpha = numpy.dot(a2, a3) / b / c
    cosbeta = numpy.dot(a3, a1) / c / a
    cosgamma = numpy.dot(a1, a2) / a / b

    result = {
        'a1': a1,
        'a2': a2,
        'a3': a3,
        'a': a,
        'b': b,
        'c': c,
        'b1': b1,
        'b2': b2,
        'b3': b3,
        'cosalpha': cosalpha,
        'cosbeta': cosbeta,
        'cosgamma': cosgamma,
        'dimension': dimension,
        'reciprocal_cell': reciprocal_cell,
        'pbc': pbc,
    }

    return result


def get_explicit_kpoints_path(
    value=None,
    cell=None,
    pbc=None,
    kpoint_distance=None,
    cartesian=False,
    epsilon_length=_default_epsilon_length,
    epsilon_angle=_default_epsilon_angle
):
    """
    Set a path of kpoints in the Brillouin zone.

    :param value: description of the path, in various possible formats.

        None: automatically sets all irreducible high symmetry paths.
        Requires that a cell was set

        or::

          [('G','M'), (...), ...]
          [('G','M',30), (...), ...]
          [('G',(0,0,0),'M',(1,1,1)), (...), ...]
          [('G',(0,0,0),'M',(1,1,1),30), (...), ...]

    :param cell: 3x3 array representing the structure cell lattice vectors
    :param pbc: 3-dimensional array of booleans signifying the periodic boundary
        conditions along each lattice vector
    :param float kpoint_distance: parameter controlling the distance between
        kpoints. Distance is given in crystal coordinates, i.e. the distance
        is computed in the space of b1,b2,b3. The distance set will be the
        closest possible to this value, compatible with the requirement of
        putting equispaced points between two special points (since extrema
        are included).
    :param bool cartesian: if set to true, reads the coordinates eventually
        passed in value as cartesian coordinates. Default: False.
    :param float epsilon_length: threshold on lengths comparison, used
        to get the bravais lattice info. It has to be used if the
        user wants to be sure the right symmetries are recognized.
    :param float epsilon_angle: threshold on angles comparison, used
        to get the bravais lattice info. It has to be used if the
        user wants to be sure the right symmetries are recognized.

    :returns: point_coordinates, path, bravais_info, explicit_kpoints, labels
    """
    # pylint: disable=too-many-branches,too-many-statements
    bravais_info = find_bravais_info(cell=cell, pbc=pbc, epsilon_length=epsilon_length, epsilon_angle=epsilon_angle)

    analysis = analyze_cell(cell, pbc)
    dimension = analysis['dimension']
    reciprocal_cell = analysis['reciprocal_cell']
    pbc = list(analysis['pbc'])

    if dimension == 0:
        # case with zero dimension: only gamma-point is set
        return [[0., 0., 0.]], None, bravais_info

    def _is_path_1(path):
        try:
            are_two = all([len(i) == 2 for i in path])
            if not are_two:
                return False

            for i in path:
                are_str = all([isinstance(b, str) for b in i])
                if not are_str:
                    return False
        except IndexError:
            return False
        return True

    def _is_path_2(path):
        try:
            are_three = all([len(i) == 3 for i in path])
            if not are_three:
                return False

            are_good = all([all([isinstance(b[0], str), isinstance(b[1], str), isinstance(b[2], int)]) for b in path])
            if not are_good:
                return False

            # check that at least two points per segment (beginning and end)
            points_num = [int(i[2]) for i in path]
            if any([i < 2 for i in points_num]):
                raise ValueError('Must set at least two points per path segment')

        except IndexError:
            return False
        return True

    def _is_path_3(path):
        # [('G',(0,0,0),'M',(1,1,1)), (...), ...]
        try:
            _ = len(path)
            are_four = all([len(i) == 4 for i in path])
            if not are_four:
                return False
            have_labels = all(all([isinstance(i[0], str), isinstance(i[2], str)]) for i in path)
            if not have_labels:
                return False
            for i in path:
                coord1 = [float(j) for j in i[1]]
                coord2 = [float(j) for j in i[3]]
                if len(coord1) != 3 or len(coord2) != 3:
                    return False
        except (TypeError, IndexError):
            return False
        return True

    def _is_path_4(path):
        # [('G',(0,0,0),'M',(1,1,1),30), (...), ...]
        try:
            _ = len(path)
            are_five = all([len(i) == 5 for i in path])
            if not are_five:
                return False
            have_labels = all(all([isinstance(i[0], str), isinstance(i[2], str)]) for i in path)
            if not have_labels:
                return False
            have_points_num = all([isinstance(i[4], int) for i in path])
            if not have_points_num:
                return False
            # check that at least two points per segment (beginning and end)
            points_num = [int(i[4]) for i in path]
            if any([i < 2 for i in points_num]):
                raise ValueError('Must set at least two points per path segment')
            for i in path:
                coord1 = [float(j) for j in i[1]]
                coord2 = [float(j) for j in i[3]]
                if len(coord1) != 3 or len(coord2) != 3:
                    return False
        except (TypeError, IndexError):
            return False
        return True

    def _num_points_from_coordinates(path, point_coordinates, kpoint_distance=None):
        # NOTE: this way of creating intervals ensures equispaced objects
        #       in crystal coordinates of b1,b2,b3
        distances = [
            numpy.linalg.norm(numpy.array(point_coordinates[i[0]]) - numpy.array(point_coordinates[i[1]])) for i in path
        ]

        if kpoint_distance is None:
            # Use max_points_per_interval as the default guess for automatically
            # guessing the number of points
            max_point_per_interval = 10
            max_interval = max(distances)
            try:
                points_per_piece = [max(2, max_point_per_interval * i // max_interval) for i in distances]
            except ValueError:
                raise ValueError('The beginning and end of each segment in the path should be different.')

        else:
            points_per_piece = [max(2, int(distance // kpoint_distance)) for distance in distances]
        return points_per_piece

    if cartesian:
        if cell is None:
            raise ValueError('To use cartesian coordinates, a cell must be provided')

    if kpoint_distance is not None:
        if kpoint_distance <= 0.:
            raise ValueError('kpoints_distance must be a positive float')

    if value is None:
        if cell is None:
            raise ValueError('Cannot set a path not even knowing the kpoints or at least the cell')
        point_coordinates, path, bravais_info = get_kpoints_path(
            cell=cell, pbc=pbc, cartesian=cartesian, epsilon_length=epsilon_length, epsilon_angle=epsilon_angle
        )
        num_points = _num_points_from_coordinates(path, point_coordinates, kpoint_distance)

    elif _is_path_1(value):
        # in the form [('X','M'),(...),...]
        if cell is None:
            raise ValueError('Cannot set a path not even knowing the kpoints or at least the cell')

        path = value
        point_coordinates, _, bravais_info = get_kpoints_path(
            cell=cell, pbc=pbc, cartesian=cartesian, epsilon_length=epsilon_length, epsilon_angle=epsilon_angle
        )
        num_points = _num_points_from_coordinates(path, point_coordinates, kpoint_distance)

    elif _is_path_2(value):
        # [('G','M',30), (...), ...]
        if cell is None:
            raise ValueError('Cannot set a path not even knowing the kpoints or at least the cell')

        path = [(i[0], i[1]) for i in value]
        point_coordinates, _, bravais_info = get_kpoints_path(
            cell=cell, pbc=pbc, cartesian=cartesian, epsilon_length=epsilon_length, epsilon_angle=epsilon_angle
        )
        num_points = [i[2] for i in value]

    elif _is_path_3(value):
        # [('G',(0,0,0),'M',(1,1,1)), (...), ...]
        path = [(i[0], i[2]) for i in value]

        point_coordinates = {}
        for piece in value:
            if piece[0] in point_coordinates:
                if point_coordinates[piece[0]] != piece[1]:
                    raise ValueError('Different points cannot have the same label')
            else:
                if cartesian:
                    point_coordinates[
                        piece[0]] = change_reference(reciprocal_cell, numpy.array([piece[1]]), to_cartesian=False)[0]
                else:
                    point_coordinates[piece[0]] = piece[1]
            if piece[2] in point_coordinates:
                if point_coordinates[piece[2]] != piece[3]:
                    raise ValueError('Different points cannot have the same label')
            else:
                if cartesian:
                    point_coordinates[
                        piece[2]] = change_reference(reciprocal_cell, numpy.array([piece[3]]), to_cartesian=False)[0]
                else:
                    point_coordinates[piece[2]] = piece[3]

        num_points = _num_points_from_coordinates(path, point_coordinates, kpoint_distance)

    elif _is_path_4(value):
        # [('G',(0,0,0),'M',(1,1,1),30), (...), ...]
        path = [(i[0], i[2]) for i in value]

        point_coordinates = {}
        for piece in value:
            if piece[0] in point_coordinates:
                if point_coordinates[piece[0]] != piece[1]:
                    raise ValueError('Different points cannot have the same label')
            else:
                if cartesian:
                    point_coordinates[
                        piece[0]] = change_reference(reciprocal_cell, numpy.array([piece[1]]), to_cartesian=False)[0]
                else:
                    point_coordinates[piece[0]] = piece[1]
            if piece[2] in point_coordinates:
                if point_coordinates[piece[2]] != piece[3]:
                    raise ValueError('Different points cannot have the same label')
            else:
                if cartesian:
                    point_coordinates[
                        piece[2]] = change_reference(reciprocal_cell, numpy.array([piece[3]]), to_cartesian=False)[0]
                else:
                    point_coordinates[piece[2]] = piece[3]

        num_points = [i[4] for i in value]

    else:
        raise ValueError('Input format not recognized')

    explicit_kpoints = [tuple(point_coordinates[path[0][0]])]
    labels = [(0, path[0][0])]

    assert all([_.is_integer() for _ in num_points if isinstance(_, (float, numpy.float64))]
               ), f'Could not determine number of points as a whole number. num_points={num_points}'
    num_points = [int(_) for _ in num_points]

    for count_piece, i in enumerate(path):
        ini_label = i[0]
        end_label = i[1]
        ini_coord = point_coordinates[ini_label]
        end_coord = point_coordinates[end_label]

        path_piece = list(
            zip(
                numpy.linspace(ini_coord[0], end_coord[0], num_points[count_piece]),
                numpy.linspace(ini_coord[1], end_coord[1], num_points[count_piece]),
                numpy.linspace(ini_coord[2], end_coord[2], num_points[count_piece]),
            )
        )

        for count, j in enumerate(path_piece):
            if all(numpy.array(explicit_kpoints[-1]) == j):
                continue  # avoid duplcates

            explicit_kpoints.append(j)

            # add labels for the first and last point
            if count == 0:
                labels.append((len(explicit_kpoints) - 1, ini_label))
            if count == len(path_piece) - 1:
                labels.append((len(explicit_kpoints) - 1, end_label))

    # I still have some duplicates in the labels: eliminate them
    sorted(set(labels), key=lambda x: x[0])

    return point_coordinates, path, bravais_info, explicit_kpoints, labels


def find_bravais_info(cell, pbc, epsilon_length=_default_epsilon_length, epsilon_angle=_default_epsilon_angle):
    """
    Finds the Bravais lattice of the cell passed in input to the Kpoint class
    :note: We assume that the cell given by the cell property is the
    primitive unit cell.

    .. note:: in 3D, this implementation expects
       that the structure is already standardized according to the Setyawan
       paper. If this is not the case, the kpoints and band structure returned will be incorrect. The only case
       that is dealt correctly by the library is the case when axes are swapped, where the library correctly
       takes this swapping/rotation into account to assign kpoint labels and coordinates.


    :param cell: 3x3 array representing the structure cell lattice vectors
    :param pbc: 3-dimensional array of booleans signifying the periodic boundary
        conditions along each lattice vector
        passed in value as cartesian coordinates. Default: False.
    :param float epsilon_length: threshold on lengths comparison, used
        to get the bravais lattice info. It has to be used if the
        user wants to be sure the right symmetries are recognized.
    :param float epsilon_angle: threshold on angles comparison, used
        to get the bravais lattice info. It has to be used if the
        user wants to be sure the right symmetries are recognized.
    :return: a dictionary, with keys short_name, extended_name, index
            (index of the Bravais lattice), and sometimes variation (name of
            the variation of the Bravais lattice) and extra (a dictionary
            with extra parameters used by the get_kpoints_path method)
    """
    # pylint: disable=too-many-branches,too-many-statements
    if cell is None:
        return None

    analysis = analyze_cell(cell, pbc)
    a1 = analysis['a1']
    a2 = analysis['a2']
    a3 = analysis['a3']
    a = analysis['a']
    b = analysis['b']
    c = analysis['c']
    cosa = analysis['cosalpha']
    cosb = analysis['cosbeta']
    cosc = analysis['cosgamma']
    dimension = analysis['dimension']
    pbc = list(pbc)

    # values of cosines at various angles
    _90 = 0.
    _60 = 0.5
    _30 = numpy.sqrt(3.) / 2.
    _120 = -0.5

    # NOTE: in what follows, I'm assuming the textbook order of alfa, beta and gamma

    # TODO: Maybe additional checks to see if the "correct" primitive
    # cell is used ? (there are other equivalent primitive
    # unit cells to the one expected here, typically for body-, c-, and
    # face-centered lattices)

    def l_are_equals(a, b):
        # function to compare lengths
        return abs(a - b) <= epsilon_length

    def a_are_equals(a, b):
        # function to compare angles (actually, cosines)
        return abs(a - b) <= epsilon_angle

    if dimension == 3:
        # =========================================#
        # 3D case -> 14 possible Bravais lattices #
        # =========================================#

        comparison_length = [l_are_equals(a, b), l_are_equals(b, c), l_are_equals(c, a)]
        comparison_angles = [a_are_equals(cosa, cosb), a_are_equals(cosb, cosc), a_are_equals(cosc, cosa)]

        if comparison_length.count(True) == 3:

            # needed for the body centered orthorhombic:
            orci_a = numpy.linalg.norm(a2 + a3)
            orci_b = numpy.linalg.norm(a1 + a3)
            orci_c = numpy.linalg.norm(a1 + a2)
            orci_the_a, orci_the_b, orci_the_c = sorted([orci_a, orci_b, orci_c])
            bco1 = -(-orci_the_a**2 + orci_the_b**2 + orci_the_c**2) / (4. * a**2)
            bco2 = -(orci_the_a**2 - orci_the_b**2 + orci_the_c**2) / (4. * a**2)
            bco3 = -(orci_the_a**2 + orci_the_b**2 - orci_the_c**2) / (4. * a**2)

            # ======================#
            # simple cubic lattice #
            # ======================#
            if comparison_angles.count(True) == 3 and a_are_equals(cosa, _90):
                bravais_info = {'short_name': 'cub', 'extended_name': 'cubic', 'index': 1, 'permutation': [0, 1, 2]}
            # =====================#
            # face centered cubic #
            # =====================#
            elif comparison_angles.count(True) == 3 and a_are_equals(cosa, _60):
                bravais_info = {
                    'short_name': 'fcc',
                    'extended_name': 'face centered cubic',
                    'index': 2,
                    'permutation': [0, 1, 2]
                }
            # =====================#
            # body centered cubic #
            # =====================#
            elif comparison_angles.count(True) == 3 and a_are_equals(cosa, -1. / 3.):
                bravais_info = {
                    'short_name': 'bcc',
                    'extended_name': 'body centered cubic',
                    'index': 3,
                    'permutation': [0, 1, 2]
                }
            # ==============#
            # rhombohedral #
            # ==============#
            elif comparison_angles.count(True) == 3:
                # logical order is important, this check must come after the cubic cases
                bravais_info = {
                    'short_name': 'rhl',
                    'extended_name': 'rhombohedral',
                    'index': 11,
                    'permutation': [0, 1, 2]
                }
                if cosa > 0.:
                    bravais_info['variation'] = 'rhl1'
                    eta = (1. + 4. * cosa) / (2. + 4. * cosa)
                    bravais_info['extra'] = {
                        'eta': eta,
                        'nu': 0.75 - eta / 2.,
                    }
                else:
                    bravais_info['variation'] = 'rhl2'
                    eta = 1. / (2. * (1. - cosa) / (1. + cosa))
                    bravais_info['extra'] = {
                        'eta': eta,
                        'nu': 0.75 - eta / 2.,
                    }

            # ==========================#
            # body centered tetragonal #
            # ==========================#
            elif comparison_angles.count(True) == 1:  # two angles are the same
                bravais_info = {
                    'short_name': 'bct',
                    'extended_name': 'body centered tetragonal',
                    'index': 5,
                }
                if comparison_angles.index(True) == 0:  # alfa=beta
                    ref_ang = cosa
                    bravais_info['permutation'] = [0, 1, 2]
                elif comparison_angles.index(True) == 1:  # beta=gamma
                    ref_ang = cosb
                    bravais_info['permutation'] = [2, 0, 1]
                else:  # comparison_angles.index(True)==2: # gamma = alfa
                    ref_ang = cosc
                    bravais_info['permutation'] = [1, 2, 0]

                if ref_ang >= 0.:
                    raise ValueError('Problems on the definition of body centered tetragonal lattices')
                the_c = numpy.sqrt(-4. * ref_ang * (a**2))
                the_a = numpy.sqrt(2. * a**2 - (the_c**2) / 2.)

                if the_c < the_a:
                    bravais_info['variation'] = 'bct1'
                    bravais_info['extra'] = {'eta': (1. + (the_c / the_a)**2) / 4.}
                else:
                    bravais_info['variation'] = 'bct2'
                    bravais_info['extra'] = {
                        'eta': (1. + (the_a / the_c)**2) / 4.,
                        'csi': ((the_a / the_c)**2) / 2.,
                    }

            # ============================#
            # body centered orthorhombic #
            # ============================#
            elif (
                any([a_are_equals(cosa, bco1),
                     a_are_equals(cosb, bco1),
                     a_are_equals(cosc, bco1)]) and
                any([a_are_equals(cosa, bco2),
                     a_are_equals(cosb, bco2),
                     a_are_equals(cosc, bco2)]) and
                any([a_are_equals(cosa, bco3),
                     a_are_equals(cosb, bco3),
                     a_are_equals(cosc, bco3)])
            ):
                bravais_info = {
                    'short_name': 'orci',
                    'extended_name': 'body centered orthorhombic',
                    'index': 8,
                }
                if a_are_equals(cosa, bco1) and a_are_equals(cosc, bco3):
                    bravais_info['permutation'] = [0, 1, 2]
                if a_are_equals(cosa, bco1) and a_are_equals(cosc, bco2):
                    bravais_info['permutation'] = [0, 2, 1]
                if a_are_equals(cosa, bco3) and a_are_equals(cosc, bco2):
                    bravais_info['permutation'] = [1, 2, 0]
                if a_are_equals(cosa, bco2) and a_are_equals(cosc, bco3):
                    bravais_info['permutation'] = [1, 0, 2]
                if a_are_equals(cosa, bco2) and a_are_equals(cosc, bco1):
                    bravais_info['permutation'] = [2, 0, 1]
                if a_are_equals(cosa, bco3) and a_are_equals(cosc, bco1):
                    bravais_info['permutation'] = [2, 1, 0]

                bravais_info['extra'] = {
                    'csi': (1. + (orci_the_a / orci_the_c)**2) / 4.,
                    'eta': (1. + (orci_the_b / orci_the_c)**2) / 4.,
                    'dlt': (orci_the_b**2 - orci_the_a**2) / (4. * orci_the_c**2),
                    'mu': (orci_the_a**2 + orci_the_b**2) / (4. * orci_the_c**2),
                }

            # if it doesn't fall in the above, is triclinic
            else:
                bravais_info = {
                    'short_name': 'tri',
                    'extended_name': 'triclinic',
                    'index': 14,
                }
                # the check for triclinic variations is at the end of the method

        elif comparison_length.count(True) == 1:

            # ============#
            # tetragonal #
            # ============#
            if comparison_angles.count(True) == 3 and a_are_equals(cosa, _90):
                bravais_info = {
                    'short_name': 'tet',
                    'extended_name': 'tetragonal',
                    'index': 4,
                }
                if comparison_length[0]:
                    bravais_info['permutation'] = [0, 1, 2]
                if comparison_length[1]:
                    bravais_info['permutation'] = [2, 0, 1]
                if comparison_length[2]:
                    bravais_info['permutation'] = [1, 2, 0]
            # ====================================#
            # c-centered orthorombic + hexagonal #
            # ====================================#
            # alpha/=beta=gamma=pi/2
            elif (
                comparison_angles.count(True) == 1 and
                any([a_are_equals(cosa, _90), a_are_equals(cosb, _90),
                     a_are_equals(cosc, _90)])
            ):
                if any([a_are_equals(cosa, _120), a_are_equals(cosb, _120), a_are_equals(cosc, _120)]):
                    bravais_info = {
                        'short_name': 'hex',
                        'extended_name': 'hexagonal',
                        'index': 10,
                    }
                else:
                    bravais_info = {
                        'short_name': 'orcc',
                        'extended_name': 'c-centered orthorhombic',
                        'index': 9,
                    }
                    if comparison_length[0]:
                        the_a1 = a1
                        the_a2 = a2
                    elif comparison_length[1]:
                        the_a1 = a2
                        the_a2 = a3
                    else:  # comparison_length[2]==True:
                        the_a1 = a3
                        the_a2 = a1
                    the_a = numpy.linalg.norm(the_a1 + the_a2)
                    the_b = numpy.linalg.norm(the_a1 - the_a2)
                    bravais_info['extra'] = {
                        'csi': (1. + (the_a / the_b)**2) / 4.,
                    }

                # TODO : re-check this case, permutations look weird
                if comparison_length[0]:
                    bravais_info['permutation'] = [0, 1, 2]
                if comparison_length[1]:
                    bravais_info['permutation'] = [2, 0, 1]
                if comparison_length[2]:
                    bravais_info['permutation'] = [1, 2, 0]
            # =======================#
            # c-centered monoclinic #
            # =======================#
            elif comparison_angles.count(True) == 1:
                bravais_info = {
                    'short_name': 'mclc',
                    'extended_name': 'c-centered monoclinic',
                    'index': 13,
                }
                # TODO : re-check this case, permutations look weird
                if comparison_length[0]:
                    bravais_info['permutation'] = [0, 1, 2]
                    the_ka = cosa
                    the_a1 = a1
                    the_a2 = a2
                    the_c = c
                if comparison_length[1]:
                    bravais_info['permutation'] = [2, 0, 1]
                    the_ka = cosb
                    the_a1 = a2
                    the_a2 = a3
                    the_c = a
                if comparison_length[2]:
                    bravais_info['permutation'] = [1, 2, 0]
                    the_ka = cosc
                    the_a1 = a3
                    the_a2 = a1
                    the_c = b

                the_b = numpy.linalg.norm(the_a1 + the_a2)
                the_a = numpy.linalg.norm(the_a1 - the_a2)
                the_cosa = 2. * numpy.linalg.norm(the_a1) / the_b * the_ka

                if a_are_equals(the_ka, _90):  # order matters: has to be before the check on mclc1
                    bravais_info['variation'] = 'mclc2'
                    csi = (2. - the_b * the_cosa / the_c) / (4. * (1. - the_cosa**2))
                    psi = 0.75 - the_a**2 / (4. * the_b * (1. - the_cosa**2))
                    bravais_info['extra'] = {
                        'csi': csi,
                        'eta': 0.5 + 2. * csi * the_c * the_cosa / the_b,
                        'psi': psi,
                        'phi': psi + (0.75 - psi) * the_b * the_cosa / the_c,
                    }
                elif the_ka < 0.:
                    bravais_info['variation'] = 'mclc1'
                    csi = (2. - the_b * the_cosa / the_c) / (4. * (1. - the_cosa**2))
                    psi = 0.75 - the_a**2 / (4. * the_b * (1. - the_cosa**2))
                    bravais_info['extra'] = {
                        'csi': csi,
                        'eta': 0.5 + 2. * csi * the_c * the_cosa / the_b,
                        'psi': psi,
                        'phi': psi + (0.75 - psi) * the_b * the_cosa / the_c,
                    }
                else:  # if the_ka>0.:
                    x = the_b * the_cosa / the_c + the_b**2 * (1. - the_cosa**2) / the_a**2
                    if a_are_equals(x, 1.):
                        bravais_info['variation'] = 'mclc4'  # order matters here too
                        mu = (1. + (the_b / the_a)**2) / 4.
                        dlt = the_b * the_c * the_cosa / (2. * the_a**2)
                        csi = mu - 0.25 + (1. - the_b * the_cosa / the_c) / (4. * (1. - the_cosa**2))
                        eta = 0.5 + 2. * csi * the_c * the_cosa / the_b
                        phi = 1. + eta - 2. * mu
                        psi = eta - 2. * dlt
                        bravais_info['extra'] = {
                            'mu': mu,
                            'dlt': dlt,
                            'csi': csi,
                            'eta': eta,
                            'phi': phi,
                            'psi': psi,
                        }
                    elif x < 1.:
                        bravais_info['variation'] = 'mclc3'
                        mu = (1. + (the_b / the_a)**2) / 4.
                        dlt = the_b * the_c * the_cosa / (2. * the_a**2)
                        csi = mu - 0.25 + (1. - the_b * the_cosa / the_c) / (4. * (1. - the_cosa**2))
                        eta = 0.5 + 2. * csi * the_c * the_cosa / the_b
                        phi = 1. + eta - 2. * mu
                        psi = eta - 2. * dlt
                        bravais_info['extra'] = {
                            'mu': mu,
                            'dlt': dlt,
                            'csi': csi,
                            'eta': eta,
                            'phi': phi,
                            'psi': psi,
                        }
                    elif x > 1.:
                        bravais_info['variation'] = 'mclc5'
                        csi = ((the_b / the_a)**2 + (1. - the_b * the_cosa / the_c) / (1. - the_cosa**2)) / 4.
                        eta = 0.5 + 2. * csi * the_c * the_cosa / the_b
                        mu = eta / 2. + the_b**2 / 4. / the_a**2 - the_b * the_c * the_cosa / 2. / the_a**2
                        nu = 2. * mu - csi
                        omg = (4. * nu - 1. - the_b**2 *
                               (1. - the_cosa**2) / the_a**2) * the_c / (2. * the_b * the_cosa)
                        dlt = csi * the_c * the_cosa / the_b + omg / 2. - 0.25
                        rho = 1. - csi * the_a**2 / the_b**2
                        bravais_info['extra'] = {
                            'mu': mu,
                            'dlt': dlt,
                            'csi': csi,
                            'eta': eta,
                            'rho': rho,
                        }

            # if it doesn't fall in the above, is triclinic
            else:
                bravais_info = {
                    'short_name': 'tri',
                    'extended_name': 'triclinic',
                    'index': 14,
                }
                # the check for triclinic variations is at the end of the method

        else:  # if comparison_length.count(True)==0:

            fco1 = c**2 / numpy.sqrt((a**2 + c**2) * (b**2 + c**2))
            fco2 = a**2 / numpy.sqrt((a**2 + b**2) * (a**2 + c**2))
            fco3 = b**2 / numpy.sqrt((a**2 + b**2) * (b**2 + c**2))
            # ==============#
            # orthorhombic #
            # ==============#
            if comparison_angles.count(True) == 3:
                bravais_info = {
                    'short_name': 'orc',
                    'extended_name': 'orthorhombic',
                    'index': 6,
                }
                lens = [a, b, c]
                ind_a = lens.index(min(lens))
                ind_c = lens.index(max(lens))
                if ind_a == 0 and ind_c == 1:
                    bravais_info['permutation'] = [0, 2, 1]
                if ind_a == 0 and ind_c == 2:
                    bravais_info['permutation'] = [0, 1, 2]
                if ind_a == 1 and ind_c == 0:
                    bravais_info['permutation'] = [1, 2, 0]
                if ind_a == 1 and ind_c == 2:
                    bravais_info['permutation'] = [1, 0, 2]
                if ind_a == 2 and ind_c == 0:
                    bravais_info['permutation'] = [2, 1, 0]
                if ind_a == 2 and ind_c == 1:
                    bravais_info['permutation'] = [2, 0, 1]
            # ============#
            # monoclinic #
            # ============#
            elif (
                comparison_angles.count(True) == 1 and
                any([a_are_equals(cosa, _90), a_are_equals(cosb, _90),
                     a_are_equals(cosc, _90)])
            ):
                bravais_info = {
                    'short_name': 'mcl',
                    'extended_name': 'monoclinic',
                    'index': 12,
                }
                lens = [a, b, c]
                # find the angle different from 90
                # then order (if possible) a<b<c
                if not a_are_equals(cosa, _90):
                    the_cosa = cosa
                    the_a = min(a, b)
                    the_b = max(a, b)
                    the_c = c
                    if lens.index(the_a) == 0:
                        bravais_info['permutation'] = [0, 1, 2]
                    else:
                        bravais_info['permutation'] = [1, 0, 2]
                elif not a_are_equals(cosb, _90):
                    the_cosa = cosb
                    the_a = min(a, c)
                    the_b = max(a, c)
                    the_c = b
                    if lens.index(the_a) == 0:
                        bravais_info['permutation'] = [0, 2, 1]
                    else:
                        bravais_info['permutation'] = [1, 2, 0]
                else:  # if not _are_equals(cosc,_90):
                    the_cosa = cosc
                    the_a = min(b, c)
                    the_b = max(b, c)
                    the_c = a
                    if lens.index(the_a) == 1:
                        bravais_info['permutation'] = [2, 0, 1]
                    else:
                        bravais_info['permutation'] = [2, 1, 0]
                eta = (1. - the_b * the_cosa / the_c) / (2. * (1. - the_cosa**2))
                bravais_info['extra'] = {
                    'eta': eta,
                    'nu': 0.5 - eta * the_c * the_cosa / the_b,
                }
            # ============================#
            # face centered orthorhombic #
            # ============================#
            elif (
                any([a_are_equals(cosa, fco1),
                     a_are_equals(cosb, fco1),
                     a_are_equals(cosc, fco1)]) and
                any([a_are_equals(cosa, fco2),
                     a_are_equals(cosb, fco2),
                     a_are_equals(cosc, fco2)]) and
                any([a_are_equals(cosa, fco3),
                     a_are_equals(cosb, fco3),
                     a_are_equals(cosc, fco3)])
            ):
                bravais_info = {
                    'short_name': 'orcf',
                    'extended_name': 'face centered orthorhombic',
                    'index': 7,
                }

                lens = [a, b, c]
                ind_a1 = lens.index(max(lens))
                ind_a3 = lens.index(min(lens))
                if ind_a1 == 0 and ind_a3 == 2:
                    bravais_info['permutation'] = [0, 1, 2]
                    the_a1 = a1
                    the_a2 = a2
                    the_a3 = a3
                elif ind_a1 == 0 and ind_a3 == 1:
                    bravais_info['permutation'] = [0, 2, 1]
                    the_a1 = a1
                    the_a2 = a3
                    the_a3 = a2
                elif ind_a1 == 1 and ind_a3 == 2:
                    bravais_info['permutation'] = [1, 0, 2]
                    the_a1 = a2
                    the_a2 = a1
                    the_a3 = a3
                elif ind_a1 == 1 and ind_a3 == 0:
                    bravais_info['permutation'] = [2, 0, 1]
                    the_a1 = a3
                    the_a2 = a1
                    the_a3 = a2
                elif ind_a1 == 2 and ind_a3 == 1:
                    bravais_info['permutation'] = [1, 2, 0]
                    the_a1 = a2
                    the_a2 = a3
                    the_a3 = a1
                else:  # ind_a1 == 2 and ind_a3 == 0:
                    bravais_info['permutation'] = [2, 1, 0]
                    the_a1 = a3
                    the_a2 = a2
                    the_a3 = a1

                the_a = numpy.linalg.norm(-the_a1 + the_a2 + the_a3)
                the_b = numpy.linalg.norm(+the_a1 - the_a2 + the_a3)
                the_c = numpy.linalg.norm(+the_a1 + the_a2 - the_a3)

                fco4 = 1. / the_a**2 - 1. / the_b**2 - 1. / the_c**2
                # orcf3
                if a_are_equals(fco4, 0.):
                    bravais_info['variation'] = 'orcf3'  # order matters
                    bravais_info['extra'] = {
                        'csi': (1. + (the_a / the_b)**2 - (the_a / the_c)**2) / 4.,
                        'eta': (1. + (the_a / the_b)**2 + (the_a / the_c)**2) / 4.,
                    }
                # orcf1
                elif fco4 > 0.:
                    bravais_info['variation'] = 'orcf1'
                    bravais_info['extra'] = {
                        'csi': (1. + (the_a / the_b)**2 - (the_a / the_c)**2) / 4.,
                        'eta': (1. + (the_a / the_b)**2 + (the_a / the_c)**2) / 4.,
                    }
                # orcf2
                else:
                    bravais_info['variation'] = 'orcf2'
                    bravais_info['extra'] = {
                        'eta': (1. + (the_a / the_b)**2 - (the_a / the_c)**2) / 4.,
                        'dlt': (1. + (the_b / the_a)**2 + (the_b / the_c)**2) / 4.,
                        'phi': (1. + (the_c / the_b)**2 - (the_c / the_a)**2) / 4.,
                    }

            else:
                bravais_info = {
                    'short_name': 'tri',
                    'extended_name': 'triclinic',
                    'index': 14,
                }
        # ===========#
        # triclinic #
        # ===========#
        # still miss the variations of triclinic
        if bravais_info['short_name'] == 'tri':
            lens = [a, b, c]
            ind_a = lens.index(min(lens))
            ind_c = lens.index(max(lens))
            if ind_a == 0 and ind_c == 1:
                the_a = a
                the_b = c
                the_c = b
                the_cosa = cosa
                the_cosb = cosc
                the_cosc = cosb
                bravais_info['permutation'] = [0, 2, 1]
            if ind_a == 0 and ind_c == 2:
                the_a = a
                the_b = b
                the_c = c
                the_cosa = cosa
                the_cosb = cosb
                the_cosc = cosc
                bravais_info['permutation'] = [0, 1, 2]
            if ind_a == 1 and ind_c == 0:
                the_a = b
                the_b = c
                the_c = a
                the_cosa = cosb
                the_cosb = cosc
                the_cosc = cosa
                bravais_info['permutation'] = [1, 0, 2]
            if ind_a == 1 and ind_c == 2:
                the_a = b
                the_b = a
                the_c = c
                the_cosa = cosb
                the_cosb = cosa
                the_cosc = cosc
                bravais_info['permutation'] = [1, 0, 2]
            if ind_a == 2 and ind_c == 0:
                the_a = c
                the_b = b
                the_c = a
                the_cosa = cosc
                the_cosb = cosb
                the_cosc = cosa
                bravais_info['permutation'] = [2, 1, 0]
            if ind_a == 2 and ind_c == 1:
                the_a = c
                the_b = a
                the_c = b
                the_cosa = cosc
                the_cosb = cosa
                the_cosc = cosb
                bravais_info['permutation'] = [2, 0, 1]

            if the_cosa < 0. and the_cosb < 0.:
                if a_are_equals(the_cosc, 0.):
                    bravais_info['variation'] = 'tri2a'
                elif the_cosc < 0.:
                    bravais_info['variation'] = 'tri1a'
                else:
                    raise ValueError('Structure erroneously fell into the triclinic (a) case')
            elif the_cosa > 0. and the_cosb > 0.:
                if a_are_equals(the_cosc, 0.):
                    bravais_info['variation'] = 'tri2b'
                elif the_cosc > 0.:
                    bravais_info['variation'] = 'tri1b'
                else:
                    raise ValueError('Structure erroneously fell into the triclinic (b) case')
            else:
                raise ValueError('Structure erroneously fell into the triclinic case')

    elif dimension == 2:
        # ========================================#
        # 2D case -> 5 possible Bravais lattices #
        # ========================================#

        # find the two in-plane lattice vectors
        out_of_plane_index = pbc.index(False)  # the non-periodic dimension
        in_plane_indexes = list(set(range(3)) - set([out_of_plane_index]))
        # in_plane_indexes are the indexes of the two dimensions (e.g. [0,1])

        # build a length-2 list with the 2D cell lattice vectors
        list_vectors = ['a1', 'a2', 'a3']
        vectors = [eval(list_vectors[i]) for i in in_plane_indexes]
        # build a length-2 list with the norms of the 2D cell lattice vectors
        lens = [numpy.linalg.norm(v) for v in vectors]
        # cosine of the angle between the two primitive vectors
        list_angles = ['cosa', 'cosb', 'cosc']
        cosphi = eval(list_angles[out_of_plane_index])

        comparison_length = l_are_equals(lens[0], lens[1])
        comparison_angle_90 = a_are_equals(cosphi, _90)

        # ================#
        # square lattice #
        # ================#
        if comparison_angle_90 and comparison_length:
            bravais_info = {
                'short_name': 'sq',
                'extended_name': 'square',
                'index': 1,
            }

        # =========================#
        # (primitive) rectangular #
        # =========================#
        elif comparison_angle_90:
            bravais_info = {
                'short_name': 'rec',
                'extended_name': 'rectangular',
                'index': 2,
            }
            # set the order such that first_vector < second_vector in norm
            if lens[0] > lens[1]:
                in_plane_indexes.reverse()

        # ===========#
        # hexagonal #
        # ===========#
        # this has to be put before the centered-rectangular case
        elif (l_are_equals(lens[0], lens[1]) and a_are_equals(cosphi, _120)):
            bravais_info = {
                'short_name': 'hex',
                'extended_name': 'hexagonal',
                'index': 4,
            }

        # ======================#
        # centered rectangular #
        # ======================#
        elif (comparison_length and l_are_equals(numpy.dot(vectors[0] + vectors[1], vectors[0] - vectors[1]), 0.)):
            bravais_info = {
                'short_name': 'recc',
                'extended_name': 'centered rectangular',
                'index': 3,
            }

        # =========#
        # oblique #
        # =========#
        else:
            bravais_info = {
                'short_name': 'obl',
                'extended_name': 'oblique',
                'index': 5,
            }
            # set the order such that first_vector < second_vector in norm
            if lens[0] > lens[1]:
                in_plane_indexes.reverse()

        # the permutation is set such that p[2]=out_of_plane_index (third
        # new axis is always the non-periodic out-of-plane axis)
        # TODO: check that this (and the special points permutation of
        # coordinates) works also when the out-of-plane axis is not aligned
        # with one of the cartesian axis (I suspect that it doesn't...)
        permutation = in_plane_indexes + [out_of_plane_index]
        bravais_info['permutation'] = permutation

    elif dimension <= 1:
        # ====================================================#
        # 0D & 1D cases -> only one possible Bravais lattice #
        # ====================================================#
        if dimension == 1:
            # TODO: check that this (and the special points permutation of
            # coordinates) works also when the 1D axis is not aligned
            # with one of the cartesian axis (I suspect that it doesn't...)
            in_line_index = pbc.index(True)  # the only periodic dimension
            # the permutation is set such that p[0]=in_line_index (the 2 last
            # axes are always the non-periodic ones)
            permutation = [in_line_index] + list(set(range(3)) - set([in_line_index]))
        else:
            permutation = [0, 1, 2]

        bravais_info = {
            'short_name': f'{dimension}D',
            'extended_name': f'{dimension}D',
            'index': 1,
            'permutation': permutation,
        }

    return bravais_info


def get_kpoints_path(
    cell, pbc=None, cartesian=False, epsilon_length=_default_epsilon_length, epsilon_angle=_default_epsilon_angle
):
    """
    Get the special point and path of a given structure.

    .. note:: in 3D, this implementation expects
       that the structure is already standardized according to the Setyawan
       paper. If this is not the case, the kpoints and band structure returned will be incorrect. The only case
       that is dealt correctly by the library is the case when axes are swapped, where the library correctly
       takes this swapping/rotation into account to assign kpoint labels and coordinates.

    - In 2D, coordinates are based on the paper:
      R. Ramirez and M. C. Bohm,  Int. J. Quant. Chem., XXX, pp. 391-411 (1986)

    - In 3D, coordinates are based on the paper:
      W. Setyawan, S. Curtarolo, Comp. Mat. Sci. 49, 299 (2010)

    :param cell: 3x3 array representing the structure cell lattice vectors
    :param pbc: 3-dimensional array of booleans signifying the periodic boundary
        conditions along each lattice vector
    :param cartesian: If true, returns points in cartesian coordinates.
        Crystal coordinates otherwise. Default=False
    :param epsilon_length: threshold on lengths comparison, used
        to get the bravais lattice info
    :param epsilon_angle: threshold on angles comparison, used
        to get the bravais lattice info
    :return special_points,path: special_points: a dictionary of
        point_name:point_coords key,values.

        path: the suggested path which goes through all high symmetry
        lines. A list of lists for all path segments.
        e.g. ``[('G','X'),('X','M'),...]``
        It's not necessarily a continuous line.
    :note: We assume that the cell given by the cell property is the
        primitive unit cell
    """
    # pylint: disable=too-many-branches,too-many-statements
    # recognize which bravais lattice we are dealing with
    bravais_info = find_bravais_info(cell=cell, pbc=pbc, epsilon_length=epsilon_length, epsilon_angle=epsilon_angle)

    analysis = analyze_cell(cell, pbc)
    dimension = analysis['dimension']
    reciprocal_cell = analysis['reciprocal_cell']

    # pick the information about the special k-points.
    # it depends on the dimensionality and the Bravais lattice number.
    if dimension == 3:
        # 3D case: 14 Bravais lattices
        # simple cubic
        if bravais_info['index'] == 1:
            special_points = {
                'G': [0., 0., 0.],
                'M': [0.5, 0.5, 0.],
                'R': [0.5, 0.5, 0.5],
                'X': [0., 0.5, 0.],
            }
            path = [
                ('G', 'X'),
                ('X', 'M'),
                ('M', 'G'),
                ('G', 'R'),
                ('R', 'X'),
                ('M', 'R'),
            ]

        # face centered cubic
        elif bravais_info['index'] == 2:
            special_points = {
                'G': [0., 0., 0.],
                'K': [3. / 8., 3. / 8., 0.75],
                'L': [0.5, 0.5, 0.5],
                'U': [5. / 8., 0.25, 5. / 8.],
                'W': [0.5, 0.25, 0.75],
                'X': [0.5, 0., 0.5],
            }
            path = [
                ('G', 'X'),
                ('X', 'W'),
                ('W', 'K'),
                ('K', 'G'),
                ('G', 'L'),
                ('L', 'U'),
                ('U', 'W'),
                ('W', 'L'),
                ('L', 'K'),
                ('U', 'X'),
            ]

        # body centered cubic
        elif bravais_info['index'] == 3:
            special_points = {
                'G': [0., 0., 0.],
                'H': [0.5, -0.5, 0.5],
                'P': [0.25, 0.25, 0.25],
                'N': [0., 0., 0.5],
            }
            path = [
                ('G', 'H'),
                ('H', 'N'),
                ('N', 'G'),
                ('G', 'P'),
                ('P', 'H'),
                ('P', 'N'),
            ]

        # Tetragonal
        elif bravais_info['index'] == 4:
            special_points = {
                'G': [0., 0., 0.],
                'A': [0.5, 0.5, 0.5],
                'M': [0.5, 0.5, 0.],
                'R': [0., 0.5, 0.5],
                'X': [0., 0.5, 0.],
                'Z': [0., 0., 0.5],
            }
            path = [
                ('G', 'X'),
                ('X', 'M'),
                ('M', 'G'),
                ('G', 'Z'),
                ('Z', 'R'),
                ('R', 'A'),
                ('A', 'Z'),
                ('X', 'R'),
                ('M', 'A'),
            ]

        # body centered tetragonal
        elif bravais_info['index'] == 5:
            if bravais_info['variation'] == 'bct1':
                # Body centered tetragonal bct1
                eta = bravais_info['extra']['eta']
                special_points = {
                    'G': [0., 0., 0.],
                    'M': [-0.5, 0.5, 0.5],
                    'N': [0., 0.5, 0.],
                    'P': [0.25, 0.25, 0.25],
                    'X': [0., 0., 0.5],
                    'Z': [eta, eta, -eta],
                    'Z1': [-eta, 1. - eta, eta],
                }
                path = [
                    ('G', 'X'),
                    ('X', 'M'),
                    ('M', 'G'),
                    ('G', 'Z'),
                    ('Z', 'P'),
                    ('P', 'N'),
                    ('N', 'Z1'),
                    ('Z1', 'M'),
                    ('X', 'P'),
                ]

            else:  # bct2
                # Body centered tetragonal bct2
                eta = bravais_info['extra']['eta']
                csi = bravais_info['extra']['csi']
                special_points = {
                    'G': [0., 0., 0.],
                    'N': [0., 0.5, 0.],
                    'P': [0.25, 0.25, 0.25],
                    'S': [-eta, eta, eta],
                    'S1': [eta, 1 - eta, -eta],
                    'X': [0., 0., 0.5],
                    'Y': [-csi, csi, 0.5],
                    'Y1': [0.5, 0.5, -csi],
                    'Z': [0.5, 0.5, -0.5],
                }
                path = [
                    ('G', 'X'),
                    ('X', 'Y'),
                    ('Y', 'S'),
                    ('S', 'G'),
                    ('G', 'Z'),
                    ('Z', 'S1'),
                    ('S1', 'N'),
                    ('N', 'P'),
                    ('P', 'Y1'),
                    ('Y1', 'Z'),
                    ('X', 'P'),
                ]

        # orthorhombic
        elif bravais_info['index'] == 6:
            special_points = {
                'G': [0., 0., 0.],
                'R': [0.5, 0.5, 0.5],
                'S': [0.5, 0.5, 0.],
                'T': [0., 0.5, 0.5],
                'U': [0.5, 0., 0.5],
                'X': [0.5, 0., 0.],
                'Y': [0., 0.5, 0.],
                'Z': [0., 0., 0.5],
            }
            path = [
                ('G', 'X'),
                ('X', 'S'),
                ('S', 'Y'),
                ('Y', 'G'),
                ('G', 'Z'),
                ('Z', 'U'),
                ('U', 'R'),
                ('R', 'T'),
                ('T', 'Z'),
                ('Y', 'T'),
                ('U', 'X'),
                ('S', 'R'),
            ]

        # face centered orthorhombic
        elif bravais_info['index'] == 7:
            if bravais_info['variation'] == 'orcf1':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                special_points = {
                    'G': [0., 0., 0.],
                    'A': [0.5, 0.5 + csi, csi],
                    'A1': [0.5, 0.5 - csi, 1. - csi],
                    'L': [0.5, 0.5, 0.5],
                    'T': [1., 0.5, 0.5],
                    'X': [0., eta, eta],
                    'X1': [1., 1. - eta, 1. - eta],
                    'Y': [0.5, 0., 0.5],
                    'Z': [0.5, 0.5, 0.],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'T'),
                    ('T', 'Z'),
                    ('Z', 'G'),
                    ('G', 'X'),
                    ('X', 'A1'),
                    ('A1', 'Y'),
                    ('T', 'X1'),
                    ('X', 'A'),
                    ('A', 'Z'),
                    ('L', 'G'),
                ]

            elif bravais_info['variation'] == 'orcf2':
                eta = bravais_info['extra']['eta']
                dlt = bravais_info['extra']['dlt']
                phi = bravais_info['extra']['phi']
                special_points = {
                    'G': [0., 0., 0.],
                    'C': [0.5, 0.5 - eta, 1. - eta],
                    'C1': [0.5, 0.5 + eta, eta],
                    'D': [0.5 - dlt, 0.5, 1. - dlt],
                    'D1': [0.5 + dlt, 0.5, dlt],
                    'L': [0.5, 0.5, 0.5],
                    'H': [1. - phi, 0.5 - phi, 0.5],
                    'H1': [phi, 0.5 + phi, 0.5],
                    'X': [0., 0.5, 0.5],
                    'Y': [0.5, 0., 0.5],
                    'Z': [0.5, 0.5, 0.],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'C'),
                    ('C', 'D'),
                    ('D', 'X'),
                    ('X', 'G'),
                    ('G', 'Z'),
                    ('Z', 'D1'),
                    ('D1', 'H'),
                    ('H', 'C'),
                    ('C1', 'Z'),
                    ('X', 'H1'),
                    ('H', 'Y'),
                    ('L', 'G'),
                ]

            else:
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                special_points = {
                    'G': [0., 0., 0.],
                    'A': [0.5, 0.5 + csi, csi],
                    'A1': [0.5, 0.5 - csi, 1. - csi],
                    'L': [0.5, 0.5, 0.5],
                    'T': [1., 0.5, 0.5],
                    'X': [0., eta, eta],
                    'X1': [1., 1. - eta, 1. - eta],
                    'Y': [0.5, 0., 0.5],
                    'Z': [0.5, 0.5, 0.],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'T'),
                    ('T', 'Z'),
                    ('Z', 'G'),
                    ('G', 'X'),
                    ('X', 'A1'),
                    ('A1', 'Y'),
                    ('X', 'A'),
                    ('A', 'Z'),
                    ('L', 'G'),
                ]

        # Body centered orthorhombic
        elif bravais_info['index'] == 8:
            csi = bravais_info['extra']['csi']
            dlt = bravais_info['extra']['dlt']
            eta = bravais_info['extra']['eta']
            mu = bravais_info['extra']['mu']
            special_points = {
                'G': [0., 0., 0.],
                'L': [-mu, mu, 0.5 - dlt],
                'L1': [mu, -mu, 0.5 + dlt],
                'L2': [0.5 - dlt, 0.5 + dlt, -mu],
                'R': [0., 0.5, 0.],
                'S': [0.5, 0., 0.],
                'T': [0., 0., 0.5],
                'W': [0.25, 0.25, 0.25],
                'X': [-csi, csi, csi],
                'X1': [csi, 1. - csi, -csi],
                'Y': [eta, -eta, eta],
                'Y1': [1. - eta, eta, -eta],
                'Z': [0.5, 0.5, -0.5],
            }
            path = [
                ('G', 'X'),
                ('X', 'L'),
                ('L', 'T'),
                ('T', 'W'),
                ('W', 'R'),
                ('R', 'X1'),
                ('X1', 'Z'),
                ('Z', 'G'),
                ('G', 'Y'),
                ('Y', 'S'),
                ('S', 'W'),
                ('L1', 'Y'),
                ('Y1', 'Z'),
            ]

        # C-centered orthorhombic
        elif bravais_info['index'] == 9:
            csi = bravais_info['extra']['csi']
            special_points = {
                'G': [0., 0., 0.],
                'A': [csi, csi, 0.5],
                'A1': [-csi, 1. - csi, 0.5],
                'R': [0., 0.5, 0.5],
                'S': [0., 0.5, 0.],
                'T': [-0.5, 0.5, 0.5],
                'X': [csi, csi, 0.],
                'X1': [-csi, 1. - csi, 0.],
                'Y': [-0.5, 0.5, 0.],
                'Z': [0., 0., 0.5],
            }
            path = [
                ('G', 'X'),
                ('X', 'S'),
                ('S', 'R'),
                ('R', 'A'),
                ('A', 'Z'),
                ('Z', 'G'),
                ('G', 'Y'),
                ('Y', 'X1'),
                ('X1', 'A1'),
                ('A1', 'T'),
                ('T', 'Y'),
                ('Z', 'T'),
            ]

        # Hexagonal
        elif bravais_info['index'] == 10:
            special_points = {
                'G': [0., 0., 0.],
                'A': [0., 0., 0.5],
                'H': [1. / 3., 1. / 3., 0.5],
                'K': [1. / 3., 1. / 3., 0.],
                'L': [0.5, 0., 0.5],
                'M': [0.5, 0., 0.],
            }
            path = [
                ('G', 'M'),
                ('M', 'K'),
                ('K', 'G'),
                ('G', 'A'),
                ('A', 'L'),
                ('L', 'H'),
                ('H', 'A'),
                ('L', 'M'),
                ('K', 'H'),
            ]

        # rhombohedral
        elif bravais_info['index'] == 11:
            if bravais_info['variation'] == 'rhl1':
                eta = bravais_info['extra']['eta']
                nu = bravais_info['extra']['nu']
                special_points = {
                    'G': [0., 0., 0.],
                    'B': [eta, 0.5, 1. - eta],
                    'B1': [0.5, 1. - eta, eta - 1.],
                    'F': [0.5, 0.5, 0.],
                    'L': [0.5, 0., 0.],
                    'L1': [0., 0., -0.5],
                    'P': [eta, nu, nu],
                    'P1': [1. - nu, 1. - nu, 1. - eta],
                    'P2': [nu, nu, eta - 1.],
                    'Q': [1. - nu, nu, 0.],
                    'X': [nu, 0., -nu],
                    'Z': [0.5, 0.5, 0.5],
                }
                path = [
                    ('G', 'L'),
                    ('L', 'B1'),
                    ('B', 'Z'),
                    ('Z', 'G'),
                    ('G', 'X'),
                    ('Q', 'F'),
                    ('F', 'P1'),
                    ('P1', 'Z'),
                    ('L', 'P'),
                ]

            else:  # Rhombohedral rhl2
                eta = bravais_info['extra']['eta']
                nu = bravais_info['extra']['nu']
                special_points = {
                    'G': [0., 0., 0.],
                    'F': [0.5, -0.5, 0.],
                    'L': [0.5, 0., 0.],
                    'P': [1. - nu, -nu, 1. - nu],
                    'P1': [nu, nu - 1., nu - 1.],
                    'Q': [eta, eta, eta],
                    'Q1': [1. - eta, -eta, -eta],
                    'Z': [0.5, -0.5, 0.5],
                }
                path = [
                    ('G', 'P'),
                    ('P', 'Z'),
                    ('Z', 'Q'),
                    ('Q', 'G'),
                    ('G', 'F'),
                    ('F', 'P1'),
                    ('P1', 'Q1'),
                    ('Q1', 'L'),
                    ('L', 'Z'),
                ]

        # monoclinic
        elif bravais_info['index'] == 12:
            eta = bravais_info['extra']['eta']
            nu = bravais_info['extra']['nu']
            special_points = {
                'G': [0., 0., 0.],
                'A': [0.5, 0.5, 0.],
                'C': [0., 0.5, 0.5],
                'D': [0.5, 0., 0.5],
                'D1': [0.5, 0., -0.5],
                'E': [0.5, 0.5, 0.5],
                'H': [0., eta, 1. - nu],
                'H1': [0., 1. - eta, nu],
                'H2': [0., eta, -nu],
                'M': [0.5, eta, 1. - nu],
                'M1': [0.5, 1. - eta, nu],
                'M2': [0.5, eta, -nu],
                'X': [0., 0.5, 0.],
                'Y': [0., 0., 0.5],
                'Y1': [0., 0., -0.5],
                'Z': [0.5, 0., 0.],
            }
            path = [
                ('G', 'Y'),
                ('Y', 'H'),
                ('H', 'C'),
                ('C', 'E'),
                ('E', 'M1'),
                ('M1', 'A'),
                ('A', 'X'),
                ('X', 'H1'),
                ('M', 'D'),
                ('D', 'Z'),
                ('Y', 'D'),
            ]

        elif bravais_info['index'] == 13:
            if bravais_info['variation'] == 'mclc1':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                psi = bravais_info['extra']['psi']
                phi = bravais_info['extra']['phi']
                special_points = {
                    'G': [0., 0., 0.],
                    'N': [0.5, 0., 0.],
                    'N1': [0., -0.5, 0.],
                    'F': [1. - csi, 1. - csi, 1. - eta],
                    'F1': [csi, csi, eta],
                    'F2': [csi, -csi, 1. - eta],
                    'F3': [1. - csi, -csi, 1. - eta],
                    'I': [phi, 1. - phi, 0.5],
                    'I1': [1. - phi, phi - 1., 0.5],
                    'L': [0.5, 0.5, 0.5],
                    'M': [0.5, 0., 0.5],
                    'X': [1. - psi, psi - 1., 0.],
                    'X1': [psi, 1. - psi, 0.],
                    'X2': [psi - 1., -psi, 0.],
                    'Y': [0.5, 0.5, 0.],
                    'Y1': [-0.5, -0.5, 0.],
                    'Z': [0., 0., 0.5],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'F'),
                    ('F', 'L'),
                    ('L', 'I'),
                    ('I1', 'Z'),
                    ('Z', 'F1'),
                    ('Y', 'X1'),
                    ('X', 'G'),
                    ('G', 'N'),
                    ('M', 'G'),
                ]

            elif bravais_info['variation'] == 'mclc2':
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                psi = bravais_info['extra']['psi']
                phi = bravais_info['extra']['phi']
                special_points = {
                    'G': [0., 0., 0.],
                    'N': [0.5, 0., 0.],
                    'N1': [0., -0.5, 0.],
                    'F': [1. - csi, 1. - csi, 1. - eta],
                    'F1': [csi, csi, eta],
                    'F2': [csi, -csi, 1. - eta],
                    'F3': [1. - csi, -csi, 1. - eta],
                    'I': [phi, 1. - phi, 0.5],
                    'I1': [1. - phi, phi - 1., 0.5],
                    'L': [0.5, 0.5, 0.5],
                    'M': [0.5, 0., 0.5],
                    'X': [1. - psi, psi - 1., 0.],
                    'X1': [psi, 1. - psi, 0.],
                    'X2': [psi - 1., -psi, 0.],
                    'Y': [0.5, 0.5, 0.],
                    'Y1': [-0.5, -0.5, 0.],
                    'Z': [0., 0., 0.5],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'F'),
                    ('F', 'L'),
                    ('L', 'I'),
                    ('I1', 'Z'),
                    ('Z', 'F1'),
                    ('N', 'G'),
                    ('G', 'M'),
                ]

            elif bravais_info['variation'] == 'mclc3':
                mu = bravais_info['extra']['mu']
                dlt = bravais_info['extra']['dlt']
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                phi = bravais_info['extra']['phi']
                psi = bravais_info['extra']['psi']
                special_points = {
                    'G': [0., 0., 0.],
                    'F': [1. - phi, 1 - phi, 1. - psi],
                    'F1': [phi, phi - 1., psi],
                    'F2': [1. - phi, -phi, 1. - psi],
                    'H': [csi, csi, eta],
                    'H1': [1. - csi, -csi, 1. - eta],
                    'H2': [-csi, -csi, 1. - eta],
                    'I': [0.5, -0.5, 0.5],
                    'M': [0.5, 0., 0.5],
                    'N': [0.5, 0., 0.],
                    'N1': [0., -0.5, 0.],
                    'X': [0.5, -0.5, 0.],
                    'Y': [mu, mu, dlt],
                    'Y1': [1. - mu, -mu, -dlt],
                    'Y2': [-mu, -mu, -dlt],
                    'Y3': [mu, mu - 1., dlt],
                    'Z': [0., 0., 0.5],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'F'),
                    ('F', 'H'),
                    ('H', 'Z'),
                    ('Z', 'I'),
                    ('I', 'F1'),
                    ('H1', 'Y1'),
                    ('Y1', 'X'),
                    ('X', 'F'),
                    ('G', 'N'),
                    ('M', 'G'),
                ]

            elif bravais_info['variation'] == 'mclc4':
                mu = bravais_info['extra']['mu']
                dlt = bravais_info['extra']['dlt']
                csi = bravais_info['extra']['csi']
                eta = bravais_info['extra']['eta']
                phi = bravais_info['extra']['phi']
                psi = bravais_info['extra']['psi']
                special_points = {
                    'G': [0., 0., 0.],
                    'F': [1. - phi, 1 - phi, 1. - psi],
                    'F1': [phi, phi - 1., psi],
                    'F2': [1. - phi, -phi, 1. - psi],
                    'H': [csi, csi, eta],
                    'H1': [1. - csi, -csi, 1. - eta],
                    'H2': [-csi, -csi, 1. - eta],
                    'I': [0.5, -0.5, 0.5],
                    'M': [0.5, 0., 0.5],
                    'N': [0.5, 0., 0.],
                    'N1': [0., -0.5, 0.],
                    'X': [0.5, -0.5, 0.],
                    'Y': [mu, mu, dlt],
                    'Y1': [1. - mu, -mu, -dlt],
                    'Y2': [-mu, -mu, -dlt],
                    'Y3': [mu, mu - 1., dlt],
                    'Z': [0., 0., 0.5],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'F'),
                    ('F', 'H'),
                    ('H', 'Z'),
                    ('Z', 'I'),
                    ('H1', 'Y1'),
                    ('Y1', 'X'),
                    ('X', 'G'),
                    ('G', 'N'),
                    ('M', 'G'),
                ]

            else:
                csi = bravais_info['extra']['csi']
                mu = bravais_info['extra']['mu']
                omg = bravais_info['extra']['omg']
                eta = bravais_info['extra']['eta']
                nu = bravais_info['extra']['nu']
                dlt = bravais_info['extra']['dlt']
                rho = bravais_info['extra']['rho']
                special_points = {
                    'G': [0., 0., 0.],
                    'F': [nu, nu, omg],
                    'F1': [1. - nu, 1. - nu, 1. - omg],
                    'F2': [nu, nu - 1., omg],
                    'H': [csi, csi, eta],
                    'H1': [1. - csi, -csi, 1. - eta],
                    'H2': [-csi, -csi, 1. - eta],
                    'I': [rho, 1. - rho, 0.5],
                    'I1': [1. - rho, rho - 1., 0.5],
                    'L': [0.5, 0.5, 0.5],
                    'M': [0.5, 0., 0.5],
                    'N': [0.5, 0., 0.],
                    'N1': [0., -0.5, 0.],
                    'X': [0.5, -0.5, 0.],
                    'Y': [mu, mu, dlt],
                    'Y1': [1. - mu, -mu, -dlt],
                    'Y2': [-mu, -mu, -dlt],
                    'Y3': [mu, mu - 1., dlt],
                    'Z': [0., 0., 0.5],
                }
                path = [
                    ('G', 'Y'),
                    ('Y', 'F'),
                    ('F', 'L'),
                    ('L', 'I'),
                    ('I1', 'Z'),
                    ('Z', 'H'),
                    ('H', 'F1'),
                    ('H1', 'Y1'),
                    ('Y1', 'X'),
                    ('X', 'G'),
                    ('G', 'N'),
                    ('M', 'G'),
                ]

        # triclinic
        elif bravais_info['index'] == 14:
            if bravais_info['variation'] == 'tri1a' or bravais_info['variation'] == 'tri2a':
                special_points = {
                    'G': [0.0, 0.0, 0.0],
                    'L': [0.5, 0.5, 0.0],
                    'M': [0.0, 0.5, 0.5],
                    'N': [0.5, 0.0, 0.5],
                    'R': [0.5, 0.5, 0.5],
                    'X': [0.5, 0.0, 0.0],
                    'Y': [0.0, 0.5, 0.0],
                    'Z': [0.0, 0.0, 0.5],
                }
                path = [
                    ('X', 'G'),
                    ('G', 'Y'),
                    ('L', 'G'),
                    ('G', 'Z'),
                    ('N', 'G'),
                    ('G', 'M'),
                    ('R', 'G'),
                ]

            else:
                special_points = {
                    'G': [0.0, 0.0, 0.0],
                    'L': [0.5, -0.5, 0.0],
                    'M': [0.0, 0.0, 0.5],
                    'N': [-0.5, -0.5, 0.5],
                    'R': [0.0, -0.5, 0.5],
                    'X': [0.0, -0.5, 0.0],
                    'Y': [0.5, 0.0, 0.0],
                    'Z': [-0.5, 0.0, 0.5],
                }
                path = [
                    ('X', 'G'),
                    ('G', 'Y'),
                    ('L', 'G'),
                    ('G', 'Z'),
                    ('N', 'G'),
                    ('G', 'M'),
                    ('R', 'G'),
                ]

    elif dimension == 2:
        # 2D case: 5 Bravais lattices
        if bravais_info['index'] == 1:
            # square
            special_points = {
                'G': [0., 0., 0.],
                'M': [0.5, 0.5, 0.],
                'X': [0.5, 0., 0.],
            }
            path = [
                ('G', 'X'),
                ('X', 'M'),
                ('M', 'G'),
            ]

        elif bravais_info['index'] == 2:
            # (primitive) rectangular
            special_points = {
                'G': [0., 0., 0.],
                'X': [0.5, 0., 0.],
                'Y': [0., 0.5, 0.],
                'S': [0.5, 0.5, 0.],
            }
            path = [
                ('G', 'X'),
                ('X', 'S'),
                ('S', 'Y'),
                ('Y', 'G'),
            ]

        elif bravais_info['index'] == 3:
            # centered rectangular (rhombic)
            # TODO: this looks quite different from the in-plane part of the
            # 3D C-centered orthorhombic lattice, which is strange...

            # NOTE: special points below are in (b1, b2) fractional
            # coordinates (primitive reciprocal cell) as for the rest.
            # Ramirez & Bohn gave them initially in (s1=b1+b2, s2=-b1+b2)
            # coordinates, i.e. using the conventional reciprocal cell.
            special_points = {
                'G': [0., 0., 0.],
                'X': [0.5, 0.5, 0.],
                'Y1': [0.25, 0.75, 0.],
                'Y': [-0.25, 0.25, 0.],  # typo in p. 404 of Ramirez & Bohm (should be Y=(0,1/4))
                'C': [0., 0.5, 0.],
            }
            path = [
                ('Y1', 'X'),
                ('X', 'G'),
                ('G', 'Y'),
                ('Y', 'C'),
            ]

        elif bravais_info['index'] == 4:
            # hexagonal
            special_points = {
                'G': [0., 0., 0.],
                'M': [0.5, 0., 0.],
                'K': [1. / 3., 1. / 3., 0.],
            }
            path = [
                ('G', 'M'),
                ('M', 'K'),
                ('K', 'G'),
            ]

        elif bravais_info['index'] == 5:
            # oblique
            # NOTE: only end-points are high-symmetry points (not the path
            # in-between)
            special_points = {
                'G': [0., 0., 0.],
                'X': [0.5, 0., 0.],
                'Y': [0., 0.5, 0.],
                'A': [0.5, 0.5, 0.],
            }
            path = [
                ('X', 'G'),
                ('G', 'Y'),
                ('A', 'G'),
            ]

    elif dimension == 1:
        # 1D case: 1 Bravais lattice
        special_points = {
            'G': [0., 0., 0.],
            'X': [0.5, 0., 0.],
        }
        path = [
            ('G', 'X'),
        ]

    elif dimension == 0:
        # 0D case: 1 Bravais lattice, only Gamma point, no path
        special_points = {
            'G': [0., 0., 0.],
        }
        path = [
            ('G', 'G'),
        ]

    permutation = bravais_info['permutation']

    def permute(x, permutation):
        # return new_x such that new_x[i]=x[permutation[i]]
        return [x[int(p)] for p in permutation]

    the_special_points = {}
    for key, value in special_points.items():
        # NOTE: this originally returned the inverse of the permutation, but was later changed to permutation
        the_special_points[key] = permute(value, permutation)

    # output crystal or cartesian
    if cartesian:
        the_abs_special_points = {}
        for key, value in the_special_points.items():
            the_abs_special_points[key] = change_reference(reciprocal_cell, numpy.array(value), to_cartesian=True)

        return the_abs_special_points, path, bravais_info

    return the_special_points, path, bravais_info
