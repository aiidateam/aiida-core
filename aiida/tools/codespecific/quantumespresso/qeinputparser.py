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
Tools for parsing QE PW input files and creating AiiDa Node objects based on
them.

TODO: Parse CONSTRAINTS, OCCUPATIONS, ATOMIC_FORCES once they are implemented
      in AiiDA
"""
import re
import os
import numpy as np
from aiida.parsers.plugins.quantumespresso.constants import bohr_to_ang
from aiida.common.exceptions import ParsingError
from aiida.orm.data.structure import StructureData, _valid_symbols
from aiida.orm.calculation.job.quantumespresso import _uppercase_dict
from aiida.common.constants import bohr_to_ang
from aiida.common.exceptions import InputValidationError


RE_FLAGS = re.M | re.X | re.I

class QeInputFile(object):
    """
    Class used for parsing Quantum Espresso pw.x input files and using the info.

    Members:
    
    * ``namelists``:
        A nested dictionary of the namelists and their key-value
        pairs. The namelists will always be upper-case keys, while the parameter
        keys will always be lower-case.

        For example::

            {"CONTROL": {"calculation": "bands",
                         "prefix": "al",
                         "pseudo_dir": "./pseudo",
                         "outdir": "./out"},
             "ELECTRONS": {"diagonalization": "cg"},
             "SYSTEM": {"nbnd": 8,
                        "ecutwfc": 15.0,
                        "celldm(1)": 7.5,
                        "ibrav": 2,
                        "nat": 1,
                        "ntyp": 1}
            }

    * ``atomic_positions``:
        A dictionary with

            * units: the units of the positions (always lower-case) or None
            * names: list of the atom names (e.g. ``'Si'``, ``'Si0'``,
              ``'Si_0'``)
            * positions: list of the [x, y, z] positions
            * fixed_coords: list of [x, y, z] (bools) of the force modifications
              (**Note:** True <--> Fixed, as defined in the
              ``BasePwCpInputGenerator._if_pos`` method)

        For example::

            {'units': 'bohr',
             'names': ['C', 'O'],
             'positions': [[0.0, 0.0, 0.0],
                           [0.0, 0.0, 2.5]]
             'fixed_coords': [[False, False, False],
                              [True, True, True]]}

    * ``cell_parameters``:
        A dictionary (if CELL_PARAMETERS is present; else: None) with

            * units: the units of the lattice vectors (always lower-case) or
              None
            * cell: 3x3 list with lattice vectors as rows

        For example::

            {'units': 'angstrom',
             'cell': [[16.9, 0.0, 0.0],
                      [-2.6, 8.0, 0.0],
                      [-2.6, -3.5, 7.2]]}

    * ``k_points``:
        A dictionary containing

            * type: the type of kpoints (always lower-case)
            * points: an Nx3 list of the kpoints (will not be present if type =
              'gamma' or type = 'automatic')
            * weights: a 1xN list of the kpoint weights (will not be present if
              type = 'gamma' or type = 'automatic')
            * mesh: a 1x3 list of the number of equally-spaced points in each 
              direction of the Brillouin zone, as in Monkhorst-Pack grids (only
              present if type = 'automatic')
            * offset: a 1x3 list of the grid offsets in each direction of the
              Brillouin zone (only present if type = 'automatic')
              (**Note:** The offset value for each direction will be *one of*
              ``0.0`` [no offset] *or* ``0.5`` [offset by half a grid step].
              This differs from the Quantum Espresso convention, where an offset
              value of ``1`` corresponds to a half-grid-step offset, but adheres
              to the current AiiDa convention.
            

        Examples::

            {'type': 'crystal',
             'points': [[0.125,  0.125,  0.0],
                        [0.125,  0.375,  0.0],
                        [0.375,  0.375,  0.0]],
             'weights': [1.0, 2.0, 1.0]}

            {'type': 'automatic',
             'points': [8, 8, 8],
             'offset': [0.0, 0.5, 0.0]}

            {'type': 'gamma'}

    * ``atomic_species``:
        A dictionary with

            * names: list of the atom names (e.g. 'Si', 'Si0', 'Si_0') (case
              as-is)
            * masses: list of the masses of the atoms in 'names'
            * pseudo_file_names: list of the pseudopotential file names for the
              atoms in 'names' (case as-is)

        Example::

            {'names': ['Li', 'O', 'Al', 'Si'],
             'masses': [6.941,  15.9994, 26.98154, 28.0855],
             'pseudo_file_names': ['Li.pbe-sl-rrkjus_psl.1.0.0.UPF',
                                   'O.pbe-nl-rrkjus_psl.1.0.0.UPF',
                                   'Al.pbe-nl-rrkjus_psl.1.0.0.UPF',
                                   'Si3 28.0855 Si.pbe-nl-rrkjus_psl.1.0.0.UPF']

    """

    def __init__(self, pwinput):
        """
        Parse inputs's namelist and cards to create attributes of the info.

        :param pwinput:
            Any one of the following

                * A string of the (existing) absolute path to the pwinput file.
                * A single string containing the pwinput file's text.
                * A list of strings, with the lines of the file as the elements.
                * A file object. (It will be opened, if it isn't already.)

        :raises IOError: if ``pwinput`` is a file and there is a problem reading
            the file.
        :raises TypeError: if ``pwinput`` is a list containing any non-string
            element(s).
        :raises aiida.common.exceptions.ParsingError: if there are issues
            parsing the pwinput.
        """
        # Get the text of the pwinput file as a single string.
        # File.
        if isinstance(pwinput, file):
            try:
                self.input_txt = pwinput.read()
            except IOError:
                raise IOError(
                    'Unable to open the provided pwinput, {}'
                    ''.format(file.name)
                )
        # List.
        elif isinstance(pwinput, list):
            if all((issubclass(type(s), basestring) for s in pwinput)):
                self.input_txt = ''.join(pwinput)
            else:
                raise TypeError(
                    'You provided a list to parse, but some elements were not '
                    'strings. Each element should be a string containing a line'
                    'of the pwinput file.')
        # Path or string of the text.
        elif issubclass(type(pwinput), basestring):
            if os.path.isfile(pwinput):
                if os.path.exists(pwinput) and os.path.isabs(pwinput):
                    self.input_txt = open(pwinput).read()
                else:
                    raise IOError(
                        'Please provide the absolute path to an existing '
                        'pwinput file.'
                    )
            else:
                self.input_txt = pwinput

        # Check that pwinput is not empty.
        if len(self.input_txt.strip()) == 0:
            raise ParsingError('The pwinput provided was empty!')



    def get_structuredata(self):
        """
        Return a StructureData object based on the data in the input file.
        
        This uses all of the data in the input file to do the necessary unit 
        conversion, ect. and then creates an AiiDa StructureData object.
    
        All of the names corresponding of the Kind objects composing the 
        StructureData object will match those found in the ATOMIC_SPECIES 
        block, so the pseudopotentials can be linked to the calculation using 
        the kind.name for each specific type of atom (in the event that you 
        wish to use different pseudo's for two or more of the same atom).
    
        :return: StructureData object of the structure in the input file
        :rtype: aiida.orm.data.structure.StructureData
        :raises aiida.common.exceptions.ParsingError: if there are issues
            parsing the input.
        """
        return get_structuredata_from_qeinput(
                text=self.input_txt, namelists=self.namelists,
                atomic_positions=self.atomic_positions,
                atomic_species=self.atomic_species,
                cell_parameters=self.cell_parameters
            )


def str2val(valstr):
    """
    Return a python value by converting valstr according to f90 syntax.

    :param valstr: String representation of the variable to be converted.
                   (e.g. '.true.')
    :type valstr: str
    :return: A python variable corresponding to valstr.
    :rtype: bool or float or int or str
    :raises: ValueError: if a suitable conversion of ``valstr`` cannot be found.
    """
    # Define regular expression for matching floats.
    float_re = re.compile(r"""
        [-+]?                 # optional sign
        (?:                   # either
         \d*[.]\d+            # 10.53 or .53
         |                    # or
         \d+[.]\d* )          # 10.53 or 10.
        (?:[dEeE][-+]?[0-9]+)?  # optional exponent
        """, re.X)
    # Strip any white space characters before analyzing.
    valstr = valstr.strip()
    # Define a tuple of regular expressions to match and their corresponding
    # conversion functions.
    re_fn_tuple = (
        (re.compile(r"[.](true|t)[.]", re.I), lambda s: True),
        (re.compile(r"[.](false|f)[.]", re.I), lambda s: False),
        (float_re, lambda s: float(s.replace('d', 'e').replace('D', 'E'))),
        (re.compile(r"[-+]?\d+$"), lambda s: int(s)),
        (re.compile(r"""['"].+['"]"""), lambda s: str(s.strip("\'\"")))
    )
    # Convert valstr to a value.
    val = None
    for regex, conversion_fn in re_fn_tuple:
        # If valstr matches the regular expression, convert it with
        # conversion_fn.
        if regex.match(valstr):
            try:
                val = conversion_fn(valstr)
            except ValueError as error:
                print 'Error converting {} to a value'.format(repr(valstr))
                raise error
    if val is None:
        raise ValueError('Unable to convert {} to a python variable.\n'
                         'NOTE: Support for algebraic expressions is not yet '
                         'implemented.'.format(repr(valstr)))
    else:
        return val


def parse_namelists(txt):
    """
    Parse txt to extract a dictionary of the namelist info.
    
    :param txt: A single string containing the QE input text to be parsed.
    :type txt: str

    :returns:
        A nested dictionary of the namelists and their key-value pairs. The
        namelists will always be upper-case keys, while the parameter keys will
        always be lower-case.

        For example::

            {"CONTROL": {"calculation": "bands",
                         "prefix": "al",
                         "pseudo_dir": "./pseudo",
                         "outdir": "./out"},
             "ELECTRONS": {"diagonalization": "cg"},
             "SYSTEM": {"nbnd": 8,
                        "ecutwfc": 15.0,
                        "celldm(1)": 7.5,
                        "ibrav": 2,
                        "nat": 1,
                        "ntyp": 1}
            }

    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    # TODO: Incorporate support for algebraic expressions?
    # Define the re to match a namelist and extract the info from it.
    namelist_re = re.compile(r"""
        ^ [ \t]* &(\S+) [ \t]* $\n  # match line w/ nmlst tag; save nmlst name
        (
         [\S\s]*?                # match any line non-greedily
        )                        # save the group of text between nmlst
        ^ [ \t]* / [ \t]* $\n    # match line w/ "/" as only non-whitespace char
        """, re.M | re.X)
    # Define the re to match and extract all of the key = val pairs inside
    # a block of namelist text.
    key_value_re = re.compile(r"""
        [ \t]* (\S+?) [ \t]*  # match and store key
        =               # equals sign separates key and value
        [ \t]* (\S+?) [ \t]*  # match and store value
        [\n,]           # return or comma separates "key = value" pairs
        """, re.M | re.X)
    # Scan through the namelists...
    params_dict = {}
    for nmlst, blockstr in namelist_re.findall(txt):
        # ...extract the key value pairs, storing them each in nmlst_dict,...
        nmlst_dict = {}
        for key, valstr in key_value_re.findall(blockstr):
            nmlst_dict[key.lower()] = str2val(valstr)
        # ...and, store nmlst_dict as a value in params_dict with the namelist
        # as the key.
        if len(nmlst_dict.keys()) > 0:
            params_dict[nmlst.upper()] = nmlst_dict
    if len(params_dict) == 0:
        raise ParsingError(
            'No data was found while parsing the namelist in the following '
            'text\n' + txt
        )
    return _uppercase_dict(params_dict, "params_dict")


def parse_atomic_positions(txt):
    """
    Return a dictionary containing info from the ATOMIC_POSITIONS card block
    in txt.

    .. note:: If the units are unspecified, they will be returned as None.

    :param txt: A single string containing the QE input text to be parsed.
    :type txt: str

    :returns:
        A dictionary with

            * units: the units of the positions (always lower-case) or None
            * names: list of the atom names (e.g. ``'Si'``, ``'Si0'``,
              ``'Si_0'``)
            * positions: list of the [x, y, z] positions
            * fixed_coords: list of [x, y, z] (bools) of the force modifications
              (**Note:** True <--> Fixed, as defined in the
              ``BasePwCpInputGenerator._if_pos`` method)

        For example::

            {'units': 'bohr',
             'names': ['C', 'O'],
             'positions': [[0.0, 0.0, 0.0],
                           [0.0, 0.0, 2.5]]
             'fixed_coords': [[False, False, False],
                              [True, True, True]]}


    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    def str01_to_bool(s):
        """
        Map strings '0', '1' strings to bools: '0' --> True; '1' --> False.

        While this is opposite to the QE standard, this mapping is what needs to
        be passed to aiida in a 'settings' ParameterData object.
        (See the _if_pos method of BasePwCpInputGenerator)
        """
        if s == '0':
            return True
        elif s == '1':
            return False
        else:
            raise ParsingError(
                'Unable to convert if_pos = "{}" to bool'.format(s)
            )
    
    # Define re for the card block.
    # NOTE: This will match card block lines w/ or w/out force modifications.
    atomic_positions_block_re = re.compile(r"""
        ^ \s* ATOMIC_POSITIONS \s*                      # Atomic positions start with that string
        [{(]? \s* (?P<units>\S+?)? \s* [)}]? \s* $\n    # The units are after the string in optional brackets
        (?P<block>                                  # This is the block of positions
            (
                (
                    \s*                                 # White space in front of the element spec is ok
                    (
                        [A-Za-z]+[A-Za-z0-9]{0,2}       # Element spec
                        (
                            \s+                         # White space in front of the number
                            [-|+]?                      # Plus or minus in front of the number (optional)
                            (
                                (
                                    \d*                 # optional decimal in the beginning .0001 is ok, for example
                                    [\.]                # There has to be a dot followed by
                                    \d+                 # at least one decimal
                                )
                                |                       # OR
                                (
                                    \d+                 # at least one decimal, followed by
                                    [\.]?               # an optional dot ( both 1 and 1. are fine)
                                    \d*                 # And optional number of decimals (1.00001)
                                )                        # followed by optional decimals
                            )
                            ([E|e|d|D][+|-]?\d+)?       # optional exponents E+03, e-05
                        ){3}                            # I expect three float values
                        ((\s+[0-1]){3}\s*)?             # Followed by optional ifpos
                        \s*                             # Followed by optional white space
                        |
                        \#.*                            # If a line is commented out, that is also ok
                        |
                        \!.*                            # Comments also with excl. mark in fortran
                    )
                    |                                   # OR
                    \s*                                 # A line only containing white space
                 )
                [\n]                                    # line break at the end
            )+                                          # A positions block should be one or more lines
        )
        """, re.X | re.M)

    atomic_positions_block_re_ = re.compile(r"""
        ^ [ \t]* ATOMIC_POSITIONS [ \t]*
            [{(]? [ \t]* (?P<units>\S+?)? [ \t]* [)}]? [ \t]* $\n
        (?P<block>
         (?:
          ^ [ \t]*
          (?:
           \S+ [ \t]+ \S+ [ \t]+ \S+ [ \t]+ \S+
           (?:[ \t]+ [{(]? [ \t]* [01] [ \t]+ [01] [ \t]+ [01] [ \t]* [)}]?)?
          )
          [ \t]* $\n?
         )+
        )
        """, RE_FLAGS)
    # Define re for atomic positions without force modifications.

    
    atomic_positions_w_constraints_re = re.compile(r"""
        ^                                       # Linestart
        [ \t]*                                  # Optional white space
        (?P<name>[A-Za-z]+[A-Za-z0-9]{0,2})\s+   # get the symbol, max 3 chars, starting with a char
        (?P<x>                                  # Get x
            [\-|\+]?(\d*[\.]\d+ | \d+[\.]?\d*)
            ([E|e|d|D][+|-]?\d+)?
        )
        [ \t]+
        (?P<y>                                  # Get y
            [\-|\+]?(\d*[\.]\d+ | \d+[\.]?\d*)
            ([E|e|d|D][+|-]?\d+)?
        )
        [ \t]+
        (?P<z>                                  # Get z
            [\-|\+]?(\d*[\.]\d+ | \d+[\.]?\d*)
            ([E|e|d|D][+|-]?\d+)?
        )
        [ \t]*
        (?P<fx>[01]?)                           # Get fx
        [ \t]*
        (?P<fy>[01]?)                           # Get fx
        [ \t]*
        (?P<fz>[01]?)                           # Get fx
        """, re.X | re.M)
    # Find the card block and extract units and the lines of the block.
    match = atomic_positions_block_re.search(txt)
    if not match:
        raise ParsingError(
            'The ATOMIC_POSITIONS card block was not found in\n' + txt
        )
    # Get the units. If they are not found, match.group('units') will be None.
    units = match.group('units')
    if units is not None:
        units = units.lower()
    # Get the string containing the lines of the block.
    if match.group('block') is None:
        raise ParsingError(
            'The ATOMIC_POSITIONS card block was parsed as empty in\n' + txt
        )
    else:
        blockstr = match.group('block')

    # Define a small helper function to convert if_pos strings to bools that
    # correspond to the mapping of BasePwCpInputGenerator._if_pos method.
    
    # Define a small helper function to convert strings of fortran-type floats.
    fortfloat = lambda s: float(s.replace('d', 'e').replace('D', 'E'))
    # Parse the lines of the card block, extracting an atom name, position
    # and fixed coordinates.
    names, positions, fixed_coords = [], [], []
    # First, try using the re for lines without force modifications. Set the
    # default force modification to the default (True) for each atom.
    # PROBLEM this changes the order of the atoms, which is unwanted!
    #~ for match in atomic_positions_re.finditer(blockstr):
        #~ names.append(match.group('name'))
        #~ positions.append(map(fortfloat, match.group('x', 'y', 'z')))
        #~ fixed_coords.append(3 * [False])  # False <--> not fixed (the default)
    # Next, try using the re for lines with force modifications.
    for match in atomic_positions_w_constraints_re.finditer(blockstr):
        positions.append(map(fortfloat, match.group('x', 'y', 'z')))
        fixed_coords_this_pos = [f or '1' for f in match.group('fx', 'fy', 'fz')] # False <--> not fixed (the default)
        fixed_coords.append(map(str01_to_bool, fixed_coords_this_pos)) 
        names.append(match.group('name'))

    # Check that the number of atomic positions parsed is equal to the number of
    # lines in blockstr
    # LK removed this check since lines can be commented out, and that is fine.
    # n_lines = len(blockstr.rstrip().split('\n'))
    #~ if len(names) != n_lines:
        #~ raise ParsingError(
            #~ 'Only {} atomic positions were parsed from the {} lines of the '
            #~ 'ATOMIC_POSITIONS card block:\n{}'.format(len(names), n_lines,
                                                      #~ blockstr)
        #~ )
    info_dict = dict(units=units, names=names, positions=positions,
                     fixed_coords=fixed_coords)
    return info_dict


def parse_cell_parameters(txt):
    """
    Return dict containing info from the CELL_PARAMETERS card block in txt.

    .. note:: This card is only needed if ibrav = 0. Therefore, if the card is
           not present, the function will return None and not raise an error.

    .. note:: If the units are unspecified, they will be returned as None. The
           units interpreted by QE depend on whether or not one of 'celldm(1)'
           or 'a' is set in &SYSTEM.

    :param txt: A single string containing the QE input text to be parsed.

    :returns:
        A dictionary (if CELL_PARAMETERS is present; else: None) with

            * units: the units of the lattice vectors (always lower-case) or
              None
            * cell: 3x3 list with lattice vectors as rows

        For example::

            {'units': 'angstrom',
             'cell': [[16.9, 0.0, 0.0],
                      [-2.6, 8.0, 0.0],
                      [-2.6, -3.5, 7.2]]}

    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    # Define re for the card block.
    cell_parameters_block_re = re.compile(r"""
        ^ [ \t]*
        CELL_PARAMETERS [ \t]*
        [{(]? \s* (?P<units>[a-z]*) \s* [)}]? \s* [\n]
        (?P<block>
        (
            (
                \s*             # White space in front of the element spec is ok
                (
                    # First number
                    (
                        [-|+]?   # Plus or minus in front of the number (optional)
                        (\d*     # optional decimal in the beginning .0001 is ok, for example
                        [\.]     # There has to be a dot followed by
                        \d+)     # at least one decimal
                        |        # OR
                        (\d+     # at least one decimal, followed by
                        [\.]?    # an optional dot
                        \d*)     # followed by optional decimals
                        ([E|e|d|D][+|-]?\d+)?  # optional exponents E+03, e-05, d0, D0
                    
                        (
                            \s+      # White space between numbers
                            [-|+]?   # Plus or minus in front of the number (optional)
                            (\d*     # optional decimal in the beginning .0001 is ok, for example
                            [\.]     # There has to be a dot followed by
                            \d+)     # at least one decimal
                            |        # OR
                            (\d+     # at least one decimal, followed by
                            [\.]?    # an optional dot
                            \d*)     # followed by optional decimals
                            ([E|e|d|D][+|-]?\d+)?  # optional exponents E+03, e-05, d0, D0
                        ){2}         # I expect three float values
                    )
                    |
                    \#
                    |
                    !            # If a line is commented out, that is also ok
                )
                .*               # I do not care what is after the comment or the vector
                |                # OR
                \s*              # A line only containing white space
             )
            [\n]                 # line break at the end
        ){3}                     # I need exactly 3 vectors
    )
    """, RE_FLAGS)
    
    
    cell_vector_regex = re.compile(r"""
        ^                        # Linestart
        [ \t]*                   # Optional white space
        (?P<x>                   # Get x
            [\-|\+]? ( \d*[\.]\d+ | \d+[\.]?\d*)
            ([E|e|d|D][+|-]?\d+)?
        )
        [ \t]+
        (?P<y>                   # Get y
            [\-|\+]? (\d*[\.]\d+ | \d+[\.]?\d*)
            ([E|e|d|D][+|-]?\d+)?
        )
        [ \t]+
        (?P<z>                   # Get z
            [\-|\+]? (\d*[\.]\d+ | \d+[\.]?\d*)
            ([E|e|d|D][+|-]?\d+)?
        )
        """, re.X | re.M) 
    #~ cell_parameters_block_re = re.compile(r"""
        #~ ^ [ \t]* CELL_PARAMETERS [ \t]*
            #~ [{(]? [ \t]* (?P<units>\S+?)? [ \t]* [)}]? [ \t]* $\n
        #~ (?P<block>
         #~ (?:
          #~ ^ [ \t]* \S+ [ \t]+ \S+ [ \t]+ \S+ [ \t]* $\n?
         #~ ){3}
        #~ )
        #~ """, RE_FLAGS)
    # Define re for the info contained in the block.
    #~ atomic_species_re = re.compile(r"""
        #~ ^ [ \t]* (\S+) [ \t]+ (\S+) [ \t]+ (\S+) [ \t]* $\n?
        #~ """, RE_FLAGS)
    # Find the card block and extract units and the lines of the block.
    match = cell_parameters_block_re.search(txt)
    if not match:
        return None
    # Use specified units or None if not specified.
    units = match.group('units')
    if units is not None:
        units = units.lower()
    # Get the string containing the lines of the block.
    if match.group('block') is None:
        raise ParsingError(
            'The CELL_PARAMETER card block was parsed as empty in\n' + txt
        )
    else:
        blockstr = match.group('block')
    # Define a small helper function to convert strings of fortran-type floats.
    fortfloat = lambda s: float(s.replace('d', 'e').replace('D', 'E'))
    # Now, extract the lattice vectors.
    lattice_vectors = []
    for match in cell_vector_regex.finditer(blockstr):
        lattice_vectors.append(map(fortfloat, (match.group('x'),match.group('y'),match.group('z'))))
    info_dict = dict(units=units, cell=lattice_vectors)
    return info_dict


def parse_atomic_species(txt):
    """
    Return a dictionary containing info from the ATOMIC_SPECIES card block
    in txt.

    :param txt: A single string containing the QE input text to be parsed.
    :type txt: str

    :returns:
        A dictionary with

            * names: list of the atom names (e.g. 'Si', 'Si0', 'Si_0') (case
              as-is)
            * masses: list of the masses of the atoms in 'names'
            * pseudo_file_names: list of the pseudopotential file names for the
              atoms in 'names' (case as-is)

        Example::

            {'names': ['Li', 'O', 'Al', 'Si'],
             'masses': [6.941,  15.9994, 26.98154, 28.0855],
             'pseudo_file_names': ['Li.pbe-sl-rrkjus_psl.1.0.0.UPF',
                                   'O.pbe-nl-rrkjus_psl.1.0.0.UPF',
                                   'Al.pbe-nl-rrkjus_psl.1.0.0.UPF',
                                   'Si3 28.0855 Si.pbe-nl-rrkjus_psl.1.0.0.UPF']

    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    # Define re for atomic species card block.
    atomic_species_block_re = re.compile(r"""
        ^ [ \t]* ATOMIC_SPECIES [ \t]* $\n
        (?P<block>
         (?:
          ^ [ \t]* \S+ [ \t]+ \S+ [ \t]+ \S+ [ \t]* $\n?
         )+
        )
        """, RE_FLAGS)
    # Define re for the info contained in the block.
    atomic_species_re = re.compile(r"""
        ^ [ \t]* (?P<name>\S+) [ \t]+ (?P<mass>\S+) [ \t]+ (?P<pseudo>\S+)
            [ \t]* $\n?
        """, RE_FLAGS)
    # Find the card block and extract units and the lines of the block.
    try:
        match = atomic_species_block_re.search(txt)
    except AttributeError:
        raise ParsingError(
            'The ATOMIC_SPECIES card block was not found in\n' + txt
        )
    # Make sure the card block lines were extracted. If they were, store the
    # string of lines as blockstr.
    if match.group('block') is None:
        raise ParsingError(
            'The ATOMIC_POSITIONS card block was parse as empty in\n' + txt
        )
    else:
        blockstr = match.group('block')
    # Define a small helper function to convert strings of fortran-type floats.
    fortfloat = lambda s: float(s.replace('d', 'e').replace('D', 'E'))
    # Now, extract the name, mass, and pseudopotential file name from each line
    # of the card block.
    names, masses, pseudo_fnms = [], [], []
    for match in atomic_species_re.finditer(blockstr):
        names.append(match.group('name'))
        masses.append(fortfloat(match.group('mass')))
        pseudo_fnms.append(match.group('pseudo'))
    info_dict = dict(names=names, masses=masses, pseudo_file_names=pseudo_fnms)
    return info_dict



def get_cell_from_parameters(cell_parameters, system_dict, alat, using_celldm):
    """
    A function to get the cell from cell parameters and SYSTEM card dictionary as read by 
    parse_namelists.
    :param cell_parameters: The parameters as returned by parse_cell_parameters
    :param system_dict: the dictionary for card SYSTEM
    :param alat: The value for alat
    :returns: The cell as a numpy array
    """
    ibrav = system_dict['ibrav']

    valid_ibravs = range(15) + [-5, -9, -12]
    if ibrav not in valid_ibravs:
        raise InputValidationError(
            'I found ibrav = {} in input, \n'
            'but it is not among the valid values\n'
            '{}'.format(ibrav, valid_ibravs))

    if ibrav != 0:
        # Ok, user was not nice and used ibrav > 0 to define cell using
        # either the keys celldm(n) n = 1,2,...,6  (celldm - system)
        # or A,B,C, cosAB, cosAC, cosBC (ABC-system)
        # to define the necessary cell geometry factors
        # NOT both
        # I am only going to this for the important first lattice vector
      
        if alat is None:
            raise Exception('You have to define lattice vector'
                            'celldm(1) or A'
                            )
        # So, depending on what is defined for the first lattice vector,
        # I define the keys that I will look for to find the other
        # geometry definitions
        try:
            # Not all geometry definitions are needed,
            # but some are necessary depending on ibrav
            # and will be matched here:
            if abs(ibrav) > 7:
                if using_celldm:
                    b = alat * system_dict['celldm(2)']
                else:
                    b = system_dict['b']
            if abs(ibrav) > 3 and ibrav not in (-5, 5):
                if using_celldm:
                    c = alat * system_dict['celldm(3)']
                else:
                    c = system_dict['c']
            if ibrav in (5, 12, 13):
                if using_celldm:
                    cosg = system_dict['celldm(4)']
                else:
                    cosg = system_dict['cosab']
                sing = np.sqrt(1. - cosg ** 2)
            if ibrav in (5,):
                # They are the same in trigonal R
                cosa = cosg
                sina = sing
            if ibrav in (-12, 14):
                if using_celldm:
                    cosb = system_dict['celldm(5)']
                else:
                    cosb = system_dict['cosac']
                sinb = np.sqrt(1. - cosb ** 2)
            if ibrav in (14,):
                if using_celldm:
                    cosa = system_dict['celldm(4)']
                else:
                    cosa = system_dict['cosbc']
            if ibrav in (14,):
                if using_celldm:
                    cosg = system_dict['celldm(6)']
                else:
                    cosg = system_dict['cosab']
        except Exception as e:
            raise InputValidationError(
                '\nException {} raised when searching for\n'
                'key {} in qeinput, necessary when ibrav = {}'.format(
                    e, e.message, ibrav
                )
            )
    # Calculating the cell according to ibrav.
    # The comments in each case are taken from
    # http://www.quantum-espresso.org/wp-content/uploads/Doc/INPUT_PW.html#ibrav

    if ibrav == 0:
        # The cell is defined explicitly in a block CELL_PARAMETERS
        # Match the cell block using the regex defined above:
        cell = np.array(cell_parameters['cell'])
        cell_unit = cell_parameters['units']
        # Now, we do the convert the cell to the right units (we want angstrom):
        if cell_unit == 'angstrom':
            pass
        elif cell_unit == 'bohr':
            cell = bohr_to_ang * cell
        elif cell_unit == 'alat':
            if alat is None:
                raise InputValidationError("You have specified units of alat for the cell, \n"
                    "but you have not provided a value for alat")
            cell = alat * cell
        elif cell_unit == '':
            # Now here comes some piece of retardedness in QE:
            # If alat was somehow specified, cell is given in units of alats
            # if alat was not specified, the default is bohr:
            if alat is None:
                cell = bohr_to_ang * cell
            else:
                cell = alat * cell
        else:
            raise InputValidationError("Unknown unit for CELL_PARAMETERS {}".format(cell_unit))


    if ibrav == 1:
        # 1          cubic P (sc)
        # v1 = a(1,0,0),  v2 = a(0,1,0),  v3 = a(0,0,1)
        cell = np.diag([alat, alat, alat])
    elif ibrav == 2:
        #  2          cubic F (fcc)
        #  v1 = (a/2)(-1,0,1),  v2 = (a/2)(0,1,1), v3 = (a/2)(-1,1,0)
        cell = 0.5 * alat * np.array([
            [-1., 0., 1.],
            [0., 1., 1.],
            [-1., 1., 0.],
        ])
    elif ibrav == 3:
        # cubic I (bcc)
        #  v1 = (a/2)(1,1,1),  v2 = (a/2)(-1,1,1),  v3 = (a/2)(-1,-1,1)
        cell = 0.5 * alat * np.array([
            [1., 1., 1.],
            [-1., 1., 1.],
            [-1., -1., 0.],
        ])
    elif ibrav == 4:
        # 4          Hexagonal and Trigonal P        celldm(3)=c/a
        # v1 = a(1,0,0),  v2 = a(-1/2,sqrt(3)/2,0),  v3 = a(0,0,c/a)
        cell = alat * np.array([
            [1., 0., 0.],
            [-0.5, 0.5 * np.sqrt(3.), 0.],
            [0., 0., c / alat]
        ])
    elif ibrav == 5:
        # 5          Trigonal R, 3fold axis c        celldm(4)=cos(alpha)
        # The crystallographic vectors form a three-fold star around
        # the z-axis, the primitive cell is a simple rhombohedron:
        # v1 = a(tx,-ty,tz),   v2 = a(0,2ty,tz),   v3 = a(-tx,-ty,tz)
        # where c=cos(alpha) is the cosine of the angle alpha between
        # any pair of crystallographic vectors, tx, ty, tz are:
        # tx=sqrt((1-c)/2), ty=sqrt((1-c)/6), tz=sqrt((1+2c)/3)
        tx = np.sqrt((1. - cosa) / 2.)
        ty = np.sqrt((1. - cosa) / 6.)
        tz = np.sqrt((1. + 2. * cosa) / 3.)
        cell = alat * np.array([
            [tx, -ty, tz],
            [0., 2 * ty, tz],
            [-tx, -ty, tz]
        ])
    elif ibrav == -5:
        # -5          Trigonal R, 3fold axis <111>    celldm(4)=cos(alpha)
        # The crystallographic vectors form a three-fold star around
        # <111>. Defining a' = a/sqrt(3) :
        # v1 = a' (u,v,v),   v2 = a' (v,u,v),   v3 = a' (v,v,u)
        # where u and v are defined as
        # u = tz - 2*sqrt(2)*ty,  v = tz + sqrt(2)*ty
        # and tx, ty, tz as for case ibrav=5
        # Note: if you prefer x,y,z as axis in the cubic limit,
        # set  u = tz + 2*sqrt(2)*ty,  v = tz - sqrt(2)*ty
        # See also the note in flib/latgen.f90
        tx = np.sqrt((1. - c) / 2.)
        ty = np.sqrt((1. - c) / 6.)
        tz = np.sqrt((1. + 2. * c) / 3.)
        u = tz - 2. * np.sqrt(2.) * ty
        v = tz + np.sqrt(2.) * ty
        cell = a / np.sqrt(3.) * np.array([
            [u, v, v],
            [v, u, v],
            [v, v, u]
        ])
    elif ibrav == 6:
        # 6          Tetragonal P (st)               celldm(3)=c/a
        # v1 = a(1,0,0),  v2 = a(0,1,0),  v3 = a(0,0,c/a)
        cell = alat * np.array([
            [1., 0., 0.],
            [0., 1., 0.],
            [0., 0., c / alat]
        ])
    elif ibrav == 7:
        # 7          Tetragonal I (bct)              celldm(3)=c/a
        # v1=(a/2)(1,-1,c/a),  v2=(a/2)(1,1,c/a),  v3=(a/2)(-1,-1,c/a)
        cell = 0.5 * alat * np.array([
            [1., -1., c / alat],
            [1., 1., c / alat],
            [-1., -1., c / alat]
        ])
    elif ibrav == 8:
        # 8  Orthorhombic P       celldm(2)=b/a
        #                         celldm(3)=c/a
        #  v1 = (a,0,0),  v2 = (0,b,0), v3 = (0,0,c)
        cell = np.diag([alat, b, c])
    elif ibrav == 9:
        #   9   Orthorhombic base-centered(bco) celldm(2)=b/a
        #                                         celldm(3)=c/a
        #  v1 = (a/2, b/2,0),  v2 = (-a/2,b/2,0),  v3 = (0,0,c)
        cell = np.array([
            [0.5 * alat, 0.5 * b, 0.],
            [-0.5 * alat, 0.5 * b, 0.],
            [0., 0., c]
        ])
    elif ibrav == -9:
        # -9          as 9, alternate description
        #  v1 = (a/2,-b/2,0),  v2 = (a/2,-b/2,0),  v3 = (0,0,c)
        cell = np.array([
            [0.5 * alat, 0.5 * b, 0.],
            [0.5 * alat, -0.5 * b, 0.],
            [0., 0., c]
        ])
    elif ibrav == 10:
        # 10          Orthorhombic face-centered      celldm(2)=b/a
        #                                         celldm(3)=c/a
        #  v1 = (a/2,0,c/2),  v2 = (a/2,b/2,0),  v3 = (0,b/2,c/2)
        cell = np.array([
            [0.5 * alat, 0., 0.5 * c],
            [0.5 * alat, 0.5 * b, 0.],
            [0., 0.5 * b, 0.5 * c]
        ])
    elif ibrav == 11:
        # 11          Orthorhombic body-centered      celldm(2)=b/a
        #                                        celldm(3)=c/a
        #  v1=(a/2,b/2,c/2),  v2=(-a/2,b/2,c/2),  v3=(-a/2,-b/2,c/2)
        cell = np.array([
            [0.5 * alat, 0.5 * b, 0.5 * c],
            [-0.5 * alat, 0.5 * b, 0.5 * c],
            [-0.5 * alat, -0.5 * b, 0.5 * c]
        ])
    elif ibrav == 12:
        # 12      Monoclinic P, unique axis c     celldm(2)=b/a
        #                                         celldm(3)=c/a,
        #                                         celldm(4)=cos(ab)
        #  v1=(a,0,0), v2=(b*cos(gamma),b*sin(gamma),0),  v3 = (0,0,c)
        #  where gamma is the angle between axis a and b.
        cell = np.array([
            [alat, 0., 0.],
            [b * cosg, b * sing, 0.],
            [0., 0., c]
        ])
    elif ibrav == -12:
        # -12          Monoclinic P, unique axis b     celldm(2)=b/a
        #                                         celldm(3)=c/a,
        #                                         celldm(5)=cos(ac)
        #  v1 = (a,0,0), v2 = (0,b,0), v3 = (c*cos(beta),0,c*sin(beta))
        #  where beta is the angle between axis a and c
        cell = np.array([
            [alat, 0., 0.],
            [0., b, 0.],
            [c * cosb, 0., c * sinb]
        ])
    elif ibrav == 13:
        # 13          Monoclinic base-centered        celldm(2)=b/a
        #                                          celldm(3)=c/a,
        #                                          celldm(4)=cos(ab)
        #  v1 = (  a/2,         0,                -c/2),
        #  v2 = (b*cos(gamma), b*sin(gamma), 0),
        #  v3 = (  a/2,         0,                  c/2),
        #  where gamma is the angle between axis a and b
        cell = np.array([
            [0.5 * alat, 0., -0.5 * c],
            [b * cosg, b * sing, 0.],
            [0.5 * a, 0., 0.5 * c]
        ])
    elif ibrav == 14:
        #  14       Triclinic                     celldm(2)= b/a,
        #                                         celldm(3)= c/a,
        #                                         celldm(4)= cos(bc),
        #                                         celldm(5)= cos(ac),
        #                                         celldm(6)= cos(ab)
        #  v1 = (a, 0, 0),
        #  v2 = (b*cos(gamma), b*sin(gamma), 0)
        #  v3 = (c*cos(beta),  c*(cos(alpha)-cos(beta)cos(gamma))/sin(gamma),
        #       c*sqrt( 1 + 2*cos(alpha)cos(beta)cos(gamma)
        #                 - cos(alpha)^2-cos(beta)^2-cos(gamma)^2 )/sin(gamma) )
        # where alpha is the angle between axis b and c
        #     beta is the angle between axis a and c
        #    gamma is the angle between axis a and b
        cell = np.array([
            [alat, 0., 0.],
            [b * cosg, b * sing, 0.],
            [
                c * cosb,
                c * (cosa - cosb * cosg) / sing,
                c * np.sqrt(
                    1. + 2. * cosa * cosb * cosg - cosa ** 2 - cosb ** 2 - cosg ** 2) / sing
            ]
        ])

    return cell

def get_structuredata_from_qeinput(
        filepath=None, text=None, namelists=None,
        atomic_species=None, atomic_positions=None, cell_parameters=None
        
    ):
    """
    Function that receives either
    :param filepath: the filepath storing **or**
    :param text: the string of a standard QE-input file.
    An instance of :func:`StructureData` is initialized with kinds, positions and cell
    as defined in the input file.
    This function can deal with ibrav being set different from 0 and the cell being defined
    with celldm(n) or A,B,C, cosAB etc.
    """
    from aiida.orm.data.structure import StructureData, Kind, Site
    #~ from aiida.common.utils import get_fortfloat

    valid_elements_regex = re.compile("""
        (?P<ele>
H  | He |
Li | Be | B  | C  | N  | O  | F  | Ne |
Na | Mg | Al | Si | P  | S  | Cl | Ar |
K  | Ca | Sc | Ti | V  | Cr | Mn | Fe | Co | Ni | Cu | Zn | Ga | Ge | As | Se | Br | Kr |
Rb | Sr | Y  | Zr | Nb | Mo | Tc | Ru | Rh | Pd | Ag | Cd | In | Sn | Sb | Te | I  | Xe |
Cs | Ba | Hf | Ta | W  | Re | Os | Ir | Pt | Au | Hg | Tl | Pb | Bi | Po | At | Rn |
Fr | Ra | Rf | Db | Sg | Bh | Hs | Mt |

La | Ce | Pr | Nd | Pm | Sm | Eu | Gd | Tb | Dy | Ho | Er | Tm | Yb | Lu | # Lanthanides
Ac | Th | Pa | U  | Np | Pu | Am | Cm | Bk | Cf | Es | Fm | Md | No | Lr | # Actinides
        )
        [^a-z]  # Any specification of an element is followed by some number
                # or capital letter or special character.
    """, re.X | re.I)
    # I need either a valid filepath or the text of the qeinput file:
    if filepath:
        with open(filepath) as f:
            txt = f.read()
    elif text:
        txt = text
    else:
        raise InputValidationError(
            'Provide either a filepath or text to be parsed'
        )

    if namelists is None:
        namelists = parse_namelists(text)
    if atomic_species is None:
        atomic_species = parse_atomic_species(txt)
    if cell_parameters is None:
        cell_parameters = parse_cell_parameters(txt)
    if atomic_positions is None:
        atomic_positions = parse_atomic_positions(txt)
    

    # First, I'm trying to figure out whether alat was specified:
    system_dict = namelists['SYSTEM']

    if 'a' in system_dict and 'celldm(1)' in system_dict:
        # The user should define exclusively in celldm or ABC-system
        raise InputValidationError(
                'Both a and celldm(1) specified'
            )        
    elif 'a' in system_dict:
        alat = system_dict['a']
        using_celldm = False
    elif 'celldm(1)' in system_dict:
        alat = bohr_to_ang * system_dict['celldm(1)']
        using_celldm = True
    else:
        alat = None
        using_celldm=None

    cell = get_cell_from_parameters(cell_parameters, system_dict, alat, using_celldm)   

    # instance and set the cell
    structuredata = StructureData()
    structuredata._set_attr('cell', cell.tolist())

    #################  KINDS ##########################


    
    for mass, name, pseudo in zip(
            atomic_species['masses'],
            atomic_species['names'],
            atomic_species['pseudo_file_names']
        ):
        try:
            symbols = valid_elements_regex.search(pseudo).group('ele').capitalize()
        except Exception as e:
            raise InputValidationError(
                'I could not read an element name in {}'.format(match.group(0))
            )
        structuredata.append_kind(Kind(
                name=name,
                symbols=symbols,
                mass=mass,
            ))

    ################## POSITIONS #######################
    positions_units = atomic_positions['units']
    positions = np.array(atomic_positions['positions'])

    if positions_units is None:
        raise InputValidationError("There is no unit for positions\n"
                "This is deprecated behavior for QE.\n"
                "In addition the default values by CP and PW differ (bohr and alat)"
            )
    elif positions_units == 'angstrom':
        pass
    elif positions_units == 'bohr':
        positions = bohr_to_ang * positions
    elif positions_units == 'crystal':
        positions = np.dot(positions, cell)
    elif positions_units == 'alat':
        positions = np.linalg.norm(cell[0]) * positions
    elif positions_units == 'crystal_sg':
        raise NotImplementedError('crystal_sg is not implemented')
    else:
        valid_positions_units = ('alat', 'bohr', 'angstrom', 'crystal', 'crystal_sg')
        raise InputValidationError(
            '\nFound atom unit {}, which is not\n'
            'among the valid units: {}'.format(
                positions_units, ', '.join(valid_positions_units)
            )
        )
    ######### DEFINE SITES ######################

    positions = positions.tolist()
    [
        structuredata.append_site(Site(kind_name=sym, position=pos,))
        for sym, pos in zip(atomic_positions['names'], positions)]
    return structuredata
