# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy
import re

from six.moves import zip
import numpy as np

from aiida.common.constants import elements
from aiida.orm.nodes.data.structure import Kind, Site, StructureData
from aiida.engine import calcfunction

__all__ = ('structure_to_spglib_tuple', 'spglib_tuple_to_structure')


@calcfunction
def _get_cif_ase_inline(struct, parameters):
    """
    Creates :py:class:`aiida.orm.nodes.data.cif.CifData` using ASE.

    .. note:: requires ASE module.
    """
    from aiida.orm import CifData

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


def structure_to_spglib_tuple(structure):
    """
    Convert an AiiDA structure to a tuple of the format (cell, scaled_positions, element_numbers).

    :param structure: the AiiDA structure
    :return: (structure_tuple, kind_info, kinds) where structure_tuple
        is a tuple of format (cell, scaled_positions, element_numbers);
        kind_info is a dictionary mapping the kind_names to
        the numbers used in element_numbers. When possible, it uses
        the Z number of the element, otherwise it uses numbers > 1000;
        kinds is a list of the kinds of the structure.
    """
    def get_new_number(the_list, start_from):
        """
        Get the first integer >= start_from not yet in the list
        """
        retval = start_from
        comp_list = sorted(_ for _ in the_list if _ >= start_from)

        current_pos = 0
        found = False
        while not found:
            if len(comp_list) <= current_pos:
                return retval
            if retval == comp_list[current_pos]:
                current_pos += 1
                retval += 1
            else:
                found = True
                return retval

    Z = {v['symbol']: k for k, v in elements.items()}

    cell = np.array(structure.cell)
    abs_pos = np.array([_.position for _ in structure.sites])
    rel_pos = np.dot(abs_pos, np.linalg.inv(cell))
    kinds = {k.name: k for k in structure.kinds}

    kind_numbers = {}
    for kind in structure.kinds:
        if len(kind.symbols) == 1:
            realnumber = Z[kind.symbols[0]]
            if realnumber in kind_numbers.values():
                number = get_new_number(
                    list(kind_numbers.values()), start_from=realnumber * 1000)
            else:
                number = realnumber
            kind_numbers[kind.name] = number
        else:
            number = get_new_number(list(kind_numbers.values()), start_from=200000)
            kind_numbers[kind.name] = number

    numbers = [kind_numbers[s.kind_name] for s in structure.sites]

    return ((cell, rel_pos, numbers), kind_numbers, list(structure.kinds))


def spglib_tuple_to_structure(structure_tuple, kind_info=None, kinds=None):
    """
    Convert a tuple of the format (cell, scaled_positions, element_numbers) to an AiiDA structure.

    Unless the element_numbers are identical to the Z number of the atoms,
    you should pass both kind_info and kinds, with the same format as returned
    by get_tuple_from_aiida_structure.

    :param structure_tuple: the structure in format (structure_tuple, kind_info)
    :param kind_info: a dictionary mapping the kind_names to
       the numbers used in element_numbers. If not provided, assumes {element_name: element_Z}
    :param kinds: a list of the kinds of the structure.
    """
    if kind_info is None and kinds is not None:
        raise ValueError("If you pass kind_info, you should also pass kinds")
    if kinds is None and kind_info is not None:
        raise ValueError("If you pass kinds, you should also pass kind_info")

    Z = {v['symbol']: k for k, v in elements.items()}
    cell, rel_pos, numbers = structure_tuple
    if kind_info:
        _kind_info = copy.copy(kind_info)
        _kinds = copy.copy(kinds)
    else:
        try:
            # For each site
            symbols = [elements[num]['symbol'] for num in numbers]
        except KeyError as exc:
            raise ValueError("You did not pass kind_info, but at least one number "
                             "is not a valid Z number: {}".format(exc.args[0]))

        _kind_info = {elements[num]['symbol']: num for num in set(numbers)}
        # Get the default kinds
        _kinds = [Kind(symbols=sym) for sym in set(symbols)]

    _kinds_dict = {k.name: k for k in _kinds}
    # Now I will use in any case _kinds and _kind_info
    if len(_kind_info) != len(set(_kind_info.values())):
        raise ValueError(
            "There is at least a number repeated twice in kind_info!")
    # Invert the mapping
    mapping_num_kindname = {v: k for k, v in _kind_info.items()}
    # Create the actual mapping
    try:
        mapping_to_kinds = {num: _kinds_dict[kindname] for num, kindname
                            in mapping_num_kindname.items()}
    except KeyError as exc:
        raise ValueError(
            "Unable to find '{}' in the kinds list".format(exc.args[0]))

    try:
        site_kinds = [mapping_to_kinds[num] for num in numbers]
    except KeyError as exc:
        raise ValueError("Unable to find kind in kind_info for number {}".format(exc.args[0]))

    structure = StructureData(cell=cell)
    for k in _kinds:
        structure.append_kind(k)
    abs_pos = np.dot(rel_pos, cell)
    if len(abs_pos) != len(site_kinds):
        raise ValueError("The length of the positions array is different from the "
                         "length of the element numbers")

    for kind, pos in zip(site_kinds, abs_pos):
        structure.append_site(Site(kind_name=kind.name, position=pos))

    return structure


def xyz_parser_iterator(xyz_string):
    """
    Yields a tuple `(natoms, comment, atomiter)`for each frame
    in a XYZ file where `atomiter` is an iterator yielding a
    nested tuple `(symbol, (x, y, z))` for each entry.

    :param xyz_string: a string containing XYZ-structured text
    """

    class BlockIterator(object):
        """
        An iterator for wrapping the iterator returned by `match.finditer`
        to extract the required fields directly from the match object
        """

        def __init__(self, it, natoms):
            self._it = it
            self._natoms = natoms
            self._catom = 0

        def __iter__(self):
            return self

        def __next__(self):  # pylint: disable=missing-docstring
            try:
                match = next(self._it)
            except StopIteration:
                # if we reached the number of atoms declared, everything is well
                # and we re-raise the StopIteration exception
                if self._catom == self._natoms:
                    raise
                else:
                    # otherwise we got too less entries
                    raise TypeError("Number of atom entries ({}) is smaller than the number of atoms ({})".format(
                        self._catom, self._natoms))

            self._catom += 1

            if self._catom > self._natoms:
                raise TypeError("Number of atom entries ({}) is larger than the number of atoms ({})".format(
                    self._catom, self._natoms))

            return (match.group('sym'), (float(match.group('x')), float(match.group('y')), float(match.group('z'))))

        def next(self):
            """
            The iterator method expected by python 2.x,
            implemented as python 3.x style method.
            """
            return self.__next__()

    pos_regex = re.compile(
        r"""
^                                                                             # Linestart
[ \t]*                                                                        # Optional white space
(?P<sym>[A-Za-z]+[A-Za-z0-9]*)\s+                                             # get the symbol
(?P<x> [\+\-]?  ( \d*[\.]\d+  | \d+[\.]?\d* )  ([Ee][\+\-]?\d+)? ) [ \t]+     # Get x
(?P<y> [\+\-]?  ( \d*[\.]\d+  | \d+[\.]?\d* )  ([Ee][\+\-]?\d+)? ) [ \t]+     # Get y
(?P<z> [\+\-]?  ( \d*[\.]\d+  | \d+[\.]?\d* )  ([Ee][\+\-]?\d+)? )            # Get z
""", re.X | re.M)
    pos_block_regex = re.compile(
        r"""
                                                            # First line contains an integer
                                                            # and only an integer: the number of atoms
^[ \t]* (?P<natoms> [0-9]+) [ \t]*[\n]                      # End first line
(?P<comment>.*) [\n]                                        # The second line is a comment
(?P<positions>                                              # This is the block of positions
    (
        (
            \s*                                             # White space in front of the element spec is ok
            (
                [A-Za-z]+[A-Za-z0-9]*                       # Element spec
                (
                    \s+                                     # White space in front of the number
                    [\+\-]?                                 # Plus or minus in front of the number (optional)
                    (
                        (
                            \d*                             # optional decimal in the beginning .0001 is ok, for example
                            [\.]                            # There has to be a dot followed by
                            \d+                             # at least one decimal
                        )
                        |                                   # OR
                        (
                            \d+                             # at least one decimal, followed by
                            [\.]?                           # an optional dot
                            \d*                             # followed by optional decimals
                        )
                    )
                    ([Ee][\+\-]?\d+)?                       # optional exponents E+03, e-05
                ){3}                                        # I expect three float values
                |
                \#                                          # If a line is commented out, that is also ok
            )
            .*                                              # ignore what is after the comment or the position spec
            |                                               # OR
            \s*                                             # A line only containing white space
         )
        [\n]                                                # line break at the end
    )+
)                                                           # A positions block should be one or more lines
                    """, re.X | re.M)

    for block in pos_block_regex.finditer(xyz_string):
        natoms = int(block.group('natoms'))
        yield (natoms, block.group('comment'), BlockIterator(pos_regex.finditer(block.group('positions')), natoms))
