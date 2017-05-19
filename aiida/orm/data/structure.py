# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module defines the classes for structures and all related
functions to operate on them.
"""

from aiida.orm import Data
from aiida.common.utils import classproperty, xyz_parser_iterator
from aiida.orm.calculation.inline import optional_inline
import itertools
import copy

# Threshold used to check if the mass of two different Site objects is the same.


_mass_threshold = 1.e-3
# Threshold to check if the sum is one or not
_sum_threshold = 1.e-6
# Threshold used to check if the cell volume is not zero.
_volume_threshold = 1.e-6

# Element table
from aiida.common.constants import elements

_valid_symbols = tuple(i['symbol'] for i in elements.values())
_atomic_masses = {el['symbol']: el['mass'] for el in elements.values()}
_atomic_numbers = {data['symbol']: num for num, data in elements.iteritems()}


def _get_valid_cell(inputcell):
    """
    Return the cell in a valid format from a generic input.

    :raise ValueError: whenever the format is not valid.
    """
    try:
        the_cell = list(list(float(c) for c in i) for i in inputcell)
        if len(the_cell) != 3:
            raise ValueError
        if any(len(i) != 3 for i in the_cell):
            raise ValueError
    except (IndexError, ValueError, TypeError):
        raise ValueError("Cell must be a list of three vectors, each "
                         "defined as a list of three coordinates.")

    if abs(calc_cell_volume(the_cell)) < _volume_threshold:
        raise ValueError("The cell volume is zero. Invalid cell.")

    return the_cell


def get_valid_pbc(inputpbc):
    """
    Return a list of three booleans for the periodic boundary conditions,
    in a valid format from a generic input.

    :raise ValueError: if the format is not valid.
    """
    if isinstance(inputpbc, bool):
        the_pbc = (inputpbc, inputpbc, inputpbc)
    elif (hasattr(inputpbc, '__iter__')):
        # To manage numpy lists of bools, whose elements are of type numpy.bool_
        # and for which isinstance(i,bool) return False...
        if hasattr(inputpbc, 'tolist'):
            the_value = inputpbc.tolist()
        else:
            the_value = inputpbc
        if all(isinstance(i, bool) for i in the_value):
            if len(the_value) == 3:
                the_pbc = tuple(i for i in the_value)
            elif len(the_value) == 1:
                the_pbc = (the_value[0], the_value[0], the_value[0])
            else:
                raise ValueError("pbc length must be either one or three.")
        else:
            raise ValueError("pbc elements are not booleans.")
    else:
        raise ValueError("pbc must be a boolean or a list of three "
                         "booleans.", inputpbc)

    return the_pbc


def has_ase():
    """
    :return: True if the ase module can be imported, False otherwise.
    """
    try:
        import ase
    except ImportError:
        return False
    return True


def has_pymatgen():
    """
    :return: True if the pymatgen module can be imported, False otherwise.
    """
    try:
        import pymatgen
    except ImportError:
        return False
    return True


def get_pymatgen_version():
    """
    :return: string with pymatgen version, None if can not import.
    """
    if not has_pymatgen():
        return None
    import pymatgen
    return pymatgen.__version__


def has_spglib():
    """
    :return: True if the spglib module can be imported, False otherwise.
    """
    try:
        import spglib
    except ImportError:
        return False
    return True


def calc_cell_volume(cell):
    """
    Calculates the volume of a cell given the three lattice vectors.

    It is calculated as cell[0] . (cell[1] x cell[2]), where . represents
    a dot product and x a cross product.

    :param cell: the cell vectors; the must be a 3x3 list of lists of floats,
            no other checks are done.

    :returns: the cell volume.
    """
    # returns the volume of the primitive cell: |a1.(a2xa3)|
    a1 = cell[0]
    a2 = cell[1]
    a3 = cell[2]
    a_mid_0 = a2[1] * a3[2] - a2[2] * a3[1]
    a_mid_1 = a2[2] * a3[0] - a2[0] * a3[2]
    a_mid_2 = a2[0] * a3[1] - a2[1] * a3[0]
    return abs(a1[0] * a_mid_0 + a1[1] * a_mid_1 + a1[2] * a_mid_2)


def _create_symbols_tuple(symbols):
    """
    Returns a tuple with the symbols provided. If a string is provided,
    this is converted to a tuple with one single element.
    """
    if isinstance(symbols, basestring):
        symbols_list = (symbols,)
    else:
        symbols_list = tuple(symbols)
    return symbols_list


def _create_weights_tuple(weights):
    """
    Returns a tuple with the weights provided. If a number is provided,
    this is converted to a tuple with one single element.
    If None is provided, this is converted to the tuple (1.,)
    """
    import numbers

    if weights is None:
        weights_tuple = (1.,)
    elif isinstance(weights, numbers.Number):
        weights_tuple = (weights,)
    else:
        weights_tuple = tuple(float(i) for i in weights)
    return weights_tuple


def validate_weights_tuple(weights_tuple, threshold):
    """
    Validates the weight of the atomic kinds.

    :raise: ValueError if the weights_tuple is not valid.

    :param weights_tuple: the tuple to validate. It must be a
            a tuple of floats (as created by :func:_create_weights_tuple).
    :param threshold: a float number used as a threshold to check that the sum
            of the weights is <= 1.

    If the sum is less than one, it means that there are vacancies.
    Each element of the list must be >= 0, and the sum must be <= 1.
    """
    w_sum = sum(weights_tuple)
    if (any(i < 0. for i in weights_tuple) or
            (w_sum - 1. > threshold)):
        raise ValueError("The weight list is not valid (each element "
                         "must be positive, and the sum must be <= 1).")


def is_valid_symbol(symbol):
    """
    Validates the chemical symbol name.

    :return: True if the symbol is a valid chemical symbol (with correct
        capitalization), False otherwise.

    Recognized symbols are for elements from hydrogen (Z=1) to lawrencium
    (Z=103).
    """
    return symbol in _valid_symbols


def validate_symbols_tuple(symbols_tuple):
    """
    Used to validate whether the chemical species are valid.

    :param symbols_tuple: a tuple (or list) with the chemical symbols name.
    :raises: ValueError if any symbol in the tuple is not a valid chemical
        symbols (with correct capitalization).

    Refer also to the documentation of :func:is_valid_symbol
    """
    if len(symbols_tuple) == 0:
        valid = False
    else:
        valid = all(is_valid_symbol(sym) for sym in symbols_tuple)
    if not valid:
        raise ValueError("At least one element of the symbol list {} has "
                         "not been recognized.".format(symbols_tuple))


def is_ase_atoms(ase_atoms):
    """
    Check if the ase_atoms parameter is actually a ase.Atoms object.

    :param ase_atoms: an object, expected to be an ase.Atoms.
    :return: a boolean.

    Requires the ability to import ase, by doing 'import ase'.
    """
    # TODO: Check if we want to try to import ase and do something
    # reasonable depending on whether ase is there or not.
    import ase

    return isinstance(ase_atoms, ase.Atoms)


def group_symbols(_list):
    """
    Group a list of symbols to a list containing the number of consecutive
    identical symbols, and the symbol itself.

    Examples:

    * ``['Ba','Ti','O','O','O','Ba']`` will return
      ``[[1,'Ba'],[1,'Ti'],[3,'O'],[1,'Ba']]``

    * ``[ [ [1,'Ba'],[1,'Ti'] ],[ [1,'Ba'],[1,'Ti'] ] ]`` will return
      ``[[2, [ [1, 'Ba'], [1, 'Ti'] ] ]]``

    :param _list: a list of elements representing a chemical formula
    :return: a list of length-2 lists of the form [ multiplicity , element ]
    """

    the_list = copy.deepcopy(_list)
    the_list.reverse()
    grouped_list = [[1, the_list.pop()]]
    while the_list:
        elem = the_list.pop()
        if elem == grouped_list[-1][1]:
            # same symbol is repeated
            grouped_list[-1][0] += 1
        else:
            grouped_list.append([1, elem])

    return grouped_list


def get_formula_from_symbol_list(_list, separator=""):
    """
    Return a string with the formula obtained from the list of symbols.
    Examples:
    * ``[[1,'Ba'],[1,'Ti'],[3,'O']]`` will return ``'BaTiO3'``
    * ``[[2, [ [1, 'Ba'], [1, 'Ti'] ] ]]`` will return ``'(BaTi)2'``

    :param _list: a list of symbols and multiplicities as obtained from
        the function group_symbols
    :param separator: a string used to concatenate symbols. Default empty.

    :return: a string
    """

    list_str = []
    for elem in _list:
        if elem[0] == 1:
            multiplicity_str = ''
        else:
            multiplicity_str = str(elem[0])

        if isinstance(elem[1], basestring):
            list_str.append("{}{}".format(elem[1], multiplicity_str))
        elif elem[0] > 1:
            list_str.append(
                "({}){}".format(get_formula_from_symbol_list(elem[1],
                                                             separator=separator),
                                multiplicity_str))
        else:
            list_str.append("{}{}".format(get_formula_from_symbol_list(elem[1],
                                                                       separator=separator),
                                          multiplicity_str))

    return separator.join(list_str)


def get_formula_group(symbol_list, separator=""):
    """
    Return a string with the chemical formula from a list of chemical symbols.
    The formula is written in a compact" way, i.e. trying to group as much as
    possible parts of the formula.

    .. note:: it works for instance very well if structure was obtained
        from an ASE supercell.

    Example of result:
    ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
    'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'(BaTiO3)2BaTi2O3'``.

    :param symbol_list: list of symbols
        (e.g. ['Ba','Ti','O','O','O'])
    :param separator: a string used to concatenate symbols. Default empty.
    :returns: a string with the chemical formula for the given structure.
    """

    def group_together(_list, group_size, offset):
        """
        :param _list: a list
        :param group_size: size of the groups
        :param offset: beginning grouping after offset elements
        :return : a list of lists made of groups of size group_size
            obtained by grouping list elements together
            The first elements (up to _list[offset-1]) are not grouped
        example:
            ``group_together(['O','Ba','Ti','Ba','Ti'],2,1) =
                ['O',['Ba','Ti'],['Ba','Ti']]``
        """

        the_list = copy.deepcopy(_list)
        the_list.reverse()
        grouped_list = []
        for i in range(offset):
            grouped_list.append([the_list.pop()])

        while the_list:
            l = []
            for i in range(group_size):
                if the_list:
                    l.append(the_list.pop())
            grouped_list.append(l)

        return grouped_list

    def cleanout_symbol_list(_list):
        """
        :param _list: a list of groups of symbols and multiplicities
        :return : a list where all groups with multiplicity 1 have
            been reduced to minimum
        example: ``[[1,[[1,'Ba']]]]`` will return ``[[1,'Ba']]``
        """
        the_list = []
        for elem in _list:
            if elem[0] == 1 and isinstance(elem[1], list):
                the_list.extend(elem[1])
            else:
                the_list.append(elem)

        return the_list

    def group_together_symbols(_list, group_size):
        """
        Successive application of group_together, group_symbols and
        cleanout_symbol_list, in order to group a symbol list, scanning all
        possible offsets, for a given group size
        :param _list: the symbol list (see function group_symbols)
        :param group_size: the size of the groups
        :return the_symbol_list: the new grouped symbol list
        :return has_grouped: True if we grouped something
        """
        the_symbol_list = copy.deepcopy(_list)
        has_grouped = False
        offset = 0
        while (not has_grouped) and (offset < group_size):
            grouped_list = group_together(the_symbol_list, group_size, offset)
            new_symbol_list = group_symbols(grouped_list)
            if (len(new_symbol_list) < len(grouped_list)):
                the_symbol_list = copy.deepcopy(new_symbol_list)
                the_symbol_list = cleanout_symbol_list(the_symbol_list)
                has_grouped = True
                # print get_formula_from_symbol_list(the_symbol_list)
            offset += 1

        return the_symbol_list, has_grouped

    def group_all_together_symbols(_list):
        """
        Successive application of the function group_together_symbols, to group
        a symbol list, scanning all possible offsets and group sizes
        :param _list: the symbol list (see function group_symbols)
        :return: the new grouped symbol list
        """
        has_finished = False
        group_size = 2
        n = len(_list)
        the_symbol_list = copy.deepcopy(_list)

        while (not has_finished) and (group_size <= n / 2):
            # try to group as much as possible by groups of size group_size
            the_symbol_list, has_grouped = group_together_symbols(
                the_symbol_list,
                group_size)
            has_finished = has_grouped
            group_size += 1
            # stop as soon as we managed to group something
            # or when the group_size is too big to get anything

        return the_symbol_list

    # initial grouping of the chemical symbols
    old_symbol_list = [-1]
    new_symbol_list = group_symbols(symbol_list)

    # successively apply the grouping procedure until the symbol list does not
    # change anymore
    while new_symbol_list != old_symbol_list:
        old_symbol_list = copy.deepcopy(new_symbol_list)
        new_symbol_list = group_all_together_symbols(old_symbol_list)

    return get_formula_from_symbol_list(new_symbol_list, separator=separator)


def get_formula(symbol_list, mode='hill', separator=""):
    """
    Return a string with the chemical formula.

    :param symbol_list: a list of symbols, e.g. ``['H','H','O']``
    :param mode: a string to specify how to generate the formula, can
        assume one of the following values:

        * 'hill' (default): count the number of atoms of each species,
          then use Hill notation, i.e. alphabetical order with C and H
          first if one or several C atom(s) is (are) present, e.g.
          ``['C','H','H','H','O','C','H','H','H']`` will return ``'C2H6O'``
          ``['S','O','O','H','O','H','O']``  will return ``'H2O4S'``
          From E. A. Hill, J. Am. Chem. Soc., 22 (8), pp 478–494 (1900)

        * 'hill_compact': same as hill but the number of atoms for each
          species is divided by the greatest common divisor of all of them, e.g.
          ``['C','H','H','H','O','C','H','H','H','O','O','O']``
          will return ``'CH3O2'``

        * 'reduce': group repeated symbols e.g.
          ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
          'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'BaTiO3BaTiO3BaTi2O3'``

        * 'group': will try to group as much as possible parts of the formula
          e.g.
          ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
          'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'(BaTiO3)2BaTi2O3'``

        * 'count': same as hill (i.e. one just counts the number
          of atoms of each species) without the re-ordering (take the
          order of the atomic sites), e.g.
          ``['Ba', 'Ti', 'O', 'O', 'O','Ba', 'Ti', 'O', 'O', 'O']``
          will return ``'Ba2Ti2O6'``

        * 'count_compact': same as count but the number of atoms
          for each species is divided by the greatest common divisor of
          all of them, e.g.
          ``['Ba', 'Ti', 'O', 'O', 'O','Ba', 'Ti', 'O', 'O', 'O']``
          will return ``'BaTiO3'``

    :param separator: a string used to concatenate symbols. Default empty.

    :return: a string with the formula

    .. note:: in modes reduce, group, count and count_compact, the
        initial order in which the atoms were appended by the user is
        used to group and/or order the symbols in the formula
    """

    if mode == 'group':
        return get_formula_group(symbol_list, separator=separator)

    # for hill and count cases, simply count the occurences of each
    # chemical symbol (with some re-ordering in hill)
    elif mode in ['hill', 'hill_compact']:
        symbol_set = set(symbol_list)
        first_symbols = []
        if 'C' in symbol_set:
            # remove C (and H if present) from list and put them at the
            # beginning
            symbol_set.remove('C')
            first_symbols.append('C')
            if 'H' in symbol_set:
                symbol_set.remove('H')
                first_symbols.append('H')
        ordered_symbol_set = first_symbols + list(sorted(symbol_set))
        the_symbol_list = [[symbol_list.count(elem), elem]
                           for elem in ordered_symbol_set]

    elif mode in ['count', 'count_compact']:
        ordered_symbol_indexes = sorted([symbol_list.index(elem)
                                         for elem in set(symbol_list)])
        ordered_symbol_set = [symbol_list[i] for i in ordered_symbol_indexes]
        the_symbol_list = [[symbol_list.count(elem), elem]
                           for elem in ordered_symbol_set]

    elif mode == 'reduce':
        the_symbol_list = group_symbols(symbol_list)

    else:
        raise ValueError('Mode should be hill, hill_compact, group, '
                         'reduce, count or count_compact')

    if mode in ['hill_compact', 'count_compact']:

        def gcd_list(int_list):
            """
            Recursive function to get the greatest common divisor of
            a list of integers
            """
            from fractions import gcd
            if len(int_list) == 1:
                return int_list[0]
            elif len(int_list) == 2:
                return gcd(int_list[0], int_list[1])
            else:
                the_int_list = int_list[2:]
                the_int_list.append(gcd(int_list[0], int_list[1]))
                return gcd_list(the_int_list)

        the_gcd = gcd_list([e[0] for e in the_symbol_list])
        the_symbol_list = [[e[0] / the_gcd, e[1]] for e in the_symbol_list]

    return get_formula_from_symbol_list(the_symbol_list, separator=separator)


def get_symbols_string(symbols, weights):
    """
    Return a string that tries to match as good as possible the symbols
    and weights. If there is only one symbol (no alloy) with 100%
    occupancy, just returns the symbol name. Otherwise, groups the full
    string in curly brackets, and try to write also the composition
    (with 2 precision only).
    If (sum of weights<1), we indicate it with the X symbol followed
    by 1-sum(weights) (still with 2 digits precision, so it can be 0.00)

    :param symbols: the symbols as obtained from <kind>._symbols
    :param weights: the weights as obtained from <kind>._weights

    .. note:: Note the difference with respect to the symbols and the
        symbol properties!
    """
    if len(symbols) == 1 and weights[0] == 1.:
        return symbols[0]
    else:
        pieces = []
        for s, w in zip(symbols, weights):
            pieces.append("{}{:4.2f}".format(s, w))
        if has_vacancies(weights):
            pieces.append('X{:4.2f}'.format(1. - sum(weights)))
        return "{{{}}}".format("".join(sorted(pieces)))


def has_vacancies(weights):
    """
    Returns True if the sum of the weights is less than one.
    It uses the internal variable _sum_threshold as a threshold.
    :param weights: the weights
    :return: a boolean
    """
    w_sum = sum(weights)
    return not (1. - w_sum < _sum_threshold)


def symop_ortho_from_fract(cell):
    """
    Creates a matrix for conversion from orthogonal to fractional
    coordinates.

    Taken from
    svn://www.crystallography.net/cod-tools/trunk/lib/perl5/Fractional.pm,
    revision 850.

    :param cell: array of cell parameters (three lengths and three angles)
    """
    import math
    import numpy

    a, b, c, alpha, beta, gamma = cell
    alpha, beta, gamma = map(lambda x: math.pi * x / 180,
                             alpha, beta, gamma)
    ca, cb, cg = map(math.cos, [alpha, beta, gamma])
    sg = math.sin(gamma)

    return numpy.array([
        [a, b * cg, c * cb],
        [0, b * sg, c * (ca - cb * cg) / sg],
        [0, 0,
         c * math.sqrt(sg * sg - ca * ca - cb * cb + 2 * ca * cb * cg) / sg]
    ])


def symop_fract_from_ortho(cell):
    """
    Creates a matrix for conversion from fractional to orthogonal
    coordinates.

    Taken from
    svn://www.crystallography.net/cod-tools/trunk/lib/perl5/Fractional.pm,
    revision 850.

    :param cell: array of cell parameters (three lengths and three angles)
    """
    import math
    import numpy

    a, b, c, alpha, beta, gamma = cell
    alpha, beta, gamma = map(lambda x: math.pi * x / 180,
                             [alpha, beta, gamma])
    ca, cb, cg = map(math.cos, [alpha, beta, gamma])
    sg = math.sin(gamma)
    ctg = cg / sg
    D = math.sqrt(sg * sg - cb * cb - ca * ca + 2 * ca * cb * cg)

    return numpy.array([
        [1.0 / a, -(1.0 / a) * ctg, (ca * cg - cb) / (a * D)],
        [0, 1.0 / (b * sg), -(ca - cb * cg) / (b * D * sg)],
        [0, 0, sg / (c * D)],
    ])


def ase_refine_cell(aseatoms, **kwargs):
    """
    Detect the symmetry of the structure, remove symmetric atoms and
    refine unit cell.

    :param aseatoms: an ase.atoms.Atoms instance
    :param symprec: symmetry precision, used by spglib
    :return newase: refined cell with reduced set of atoms
    :return symmetry: a dictionary describing the symmetry space group
    """
    from spglib import refine_cell, get_symmetry_dataset
    from ase.atoms import Atoms
    cell, positions, numbers = refine_cell(aseatoms, **kwargs)

    refined_atoms = Atoms(numbers, scaled_positions=positions, cell=cell,
                          pbc=True)

    sym_dataset = get_symmetry_dataset(refined_atoms, **kwargs)

    unique_numbers = []
    unique_positions = []

    for i in set(sym_dataset['equivalent_atoms']):
        unique_numbers.append(refined_atoms.numbers[i])
        unique_positions.append(refined_atoms.get_scaled_positions()[i])

    unique_atoms = Atoms(unique_numbers,
                         scaled_positions=unique_positions,
                         cell=cell, pbc=True)

    return unique_atoms, {'hm': sym_dataset['international'],
                          'hall': sym_dataset['hall'],
                          'tables': sym_dataset['number'],
                          'rotations': sym_dataset['rotations'],
                          'translations': sym_dataset['translations']}


@optional_inline
def _get_cif_ase_inline(struct=None, parameters=None):
    """
    Creates :py:class:`aiida.orm.data.cif.CifData` using ASE.

    .. note:: requires ASE module.
    """
    from aiida.orm.data.cif import CifData

    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    cif = CifData(ase=struct.get_ase(**kwargs))
    formula = struct.get_formula(mode='hill', separator=' ')
    for i in cif.values.keys():
        cif.values[i]['_symmetry_space_group_name_H-M'] = 'P 1'
        cif.values[i]['_symmetry_space_group_name_Hall'] = 'P 1'
        cif.values[i]['_symmetry_Int_Tables_number'] = 1
        cif.values[i]['_cell_formula_units_Z'] = 1
        cif.values[i]['_chemical_formula_sum'] = formula
    return {'cif': cif}


class StructureData(Data):
    """
    This class contains the information about a given structure, i.e. a
    collection of sites together with a cell, the
    boundary conditions (whether they are periodic or not) and other
    related useful information.
    """
    _set_incompatibilities = [("ase", "cell"), ("ase", "pbc"),
                              ("ase", "pymatgen"), ("ase", "pymatgen_molecule"),
                              ("ase", "pymatgen_structure"),
                              ("cell", "pymatgen"),
                              ("cell", "pymatgen_molecule"),
                              ("cell", "pymatgen_structure"),
                              ("pbc", "pymatgen"), ("pbc", "pymatgen_molecule"),
                              ("pbc", "pymatgen_structure"),
                              ("pymatgen", "pymatgen_molecule"),
                              ("pymatgen", "pymatgen_structure"),
                              ("pymatgen_molecule", "pymatgen_structure")]

    @property
    def _set_defaults(self):
        parent_dict = super(StructureData, self)._set_defaults

        parent_dict.update({
            "pbc": [True, True, True],
            "cell": [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
        })

        return parent_dict

    def set_ase(self, aseatoms):
        """
        Load the structure from a ASE object
        """
        if is_ase_atoms(aseatoms):
            # Read the ase structure
            self.cell = aseatoms.cell
            self.pbc = aseatoms.pbc
            self.clear_kinds()  # This also calls clear_sites
            for atom in aseatoms:
                self.append_atom(ase=atom)
        else:
            raise TypeError("The value is not an ase.Atoms object")

    def set_pymatgen(self, obj, **kwargs):
        """
        Load the structure from a pymatgen object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        typestr = type(obj).__name__
        try:
            func = getattr(self, "set_pymatgen_{}".format(typestr.lower()))
        except AttributeError:
            raise AttributeError("Converter for '{}' to AiiDA structure "
                                 "does not exist".format(typestr))
        func(obj, **kwargs)

    def set_pymatgen_molecule(self, mol, margin=5):
        """
        Load the structure from a pymatgen Molecule object.

        :param margin: the margin to be added in all directions of the
            bounding box of the molecule.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        box = [max([x.coords.tolist()[0] for x in mol.sites]) -
               min([x.coords.tolist()[0] for x in mol.sites]) + 2 * margin,
               max([x.coords.tolist()[1] for x in mol.sites]) -
               min([x.coords.tolist()[1] for x in mol.sites]) + 2 * margin,
               max([x.coords.tolist()[2] for x in mol.sites]) -
               min([x.coords.tolist()[2] for x in mol.sites]) + 2 * margin]
        self.set_pymatgen_structure(mol.get_boxed_structure(*box))
        self.pbc = [False, False, False]

    def set_pymatgen_structure(self, struct):
        """
        Load the structure from a pymatgen Structure object.

        .. note:: periodic boundary conditions are set to True in all
            three directions.
        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        self.cell = struct.lattice.matrix.tolist()
        self.pbc = [True, True, True]
        self.clear_kinds()
        for site in struct.sites:
            self.append_atom(
                symbols=[x[0].symbol for x in site.species_and_occu.items()],
                weights=[x[1] for x in site.species_and_occu.items()],
                position=site.coords.tolist())

    def _validate(self):
        """
        Performs some standard validation tests.
        """

        from aiida.common.exceptions import ValidationError

        super(StructureData, self)._validate()

        try:
            _get_valid_cell(self.cell)
        except ValueError as e:
            raise ValidationError("Invalid cell: {}".format(e.message))

        try:
            get_valid_pbc(self.pbc)
        except ValueError as e:
            raise ValidationError(
                "Invalid periodic boundary conditions: {}".format(e.message))

        try:
            # This will try to create the kinds objects
            kinds = self.kinds
        except ValueError as e:
            raise ValidationError(
                "Unable to validate the kinds: {}".format(e.message))

        from collections import Counter

        counts = Counter([k.name for k in kinds])
        for c in counts:
            if counts[c] != 1:
                raise ValidationError("Kind with name '{}' appears {} times "
                                      "instead of only one".format(
                    c, counts[c]))

        try:
            # This will try to create the sites objects
            sites = self.sites
        except ValueError as e:
            raise ValidationError(
                "Unable to validate the sites: {}".format(e.message))

        for site in sites:
            if site.kind_name not in [k.name for k in kinds]:
                raise ValidationError(
                    "A site has kind {}, but no specie with that name exists"
                    "".format(site.kind_name))

        kinds_without_sites = (
            set(k.name for k in kinds) - set(s.kind_name for s in sites))
        if kinds_without_sites:
            raise ValidationError("The following kinds are defined, but there "
                                  "are no sites with that kind: {}".format(
                list(kinds_without_sites)))

    def _prepare_xsf(self, main_file_name=""):
        """
        Write the given structure to a string of format XSF (for XCrySDen).
        """
        if self.is_alloy() or self.has_vacancies():
            raise NotImplementedError("XSF for alloys or systems with "
                                      "vacancies not implemented.")

        sites = self.sites

        return_string = "CRYSTAL\nPRIMVEC 1\n"
        for cell_vector in self.cell:
            return_string += " ".join(["%18.10f" % i for i in cell_vector])
            return_string += "\n"
        return_string += "PRIMCOORD 1\n"
        return_string += "%d 1\n" % len(sites)
        for site in sites:
            # I checked above that it is not an alloy, therefore I take the
            # first symbol
            return_string += "%s " % _atomic_numbers[
                self.get_kind(site.kind_name).symbols[0]]
            return_string += "%18.10f %18.10f %18.10f\n" % tuple(site.position)
        return return_string.encode('utf-8'), {}

    def _prepare_cif(self, main_file_name=""):
        """
        Write the given structure to a string of format CIF.
        """
        from aiida.orm.data.cif import CifData

        cif = CifData(ase=self.get_ase())
        return cif._prepare_cif()

    def _prepare_tcod(self, main_file_name="", **kwargs):
        """
        Write the given structure to a string of format TCOD CIF.
        """
        from aiida.tools.dbexporters.tcod import export_cif
        return export_cif(self, **kwargs).encode('utf-8'), {}

    def _prepare_xyz(self, main_file_name=""):
        """
        Write the given structure to a string of format XYZ.
        """
        if self.is_alloy() or self.has_vacancies():
            raise NotImplementedError("XYZ for alloys or systems with "
                                      "vacancies not implemented.")

        sites = self.sites
        cell = self.cell

        return_list = ["{}".format(len(sites))]
        return_list.append('Lattice="{} {} {} {} {} {} {} {} {}" pbc="{} {} {}"'.format(
            cell[0][0], cell[0][1], cell[0][2],
            cell[0][0], cell[0][1], cell[0][2],
            cell[0][0], cell[0][1], cell[0][2],
            self.pbc[0], self.pbc[1], self.pbc[2]
        ))
        for site in sites:
            # I checked above that it is not an alloy, therefore I take the
            # first symbol
            return_list.append("{:6s} {:18.10f} {:18.10f} {:18.10f}".format(
                self.get_kind(site.kind_name).symbols[0],
                site.position[0], site.position[1], site.position[2]))

        return_string = "\n".join(return_list)
        return return_string.encode('utf-8'), {}

    def _parse_xyz(self, inputstring):
        """
        Read the structure from a string of format XYZ.
        """

        # idiom to get to the last block
        atoms = None
        for _, _, atoms in xyz_parser_iterator(inputstring):
            pass

        if atoms is None:
            raise TypeError("The data does not contain any XYZ data")

        self.clear_kinds()
        self.pbc = (False, False, False)

        for sym, position in atoms:
            self.append_atom(symbols=sym, position=position)

    def _adjust_default_cell(self, vacuum_factor=1.0, vacuum_addition=10.0,
                             pbc=(False, False, False)):
        """
        If the structure was imported from an xyz file, it lacks a defined cell,
        and the default cell is taken ([[1,0,0], [0,1,0], [0,0,1]]),
        leading to an unphysical definition of the structure.
        This method will adjust the cell
        """
        import numpy as np
        from ase.visualize import view
        from aiida.common.utils import get_extremas_from_positions

        # First, set PBC
        # All the checks are done in get_valid_pbc called by set_pbc, no need to check anything here
        self.set_pbc(pbc)

        # Calculating the minimal cell:
        positions = np.array([site.position for site in self.sites])
        position_min, position_max = get_extremas_from_positions(positions)

        # Translate the structure to the origin, such that the minimal values in each dimension
        # amount to (0,0,0)
        positions -= position_min
        for index, site in enumerate(self.get_attr('sites')):
            site['position'] = list(positions[index])

        # The orthorhombic cell that (just) accomodates the whole structure is now given by the
        # extremas of position in each dimension:
        minimal_orthorhombic_cell_dimensions = np.array(
            get_extremas_from_positions(positions)[1])
        minimal_orthorhombic_cell_dimensions = np.dot(vacuum_factor,
                                                      minimal_orthorhombic_cell_dimensions)
        minimal_orthorhombic_cell_dimensions += vacuum_addition

        # Transform the vector (a, b, c ) to [[a,0,0], [0,b,0], [0,0,c]]
        newcell = np.diag(minimal_orthorhombic_cell_dimensions)
        self.set_cell(newcell.tolist())

    def get_symbols_set(self):
        """
        Return a set containing the names of all elements involved in
        this structure (i.e., for it joins the list of symbols for each
        kind k in the structure).

        :returns: a set of strings of element names.
        """
        return set(itertools.chain.from_iterable(
            kind.symbols for kind in self.kinds))

    def get_formula(self, mode='hill', separator=""):
        """
        Return a string with the chemical formula.

        :param mode: a string to specify how to generate the formula, can
            assume one of the following values:

            * 'hill' (default): count the number of atoms of each species,
              then use Hill notation, i.e. alphabetical order with C and H
              first if one or several C atom(s) is (are) present, e.g.
              ``['C','H','H','H','O','C','H','H','H']`` will return ``'C2H6O'``
              ``['S','O','O','H','O','H','O']``  will return ``'H2O4S'``
              From E. A. Hill, J. Am. Chem. Soc., 22 (8), pp 478–494 (1900)

            * 'hill_compact': same as hill but the number of atoms for each
              species is divided by the greatest common divisor of all of them, e.g.
              ``['C','H','H','H','O','C','H','H','H','O','O','O']``
              will return ``'CH3O2'``

            * 'reduce': group repeated symbols e.g.
              ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
              'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'BaTiO3BaTiO3BaTi2O3'``

            * 'group': will try to group as much as possible parts of the formula
              e.g.
              ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
              'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'(BaTiO3)2BaTi2O3'``

            * 'count': same as hill (i.e. one just counts the number
              of atoms of each species) without the re-ordering (take the
              order of the atomic sites), e.g.
              ``['Ba', 'Ti', 'O', 'O', 'O','Ba', 'Ti', 'O', 'O', 'O']``
              will return ``'Ba2Ti2O6'``

            * 'count_compact': same as count but the number of atoms
              for each species is divided by the greatest common divisor of
              all of them, e.g.
              ``['Ba', 'Ti', 'O', 'O', 'O','Ba', 'Ti', 'O', 'O', 'O']``
              will return ``'BaTiO3'``

        :param separator: a string used to concatenate symbols. Default empty.

        :return: a string with the formula

        .. note:: in modes reduce, group, count and count_compact, the
            initial order in which the atoms were appended by the user is
            used to group and/or order the symbols in the formula
        """

        symbol_list = [self.get_kind(s.kind_name).get_symbols_string()
                       for s in self.sites]

        return get_formula(symbol_list, mode=mode, separator=separator)

    def get_site_kindnames(self):
        """
        Return a list with length equal to the number of sites of this structure,
        where each element of the list is the kind name of the corresponding site.

        .. note:: This is NOT necessarily a list of chemical symbols! Use
            ``[ self.get_kind(s.kind_name).get_symbols_string() for s in self.sites]``
            for chemical symbols

        :return: a list of strings
        """
        return [this_site.kind_name for this_site in self.sites]

    def get_composition(self):
        """
        Returns the chemical composition of this structure as a dictionary,
        where each key is the kind symbol (e.g. H, Li, Ba),
        and each value is the number of occurences of that element in this
        structure. For BaZrO3 it would return {'Ba':1, 'Zr':1, 'O':3}.
        No reduction with smallest common divisor!

        :returns: a dictionary with the composition
        """
        symbols_list = [self.get_kind(s.kind_name).get_symbols_string()
                        for s in self.sites]
        composition = {
            symbol: symbols_list.count(symbol)
            for symbol
            in set(symbols_list)
            }
        return composition

    def get_ase(self):
        """
        Get the ASE object.
        Requires to be able to import ase.

        :return: an ASE object corresponding to this
          :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
          object.

        .. note:: If any site is an alloy or has vacancies, a ValueError
            is raised (from the site.get_ase() routine).
        """
        return self._get_object_ase()

    def get_pymatgen(self):
        """
        Get pymatgen object. Returns Structure for structures with
        periodic boundary conditions (in three dimensions) and Molecule
        otherwise.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        return self._get_object_pymatgen()

    def get_pymatgen_structure(self):
        """
        Get the pymatgen Structure object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).

        :return: a pymatgen Structure object corresponding to this
          :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
          object.
        :raise ValueError: if periodic boundary conditions do not hold
          in at least one dimension of real space.
        """
        return self._get_object_pymatgen_structure()

    def get_pymatgen_molecule(self):
        """
        Get the pymatgen Molecule object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).

        :return: a pymatgen Molecule object corresponding to this
          :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
          object.
        """
        return self._get_object_pymatgen_molecule()

    def append_kind(self, kind):
        """
        Append a kind to the
        :py:class:`StructureData <aiida.orm.data.structure.StructureData>`.
        It makes a copy of the kind.

        :param kind: the site to append, must be a Kind object.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed(
                "The StructureData object cannot be modified, "
                "it has already been stored")

        new_kind = Kind(kind=kind)  # So we make a copy

        if kind.name in [k.name for k in self.kinds]:
            raise ValueError("A kind with the same name ({}) already exists."
                             "".format(kind.name))

        # If here, no exceptions have been raised, so I add the site.
        # I join two lists. Do not use .append, which would work in-place
        self._set_attr('kinds',
                       self.get_attr('kinds', []) + [new_kind.get_raw()])
        # Note, this is a dict (with integer keys) so it allows for empty
        # spots!
        if not hasattr(self, '_internal_kind_tags'):
            self._internal_kind_tags = {}
        self._internal_kind_tags[len(
            self.get_attr('kinds')) - 1] = kind._internal_tag

    def append_site(self, site):
        """
        Append a site to the
        :py:class:`StructureData <aiida.orm.data.structure.StructureData>`.
        It makes a copy of the site.

        :param site: the site to append. It must be a Site object.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed(
                "The StructureData object cannot be modified, "
                "it has already been stored")

        new_site = Site(site=site)  # So we make a copy

        if site.kind_name not in [k.name for k in self.kinds]:
            raise ValueError("No kind with name '{}', available kinds are: "
                             "{}".format(site.kind_name,
                                         [k.name for k in self.kinds]))

        # If here, no exceptions have been raised, so I add the site.
        # I join two lists. Do not use .append, which would work in-place
        self._set_attr('sites',
                       self.get_attr('sites', []) + [new_site.get_raw()])

    def append_atom(self, **kwargs):
        """
        Append an atom to the Structure, taking care of creating the
        corresponding kind.

        :param ase: the ase Atom object from which we want to create a new atom
                (if present, this must be the only parameter)
        :param position: the position of the atom (three numbers in angstrom)
        :param symbols: passed to the constructor of the Kind object.
        :param weights: passed to the constructor of the Kind object.
        :param name: passed to the constructor of the Kind object. See also the note below.

        .. note :: Note on the 'name' parameter (that is, the name of the kind):

            * if specified, no checks are done on existing species. Simply,
              a new kind with that name is created. If there is a name
              clash, a check is done: if the kinds are identical, no error
              is issued; otherwise, an error is issued because you are trying
              to store two different kinds with the same name.

            * if not specified, the name is automatically generated. Before
              adding the kind, a check is done. If other species with the
              same properties already exist, no new kinds are created, but
              the site is added to the existing (identical) kind.
              (Actually, the first kind that is encountered).
              Otherwise, the name is made unique first, by adding to the string
              containing the list of chemical symbols a number starting from 1,
              until an unique name is found

        .. note :: checks of equality of species are done using
          the :py:meth:`~Kind.compare_with` method.
        """
        aseatom = kwargs.pop('ase', None)
        if aseatom is not None:
            if kwargs:
                raise ValueError("If you pass 'ase' as a parameter to "
                                 "append_atom, you cannot pass any further"
                                 "parameter")
            position = aseatom.position
            kind = Kind(ase=aseatom)
        else:
            position = kwargs.pop('position', None)
            if position is None:
                raise ValueError("You have to specify the position of the "
                                 "new atom")
            # all remaining parameters
            kind = Kind(**kwargs)

        # I look for identical species only if the name is not specified
        _kinds = self.kinds

        if 'name' not in kwargs:
            # If the kind is identical to an existing one, I use the existing
            # one, otherwise I replace it
            exists_already = False
            for idx, existing_kind in enumerate(_kinds):
                try:
                    existing_kind._internal_tag = self._internal_kind_tags[idx]
                except KeyError:
                    # self._internal_kind_tags does not contain any info for
                    # the kind in position idx: I don't have to add anything
                    # then, and I continue
                    pass
                if (kind.compare_with(existing_kind)[0]):
                    kind = existing_kind
                    exists_already = True
                    break
            if not exists_already:
                # There is not an identical kind.
                # By default, the name of 'kind' just contains the elements.
                # I then check that the name of 'kind' does not already exist,
                # and if it exists I add a number (starting from 1) until I
                # find a non-used name.
                existing_names = [k.name for k in _kinds]
                simplename = kind.name
                counter = 1
                while kind.name in existing_names:
                    kind.name = "{}{}".format(simplename, counter)
                    counter += 1
                self.append_kind(kind)
        else:  # 'name' was specified
            old_kind = None
            for existing_kind in _kinds:
                if existing_kind.name == kwargs['name']:
                    old_kind = existing_kind
                    break
            if old_kind is None:
                self.append_kind(kind)
            else:
                is_the_same, firstdiff = kind.compare_with(old_kind)
                if is_the_same:
                    kind = old_kind
                else:
                    raise ValueError("You are explicitly setting the name "
                                     "of the kind to '{}', that already "
                                     "exists, but the two kinds are different!"
                                     " (first difference: {})".format(
                        kind.name, firstdiff))

        site = Site(kind_name=kind.name, position=position)
        self.append_site(site)

        # def _set_site_type(self, new_site, reset_type_if_needed):

    # """
    #         Check if the site can be added (i.e., if no other sites with the same type exist, or if
    #         they exist, then they are equal) and possibly sets its type.
    #
    #         Args:
    #             new_site: the new site to check, must be a Site object.
    #             reset_type_if_needed: if False, an exception is raised if a site with same type but different
    #                 properties (mass, symbols, weights, ...) is found.
    #                 If True, and an atom with same type but different properties is found, all the sites
    #                 already present in self.sites are checked to see if there is a site with the same properties.
    #                 Then, the same type is set. Otherwise, a new type name is chosen adding a number to the site
    #                 name such that the type is different from the existing ones.
    #         """
    #         from aiida.common.exceptions import ModificationNotAllowed
    #
    #         if not self._to_be_stored:
    #             raise ModificationNotAllowed("The StructureData object cannot be modified, "
    #                 "it has already been stored")
    #
    #         type_list = self.get_types()
    #         if type_list:
    #             types, positions = zip(*type_list)
    #         else:
    #             types = []
    #             positions = []
    #
    #         if new_site.type not in types:
    #             # There is no element with this type, OK to insert
    #             return
    #
    #         # I get the index of the type, and the
    #         # first atom of this type (there should always be at least one!)
    #         type_idx = types.index(new_site.type)
    #         site_idx = positions[type_idx][0]
    #
    #         # If it is of the same type, I am happy
    #         is_same_type, differences_str = new_site.compare_type(self.sites[site_idx])
    #         if is_same_type:
    #             return
    #
    #         # If I am here, the type string is the same, but they are actually of different type!
    #
    #         if not reset_type_if_needed:
    #             errstr = ("The site you are trying to insert is of type '{}'. However, another site already "
    #                       "exists with same type, but with different properties! ({})".format(
    #                          new_site.type, differences_str))
    #             raise ValueError(errstr)
    #
    #         # I check if there is a atom of the same type
    #         for site in self.sites:
    #             is_same_type, _ = new_site.compare_type(site)
    #             if is_same_type:
    #                 new_site.type = site.type
    #                 return
    #
    #         # If I am here, I didn't find any existing site which is of the same type
    #         existing_type_names = [the_type for the_type in types if the_type.startswith(new_site.type)]
    #
    #         append_int = 1
    #         while True:
    #             new_typename = "{:s}{:d}".format(new_site.type, append_int)
    #             if new_typename not in existing_type_names:
    #                 break
    #             append_int += 1
    #         new_site.type = new_typename

    def clear_kinds(self):
        """
        Removes all kinds for the StructureData object.

        .. note:: Also clear all sites!
        """
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed(
                "The StructureData object cannot be modified, "
                "it has already been stored")

        self._set_attr('kinds', [])
        self._internal_kind_tags = {}
        self.clear_sites()

    def clear_sites(self):
        """
        Removes all sites for the StructureData object.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed(
                "The StructureData object cannot be modified, "
                "it has already been stored")

        self._set_attr('sites', [])

    @property
    def sites(self):
        """
        Returns a list of sites.
        """
        try:
            raw_sites = self.get_attr('sites')
        except AttributeError:
            raw_sites = []
        return [Site(raw=i) for i in raw_sites]

    @property
    def kinds(self):
        """
        Returns a list of kinds.
        """
        try:
            raw_kinds = self.get_attr('kinds')
        except AttributeError:
            raw_kinds = []
        return [Kind(raw=i) for i in raw_kinds]

    def get_kind(self, kind_name):
        """
        Return the kind object associated with the given kind name.

        :param kind_name: String, the name of the kind you want to get

        :return: The Kind object associated with the given kind_name, if
           a Kind with the given name is present in the structure.

        :raise: ValueError if the kind_name is not present.
        """
        # Cache the kinds, if stored, for efficiency
        if self.is_stored:
            try:
                kinds_dict = self._kinds_cache
            except AttributeError:
                self._kinds_cache = {_.name: _ for _ in self.kinds}
                kinds_dict = self._kinds_cache
        else:
            kinds_dict = {_.name: _ for _ in self.kinds}

        # Will raise ValueError if the kind is not present
        try:
            return kinds_dict[kind_name]
        except KeyError:
            raise ValueError("Kind name '{}' unknown".format(kind_name))

    def get_kind_names(self):
        """
        Return a list of kind names (in the same order of the ``self.kinds``
        property, but return the names rather than Kind objects)

        .. note:: This is NOT necessarily a list of chemical symbols! Use
            get_symbols_set for chemical symbols

        :return: a list of strings.
        """
        return [k.name for k in self.kinds]

    @property
    def cell(self):
        """
        Returns the cell shape.

        :return: a 3x3 list of lists.
        """
        return copy.deepcopy(self.get_attr('cell'))

    @cell.setter
    def cell(self, value):
        self.set_cell(value)

    def set_cell(self, value):
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed(
                "The StructureData object cannot be modified, "
                "it has already been stored")

        the_cell = _get_valid_cell(value)
        self._set_attr('cell', the_cell)

    def reset_cell(self, new_cell):
        """
        Reset the cell of a structure not yet stored to a new value.

        :param new_cell: list specifying the cell vectors

        :raises:
            ModificationNotAllowed: if object is already stored
        """
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed()

        self._set_attr('cell', new_cell)

    def reset_sites_positions(self, new_positions, conserve_particle=True):
        """
        Replace all the Site positions attached to the Structure

        :param new_positions: list of (3D) positions for every sites.

        :param conserve_particle: if True, allows the possibility of removing a site.
            currently not implemented.

        :raises ModificationNotAllowed: if object is stored already
        :raises ValueError: if positions are invalid

        .. note:: it is assumed that the order of the new_positions is
            given in the same order of the one it's substituting, i.e. the
            kind of the site will not be checked.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed()

        if not conserve_particle:
            # TODO:
            raise NotImplementedError
        else:

            # test consistency of th enew input
            n_sites = len(self.sites)
            if n_sites != len(new_positions) and conserve_particle:
                raise ValueError(
                    "the new positions should be as many as the previous structure.")

            new_sites = []
            for i in range(n_sites):
                try:
                    this_pos = [float(j) for j in new_positions[i]]
                except ValueError:
                    raise ValueError(
                        "Expecting a list of floats. Found instead {}"
                        .format(new_positions[i]))

                if len(this_pos) != 3:
                    raise ValueError("Expecting a list of lists of length 3. "
                                     "found instead {}".format(len(this_pos)))

                # now append this Site to the new_site list.
                new_site = Site(site=self.sites[i])  # So we make a copy
                new_site.position = copy.deepcopy(this_pos)
                new_sites.append(new_site)

            # now clear the old sites, and substitute with the new ones
            self.clear_sites()
            for this_new_site in new_sites:
                self.append_site(this_new_site)

    @property
    def pbc(self):
        """
        Get the periodic boundary conditions.

        :return: a tuple of three booleans, each one tells if there are periodic
            boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        # return copy.deepcopy(self._pbc)
        return (
        self.get_attr('pbc1'), self.get_attr('pbc2'), self.get_attr('pbc3'))

    @pbc.setter
    def pbc(self, value):
        self.set_pbc(value)

    def set_pbc(self, value):
        from aiida.common.exceptions import ModificationNotAllowed

        if self.is_stored:
            raise ModificationNotAllowed(
                "The StructureData object cannot be modified, "
                "it has already been stored")
        the_pbc = get_valid_pbc(value)

        # self._pbc = the_pbc
        self._set_attr('pbc1', the_pbc[0])
        self._set_attr('pbc2', the_pbc[1])
        self._set_attr('pbc3', the_pbc[2])

    @property
    def cell_lengths(self):
        """
        Get the lengths of cell lattice vectors in angstroms.
        """
        import numpy

        cell = self.cell
        return [
            numpy.linalg.norm(cell[0]),
            numpy.linalg.norm(cell[1]),
            numpy.linalg.norm(cell[2]),
        ]

    @cell_lengths.setter
    def cell_lengths(self, value):
        self.set_cell_lengths(value)

    def set_cell_lengths(self, value):
        raise NotImplementedError("Modification is not implemented yet")

    @property
    def cell_angles(self):
        """
        Get the angles between the cell lattice vectors in degrees.
        """
        import numpy

        cell = self.cell
        lengths = self.cell_lengths
        return [float(numpy.arccos(x) / numpy.pi * 180) for x in [
            numpy.vdot(cell[1], cell[2]) / lengths[1] / lengths[2],
            numpy.vdot(cell[0], cell[2]) / lengths[0] / lengths[2],
            numpy.vdot(cell[0], cell[1]) / lengths[0] / lengths[1],
        ]]

    @cell_angles.setter
    def cell_angles(self, value):
        self.set_cell_angles(value)

    def set_cell_angles(self, value):
        raise NotImplementedError("Modification is not implemented yet")

    def is_alloy(self):
        """
        To understand if there are alloys in the structure.

        :return: a boolean, True if at least one kind is an alloy
        """
        return any(s.is_alloy() for s in self.kinds)

    def has_vacancies(self):
        """
        To understand if there are vacancies in the structure.

        :return: a boolean, True if at least one kind has a vacancy
        """
        return any(s.has_vacancies() for s in self.kinds)

    def get_cell_volume(self):
        """
        Returns the cell volume in Angstrom^3.

        :return: a float.
        """
        return calc_cell_volume(self.cell)

    def _get_cif(self, converter='ase', store=False, **kwargs):
        """
        Creates :py:class:`aiida.orm.data.cif.CifData`.

        :param converter: specify the converter. Default 'ase'.
        :param store: If True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :return: :py:class:`aiida.orm.data.cif.CifData` node.
        """
        from aiida.orm.data.parameter import ParameterData
        import structure  # This same module

        param = ParameterData(dict=kwargs)
        try:
            conv_f = getattr(structure, '_get_cif_{}_inline'.format(converter))
        except AttributeError:
            raise ValueError(
                "No such converter '{}' available".format(converter))
        ret_dict = conv_f(struct=self, parameters=param, store=store)
        return ret_dict['cif']

    def _get_object_phonopyatoms(self):
        """
        Converts StructureData to PhonopyAtoms

        :return: a PhonopyAtoms object
        """
        from phonopy.structure.atoms import Atoms as PhonopyAtoms

        atoms = PhonopyAtoms(symbols=[_.kind_name for _ in self.sites])
        # Phonopy internally uses scaled positions, so you must store cell first!
        atoms.set_cell(self.cell)
        atoms.set_positions([_.position for _ in self.sites])

        return atoms

    def _get_object_ase(self):
        """
        Converts
        :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
        to ase.Atoms

        :return: an ase.Atoms object
        """
        import ase

        asecell = ase.Atoms(cell=self.cell, pbc=self.pbc)
        _kinds = self.kinds

        for site in self.sites:
            asecell.append(site.get_ase(kinds=_kinds))
        return asecell

    def _get_object_pymatgen(self):
        """
        Converts
        :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
        to pymatgen object

        :return: a pymatgen Structure for structures with periodic boundary
            conditions (in three dimensions) and Molecule otherwise

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        if self.pbc == (True, True, True):
            return self._get_object_pymatgen_structure()
        else:
            return self._get_object_pymatgen_molecule()

    def _get_object_pymatgen_structure(self):
        """
        Converts
        :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
        to pymatgen Structure object

        :return: a pymatgen Structure object corresponding to this
          :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
          object
        :raise ValueError: if periodic boundary conditions does not hold
          in at least one dimension of real space

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors)
        """
        from pymatgen.core.structure import Structure

        if self.pbc != (True, True, True):
            raise ValueError("Periodic boundary conditions must apply in "
                             "all three dimensions of real space")

        species = []
        for s in self.sites:
            k = self.get_kind(s.kind_name)
            species.append({s: w for s, w in zip(k.symbols, k.weights)})

        positions = [list(x.position) for x in self.sites]
        return Structure(self.cell, species, positions,
                         coords_are_cartesian=True)

    def _get_object_pymatgen_molecule(self):
        """
        Converts
        :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
        to pymatgen Molecule object

        :return: a pymatgen Molecule object corresponding to this
          :py:class:`StructureData <aiida.orm.data.structure.StructureData>`
          object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors)
        """
        from pymatgen.core.structure import Molecule

        species = []
        for s in self.sites:
            k = self.get_kind(s.kind_name)
            species.append({s: w for s, w in zip(k.symbols, k.weights)})

        positions = [list(x.position) for x in self.sites]
        return Molecule(species, positions)


class Kind(object):
    """
    This class contains the information about the species (kinds) of the system.

    It can be a single atom, or an alloy, or even contain vacancies.
    """

    def __init__(self, **kwargs):
        """
        Create a site.
        One can either pass:

        :param raw: the raw python dictionary that will be converted to a
               Kind object.
        :param ase: an ase Atom object
        :param kind: a Kind object (to get a copy)

        Or alternatively the following parameters:

        :param symbols: a single string for the symbol of this site, or a list
                   of symbol strings
        :param weights (optional): the weights for each atomic species of
                   this site.
                   If only a single symbol is provided, then this value is
                   optional and the weight is set to 1.
        :param mass (optional): the mass for this site in atomic mass units.
                   If not provided, the mass is set by the
                   self.reset_mass() function.
        :param name: a string that uniquely identifies the kind, and that
                   is used to identify the sites.
        """
        # Internal variables
        self._mass = None
        self._symbols = None
        self._weights = None
        self._name = None

        # It will be remain to None in general; it is used to further
        # identify this species. At the moment, it is used only when importing
        # from ASE, if the species had a tag (different from zero).
        ## NOTE! This is not persisted on DB but only used while the class
        # is loaded in memory (i.e., it is not output with the get_raw() method)
        self._internal_tag = None

        # Logic to create the site from the raw format
        if 'raw' in kwargs:
            if len(kwargs) != 1:
                raise ValueError("If you pass 'raw', then you cannot pass "
                                 "any other parameter.")

            raw = kwargs['raw']

            try:
                self.set_symbols_and_weights(raw['symbols'], raw['weights'])
            except KeyError:
                raise ValueError("You didn't specify either 'symbols' or "
                                 "'weights' in the raw site data.")
            try:
                self.mass = raw['mass']
            except KeyError:
                raise ValueError("You didn't specify the site mass in the "
                                 "raw site data.")

            try:
                self.name = raw['name']
            except KeyError:
                raise ValueError("You didn't specify the name in the "
                                 "raw site data.")

        elif 'kind' in kwargs:
            if len(kwargs) != 1:
                raise ValueError("If you pass 'kind', then you cannot pass "
                                 "any other parameter.")
            oldkind = kwargs['kind']

            try:
                self.set_symbols_and_weights(oldkind.symbols, oldkind.weights)
                self.mass = oldkind.mass
                self.name = oldkind.name
                self._internal_tag = oldkind._internal_tag
            except AttributeError:
                raise ValueError("Error using the Kind object. Are you sure "
                                 "it is a Kind object? [Introspection says it is "
                                 "{}]".format(str(type(oldkind))))

        elif 'ase' in kwargs:
            aseatom = kwargs['ase']
            if len(kwargs) != 1:
                raise ValueError("If you pass 'ase', then you cannot pass "
                                 "any other parameter.")

            try:
                import numpy
                self.set_symbols_and_weights([aseatom.symbol], [1.])
                # ASE sets mass to numpy.nan for unstable species
                if not numpy.isnan(aseatom.mass):
                    self.mass = aseatom.mass
                else:
                    self.reset_mass()
            except AttributeError:
                raise ValueError("Error using the aseatom object. Are you sure "
                                 "it is a ase.atom.Atom object? [Introspection says it is "
                                 "{}]".format(str(type(aseatom))))
            if aseatom.tag != 0:
                self.set_automatic_kind_name(tag=aseatom.tag)
                self._internal_tag = aseatom.tag
            else:
                self.set_automatic_kind_name()
        else:
            if 'symbols' not in kwargs:
                raise ValueError("'symbols' need to be "
                                 "specified (at least) to create a Site object. Otherwise, "
                                 "pass a raw site using the 'raw' parameter.")
            weights = kwargs.pop('weights', None)
            self.set_symbols_and_weights(kwargs.pop('symbols'), weights)
            try:
                self.mass = kwargs.pop('mass')
            except KeyError:
                self.reset_mass()
            try:
                self.name = kwargs.pop('name')
            except KeyError:
                self.set_automatic_kind_name()
            if kwargs:
                raise ValueError("Unrecognized parameters passed to Kind "
                                 "constructor: {}".format(kwargs.keys()))

    def get_raw(self):
        """
        Return the raw version of the site, mapped to a suitable dictionary.
        This is the format that is actually used to store each kind of the
        structure in the DB.

        :return: a python dictionary with the kind.
        """
        return {
            'symbols': self.symbols,
            'weights': self.weights,
            'mass': self.mass,
            'name': self.name,
        }

        # def get_ase(self):

    # """
    #         Return a ase.Atom object for this kind, setting the position to
    #         the origin.
    #
    #         Note: If any site is an alloy or has vacancies, a ValueError is
    #             raised (from the site.get_ase() routine).
    #         """
    #         import ase
    #         if self.is_alloy() or self.has_vacancies():
    #             raise ValueError("Cannot convert to ASE if the site is an alloy "
    #                              "or has vacancies.")
    #         aseatom = ase.Atom(position=[0.,0.,0.], symbol=self.symbols[0],
    #                            mass=self.mass)
    #         return aseatom

    def reset_mass(self):
        """
        Reset the mass to the automatic calculated value.

        The mass can be set manually; by default, if not provided,
        it is the mass of the constituent atoms, weighted with their
        weight (after the weight has been normalized to one to take
        correctly into account vacancies).

        This function uses the internal _symbols and _weights values and
        thus assumes that the values are validated.

        It sets the mass to None if the sum of weights is zero.
        """
        w_sum = sum(self._weights)

        if abs(w_sum) < _sum_threshold:
            self._mass = None
            return

        normalized_weights = (i / w_sum for i in self._weights)
        element_masses = (_atomic_masses[sym] for sym in self._symbols)
        # Weighted mass
        self._mass = sum([i * j for i, j in
                          zip(normalized_weights, element_masses)])

    @property
    def name(self):
        """
        Return the name of this kind.
        The name of a kind is used to identify the species of a site.

        :return: a string
        """
        return self._name

    @name.setter
    def name(self, value):
        """
        Set the name of this site (a string).
        """
        self._name = unicode(value)

    def set_automatic_kind_name(self, tag=None):
        """
        Set the type to a string obtained with the symbols appended one
        after the other, without spaces, in alphabetical order;
        if the site has a vacancy, a X is appended at the end too.
        """
        sorted_symbol_list = list(set(self.symbols))
        sorted_symbol_list.sort()  # In-place sort
        name_string = "".join(sorted_symbol_list)
        if self.has_vacancies():
            name_string += "X"
        if tag is None:
            self.name = name_string
        else:
            self.name = "{}{}".format(name_string, tag)

    def compare_with(self, other_kind):
        """
        Compare with another Kind object to check if they are different.

        .. note:: This does NOT check the 'type' attribute. Instead, it compares
            (with reasonable thresholds, where applicable): the mass, and the list
            of symbols and of weights. Moreover, it compares the
            ``_internal_tag``, if defined (at the moment, defined automatically
            only when importing the Kind from ASE, if the atom has a non-zero tag).
            Note that the _internal_tag is only used while the class is loaded,
            but is not persisted on the database.

        :return: A tuple with two elements. The first one is True if the two sites
            are 'equivalent' (same mass, symbols and weights), False otherwise.
            The second element of the tuple is a string,
            which is either None (if the first element was True), or contains
            a 'human-readable' description of the first difference encountered
            between the two sites.
        """
        # Check length of symbols
        if len(self.symbols) != len(other_kind.symbols):
            return (False, "Different length of symbols list")

        # Check list of symbols
        for i in range(len(self.symbols)):
            if self.symbols[i] != other_kind.symbols[i]:
                return (False, "Symbol at position {:d} are different "
                               "({} vs. {})".format(
                    i + 1, self.symbols[i], other_kind.symbols[i]))
        # Check weights (assuming length of weights and of symbols have same
        # length, which should be always true
        for i in range(len(self.weights)):
            if self.weights[i] != other_kind.weights[i]:
                return (False, "Weight at position {:d} are different "
                               "({} vs. {})".format(
                    i + 1, self.weights[i], other_kind.weights[i]))
        # Check masses
        if abs(self.mass - other_kind.mass) > _mass_threshold:
            return (False, "Masses are different ({} vs. {})"
                           "".format(self.mass, other_kind.mass))

        if self._internal_tag != other_kind._internal_tag:
            return (False, "Internal tags are different ({} vs. {})"
                           "".format(self._internal_tag,
                                     other_kind._internal_tag))

        # If we got here, the two Site objects are similar enough
        # to be considered of the same kind
        return (True, "")

    @property
    def mass(self):
        """
        The mass of this species kind.

        :return: a float
        """
        return self._mass

    @mass.setter
    def mass(self, value):
        the_mass = float(value)
        if the_mass <= 0:
            raise ValueError("The mass must be positive.")
        self._mass = the_mass

    @property
    def weights(self):
        """
        Weights for this species kind. Refer also to
        :func:validate_symbols_tuple for the validation rules on the weights.
        """
        return copy.deepcopy(self._weights)

    @weights.setter
    def weights(self, value):
        """
        If value is a number, a single weight is used. Otherwise, a list or
        tuple of numbers is expected.
        None is also accepted, corresponding to the list [1.].
        """
        weights_tuple = _create_weights_tuple(value)

        if len(weights_tuple) != len(self._symbols):
            raise ValueError("Cannot change the number of weights. Use the "
                             "set_symbols_and_weights function instead.")
        validate_weights_tuple(weights_tuple, _sum_threshold)

        self._weights = weights_tuple

    def get_symbols_string(self):
        """
        Return a string that tries to match as good as possible the symbols
        of this kind. If there is only one symbol (no alloy) with 100%
        occupancy, just returns the symbol name. Otherwise, groups the full
        string in curly brackets, and try to write also the composition
        (with 2 precision only).

        .. note:: If there is a vacancy (sum of weights<1), we indicate it
            with the X symbol followed by 1-sum(weights) (still with 2
            digits precision, so it can be 0.00)

        .. note:: Note the difference with respect to the symbols and the
            symbol properties!
        """
        return get_symbols_string(self._symbols, self._weights)

    @property
    def symbol(self):
        """
        If the kind has only one symbol, return it; otherwise, raise a
        ValueError.
        """
        if len(self._symbols) == 1:
            return self._symbols[0]
        else:
            raise ValueError("This kind has more than one symbol (it is an "
                             "alloy): {}".format(self._symbols))

    @property
    def symbols(self):
        """
        List of symbols for this site. If the site is a single atom,
        pass a list of one element only, or simply the string for that atom.
        For alloys, a list of elements.

        .. note:: Note that if you change the list of symbols, the kind
            name remains unchanged.
        """
        return copy.deepcopy(self._symbols)

    @symbols.setter
    def symbols(self, value):
        """
        If value is a string, a single symbol is used. Otherwise, a list or
        tuple of strings is expected.

        I set a copy of the list, so to avoid that the content changes
        after the value is set.
        """
        symbols_tuple = _create_symbols_tuple(value)

        if len(symbols_tuple) != len(self._weights):
            raise ValueError("Cannot change the number of symbols. Use the "
                             "set_symbols_and_weights function instead.")
        validate_symbols_tuple(symbols_tuple)

        self._symbols = symbols_tuple

    def set_symbols_and_weights(self, symbols, weights):
        """
        Set the chemical symbols and the weights for the site.

        .. note:: Note that the kind name remains unchanged.
        """
        symbols_tuple = _create_symbols_tuple(symbols)
        weights_tuple = _create_weights_tuple(weights)
        if len(symbols_tuple) != len(weights_tuple):
            raise ValueError("The number of symbols and weights must coincide.")
        validate_symbols_tuple(symbols_tuple)
        validate_weights_tuple(weights_tuple, _sum_threshold)
        self._symbols = symbols_tuple
        self._weights = weights_tuple

    def is_alloy(self):
        """
        To understand if kind is an alloy.

        :return: True if the kind has more than one element (i.e.,
            len(self.symbols) != 1), False otherwise.
        """
        return len(self._symbols) != 1

    def has_vacancies(self):
        """
        Returns True if the sum of the weights is less than one.
        It uses the internal variable _sum_threshold as a threshold.

        :return: a boolean
        """
        return has_vacancies(self._weights)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        symbol = self.get_symbols_string()
        return "name '{}', symbol '{}'".format(self.name, symbol)


class Site(object):
    """
    This class contains the information about a given site of the system.

    It can be a single atom, or an alloy, or even contain vacancies.
    """

    def __init__(self, **kwargs):
        """
        Create a site.

        :param kind_name: a string that identifies the kind (species) of this site.
                This has to be found in the list of kinds of the StructureData
                object.
                Validation will be done at the StructureData level.
        :param position: the absolute position (three floats) in angstrom
        """
        self._kind_name = None
        self._position = None

        if 'site' in kwargs:
            site = kwargs.pop('site')
            if kwargs:
                raise ValueError("If you pass 'site', you cannot pass any "
                                 "further parameter to the Site constructor")
            if not isinstance(site, Site):
                raise ValueError("'site' must be of type Site")
            self.kind_name = site.kind_name
            self.position = site.position
        elif 'raw' in kwargs:
            raw = kwargs.pop('raw')
            if kwargs:
                raise ValueError("If you pass 'raw', you cannot pass any "
                                 "further parameter to the Site constructor")
            try:
                self.kind_name = raw['kind_name']
                self.position = raw['position']
            except KeyError as e:
                raise ValueError("Invalid raw object, it does not contain any "
                                 "key {}".format(e.message))
            except TypeError:
                raise ValueError("Invalid raw object, it is not a dictionary")

        else:
            try:
                self.kind_name = kwargs.pop('kind_name')
                self.position = kwargs.pop('position')
            except KeyError as e:
                raise ValueError("You need to specify {}".format(e.message))
            if kwargs:
                raise ValueError("Unrecognized parameters: {}".format(
                    kwargs.keys))

    def get_raw(self):
        """
        Return the raw version of the site, mapped to a suitable dictionary.
        This is the format that is actually used to store each site of the
        structure in the DB.

        :return: a python dictionary with the site.
        """
        return {
            'position': self.position,
            'kind_name': self.kind_name,
        }

    def get_ase(self, kinds):
        """
        Return a ase.Atom object for this site.

        :param kinds: the list of kinds from the StructureData object.

        .. note:: If any site is an alloy or has vacancies, a ValueError
            is raised (from the site.get_ase() routine).
        """
        from collections import defaultdict
        import ase

        # I create the list of tags
        tag_list = []
        used_tags = defaultdict(list)
        for k in kinds:
            # Skip alloys and vacancies
            if k.is_alloy() or k.has_vacancies():
                tag_list.append(None)
            # If the kind name is equal to the specie name,
            # then no tag should be set
            elif unicode(k.name) == unicode(k.symbols[0]):
                tag_list.append(None)
            else:
                # Name is not the specie name
                if k.name.startswith(k.symbols[0]):
                    try:
                        new_tag = int(k.name[len(k.symbols[0])])
                        tag_list.append(new_tag)
                        used_tags[k.symbols[0]].append(new_tag)
                        continue
                    except ValueError:
                        pass
                tag_list.append(k.symbols[0])  # I use a string as a placeholder

        for i in range(len(tag_list)):
            # If it is a string, it is the name of the element,
            # and I have to generate a new integer for this element
            # and replace tag_list[i] with this new integer
            if isinstance(tag_list[i], basestring):
                # I get a list of used tags for this element
                existing_tags = used_tags[tag_list[i]]
                if existing_tags:
                    new_tag = max(existing_tags) + 1
                else:  # empty list
                    new_tag = 1
                # I store it also as a used tag!
                used_tags[tag_list[i]].append(new_tag)
                # I update the tag
                tag_list[i] = new_tag

        found = False
        for k, t in zip(kinds, tag_list):
            if k.name == self.kind_name:
                kind = k
                tag = t
                found = True
                break
        if not found:
            raise ValueError("No kind '{}' has been found in the list of kinds"
                             "".format(self.kind_name))

        if kind.is_alloy() or kind.has_vacancies():
            raise ValueError("Cannot convert to ASE if the kind represents "
                             "an alloy or it has vacancies.")
        aseatom = ase.Atom(position=self.position,
                           symbol=str(kind.symbols[0]),
                           mass=kind.mass)
        if tag is not None:
            aseatom.tag = tag
        return aseatom

    @property
    def kind_name(self):
        """
        Return the kind name of this site (a string).

        The type of a site is used to decide whether two sites are identical
        (same mass, symbols, weights, ...) or not.
        """
        return self._kind_name

    @kind_name.setter
    def kind_name(self, value):
        """
        Set the type of this site (a string).
        """
        self._kind_name = unicode(value)

    @property
    def position(self):
        """
        Return the position of this site in absolute coordinates,
        in angstrom.
        """
        return copy.deepcopy(self._position)

    @position.setter
    def position(self, value):
        """
        Set the position of this site in absolute coordinates,
        in angstrom.
        """
        try:
            internal_pos = tuple(float(i) for i in value)
            if len(internal_pos) != 3:
                raise ValueError
        # value is not iterable or elements are not floats or len != 3
        except (ValueError, TypeError):
            raise ValueError("Wrong format for position, must be a list of "
                             "three float numbers.")
        self._position = internal_pos

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        return "kind name '{}' @ {},{},{}".format(self.kind_name,
                                                  self.position[0],
                                                  self.position[1],
                                                  self.position[2])

# get_structuredata_from_qeinput has been moved to:
# aiida.tools.codespecific.quantumespresso.qeinputparser
