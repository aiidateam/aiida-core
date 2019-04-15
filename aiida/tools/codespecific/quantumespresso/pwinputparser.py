# -*- coding: utf-8 -*-
"""
Tools for parsing QE PW input files and creating AiiDa Node objects based on
them.

TODO: Parse CONSTRAINTS, OCCUPATIONS, ATOMIC_FORCES once they are implemented
      in AiiDa
"""
import re
import os
import numpy as np
from aiida.parsers.plugins.quantumespresso.constants import bohr_to_ang
from aiida.common.exceptions import ParsingError
from aiida.orm.data.structure import StructureData, _valid_symbols
from aiida.orm.data.array.kpoints import KpointsData

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."

RE_FLAGS = re.M | re.X | re.I


class PwInputFile(object):
    """
    Class used for parsing Quantum Espresso pw.x input files and using the info.

    :ivar namelists:
        A nested dictionary of the namelists and their key-value
        pairs. The namelists will always be upper-case keys, while the parameter
        keys will always be lower-case.

        For example: ::

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

    :ivar atomic_positions:
        A dictionary with

            * units: the units of the positions (always lower-case) or None
            * names: list of the atom names (e.g. ``'Si'``, ``'Si0'``,
              ``'Si_0'``)
            * positions: list of the [x, y, z] positions
            * fixed_coords: list of [x, y, z] (bools) of the force modifications
              (**Note:** True <--> Fixed, as defined in the
              ``BasePwCpInputGenerator._if_pos`` method)

        For example: ::

            {'units': 'bohr',
             'names': ['C', 'O'],
             'positions': [[0.0, 0.0, 0.0],
                           [0.0, 0.0, 2.5]]
             'fixed_coords': [[False, False, False],
                              [True, True, True]]}

    :ivar cell_parameters:
        A dictionary (if CELL_PARAMETERS is present; else: None) with

            * units: the units of the lattice vectors (always lower-case) or
              None
            * cell: 3x3 list with lattice vectors as rows

        For example: ::

            {'units': 'angstrom',
             'cell': [[16.9, 0.0, 0.0],
                      [-2.6, 8.0, 0.0],
                      [-2.6, -3.5, 7.2]]}

    :ivar k_points:
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
            

        Examples: ::

            {'type': 'crystal',
             'points': [[0.125,  0.125,  0.0],
                        [0.125,  0.375,  0.0],
                        [0.375,  0.375,  0.0]],
             'weights': [1.0, 2.0, 1.0]}

            {'type': 'automatic',
             'points': [8, 8, 8],
             'offset': [0.0, 0.5, 0.0]}

            {'type': 'gamma'}

    :ivar atomic_species:
        A dictionary with

            * names: list of the atom names (e.g. 'Si', 'Si0', 'Si_0') (case
              as-is)
            * masses: list of the masses of the atoms in 'names'
            * pseudo_file_names: list of the pseudopotential file names for the
              atoms in 'names' (case as-is)

        Example: ::

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

        # Parse the namelists.
        self.namelists = parse_namelists(self.input_txt)
        # Parse the ATOMIC_POSITIONS card.
        self.atomic_positions = parse_atomic_positions(self.input_txt)
        # Parse the CELL_PARAMETERS card.
        self.cell_parameters = parse_cell_parameters(self.input_txt)
        # Parse the K_POINTS card.
        self.k_points = parse_k_points(self.input_txt)
        # Parse the ATOMIC_SPECIES card.
        self.atomic_species = parse_atomic_species(self.input_txt)

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
        # CELL_PARAMETERS are present.
        if self.cell_parameters is None:
            raise ParsingError(
                'CELL_PARAMETERS not found while parsing the input file. This '
                'card is needed for AiiDa.'
            )

        # Figure out the factor needed to convert the lattice vectors
        # to Angstroms.
        # TODO: ***ASK GEORGE IF I SHOULD MULTIPLY OR DIVIDE BY ALAT***
        cell_units = self.cell_parameters.get('units')
        if (cell_units == 'alat') or (cell_units is None):
            # Try to determine the value of alat from the namelist.
            celldm1 = self.namelists['SYSTEM'].get('celldm(1)')
            a = self.namelists['SYSTEM'].get('a')
            # Only one of 'celldm(1)' or 'a' can be set.
            if (celldm1 is not None) and (a is not None):
                raise ParsingError(
                    "Both 'celldm(1)' and 'a' were set in the input file."
                )
            elif celldm1 is not None:
                cell_conv_factor = celldm1 * bohr_to_ang  # celldm(1) in Bohr
            elif a is not None:
                cell_conv_factor = a  # a is in Angstroms
            else:
                if cell_units is None:
                    cell_conv_factor = bohr_to_ang  # QE assumes Bohr
                else:
                    raise ParsingError(
                        "Unable to determine the units of the lattice vectors."
                    )
        elif cell_units == 'bohr':
            cell_conv_factor = bohr_to_ang
        elif cell_units == 'angstrom':
            cell_conv_factor = 1.0
        else:
            raise ParsingError(
                "Unable to determine the units of the lattice vectors."
            )

        # Get the lattice vectors and convert them to units of Angstroms.
        cell = np.array(self.cell_parameters['cell']) * cell_conv_factor

        # Get the positions and convert them to [x, y, z] Angstrom vectors.
        pos_units = self.atomic_positions['units']
        positions = np.array(self.atomic_positions['positions'])
        if pos_units in (None, 'alat'):  # QE assumes alat
            alat = np.linalg.norm(cell[0])  # Cell in Ang, so alat in Ang
            positions *= alat
        elif pos_units == 'bohr':
            positions = positions * bohr_to_ang
        elif pos_units == 'angstrom':
            pass
        elif pos_units == 'crystal':
            positions = np.dot(positions, cell)  # rotate into [x y z] basis
        else:
            raise ParsingError(
                'Unable to determine to convert positions to [x y z] Angstrom.'
            )

        # Get the atom names corresponding to positions.
        names = self.atomic_positions['names']

        # Create a dictionary that maps an atom name to it's mass.
        mass_dict = dict(zip(self.atomic_species['names'],
                             self.atomic_species['masses']))

        # Use the names to figure out the atomic symbols.
        symbols = []
        for name in names:
            candiates = [s for s in _valid_symbols
                         if name.lower().startswith(s.lower())]
            if len(candiates) == 0:
                raise ParsingError(
                    'Unable to figure out the element represented by the '
                    'label, {}, in the input file.'.format(name))
            # Choose the longest match, since, for example, S and Si match Si.
            symbols.append(max(candiates, key=lambda x: len(x)))

        # Now that we have the names and their corresponding symbol and mass, as
        # well as the positions and cell in units of Angstroms, we create the
        # StructureData object.
        structuredata = StructureData(cell=cell)
        for name, symbol, position in zip(names, symbols, positions):
            mass = mass_dict[name]
            structuredata.append_atom(name=name, symbols=symbol,
                                      position=position, mass=mass)
        return structuredata

    def get_kpointsdata(self):
        """
        Return a KpointsData object based on the data in the input file.

        This uses all of the data in the input file to do the necessary unit
        conversion, ect. and then creates an AiiDa KpointsData object.


        **Note:** If the calculation uses only the gamma k-point (`if
        self.k_points['type'] == 'gamma'`), it is necessary to also attach a
        settings node to the calculation with `gamma_only = True`.

        :return: KpointsData object of the kpoints in the input file
        :rtype: aiida.orm.data.array.kpoints.KpointsData
        :raises aiida.common.exceptions.NotImplimentedError: if the kpoints are
            in a format not yet supported.
        """
        # Initialize the KpointsData node
        kpointsdata = KpointsData()
        # Get the structure using this class's method.
        structuredata = self.get_structuredata()
        # Set the structure information of the kpoints node.
        kpointsdata.set_cell_from_structure(structuredata)

        # Set the kpoints and weights, doing any necessary units conversion.
        if self.k_points['type'] == 'crystal':  # relative to recip latt vecs
            kpointsdata.set_kpoints(self.k_points['points'],
                                    weights=self.k_points['weights'])
        elif self.k_points['type'] == 'tpiba':  # cartesian; units of 2*pi/alat
            alat = np.linalg.norm(structuredata.cell[0])  # alat in Angstrom
            kpointsdata.set_kpoints(
                np.array(self.k_points['points']) * (2. * np.pi / alat),
                weights=self.k_points['weights'],
                cartesian=True
            )
        elif self.k_points['type'] == 'automatic':
            kpointsdata.set_kpoints_mesh(self.k_points['points'],
                                         offset=self.k_points['offset'])
        elif self.k_points['type'] == 'gamma':
            kpointsdata.set_kpoints_mesh([1, 1, 1])
        else:
            raise NotImplementedError(
                'Support for creating KpointsData from input units of {} is'
                'not yet implemented'.format(self.k_points['type'])
            )

        return kpointsdata


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

        For example: ::

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

    :rtype: dictionary
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
    return params_dict


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

        For example: ::

            {'units': 'bohr',
             'names': ['C', 'O'],
             'positions': [[0.0, 0.0, 0.0],
                           [0.0, 0.0, 2.5]]
             'fixed_coords': [[False, False, False],
                              [True, True, True]]}


    :rtype: dictionary
    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    # Define re for the card block.
    # NOTE: This will match card block lines w/ or w/out force modifications.
    atomic_positions_block_re = re.compile(r"""
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
    atomic_positions_re = re.compile(r"""
        ^ [ \t]*
        (?P<name>\S+) [ \t]+ (?P<x>\S+) [ \t]+ (?P<y>\S+) [ \t]+ (?P<z>\S+)
            [ \t]* $\n?
        """, RE_FLAGS)
    # Define re for atomic positions with force modifications.
    atomic_positions_constraints_re = re.compile(r"""
        ^ [ \t]*
        (?P<name>\S+) [ \t]+ (?P<x>\S+) [ \t]+ (?P<y>\S+) [ \t]+ (?P<z>\S+)
            [ \t]+ [{(]? [ \t]* (?P<if_pos1>[01]) [ \t]+ (?P<if_pos2>[01])
            [ \t]+ (?P<if_pos3>[01]) [ \t]* [)}]?
        [ \t]* $\n?
        """, RE_FLAGS)
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
                'Unable to convert if_pos = {} to bool'.format(s)
            )

    # Define a small helper function to convert strings of fortran-type floats.
    fortfloat = lambda s: float(s.replace('d', 'e').replace('D', 'E'))
    # Parse the lines of the card block, extracting an atom name, position
    # and fixed coordinates.
    names, positions, fixed_coords = [], [], []
    # First, try using the re for lines without force modifications. Set the
    # default force modification to the default (True) for each atom.
    for match in atomic_positions_re.finditer(blockstr):
        names.append(match.group('name'))
        positions.append(map(fortfloat, match.group('x', 'y', 'z')))
        fixed_coords.append(3 * [False])  # False <--> not fixed (the default)
    # Next, try using the re for lines with force modifications.
    for match in atomic_positions_constraints_re.finditer(blockstr):
        names.append(match.group('name'))
        positions.append(map(fortfloat, match.group('x', 'y', 'z')))
        if_pos123 = match.group('if_pos1', 'if_pos2', 'if_pos3')
        fixed_coords.append(map(str01_to_bool, if_pos123))
    # Check that the number of atomic positions parsed is equal to the number of
    # lines in blockstr
    n_lines = len(blockstr.rstrip().split('\n'))
    if len(names) != n_lines:
        raise ParsingError(
            'Only {} atomic positions were parsed from the {} lines of the '
            'ATOMIC_POSITIONS card block:\n{}'.format(len(names), n_lines,
                                                      blockstr)
        )
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
    :type txt: str

    :returns:
        A dictionary (if CELL_PARAMETERS is present; else: None) with

            * units: the units of the lattice vectors (always lower-case) or
              None
            * cell: 3x3 list with lattice vectors as rows

        For example: ::

            {'units': 'angstrom',
             'cell': [[16.9, 0.0, 0.0],
                      [-2.6, 8.0, 0.0],
                      [-2.6, -3.5, 7.2]]}

    :rtype: dict or None
    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    # Define re for the card block.
    cell_parameters_block_re = re.compile(r"""
        ^ [ \t]* CELL_PARAMETERS [ \t]*
            [{(]? [ \t]* (?P<units>\S+?)? [ \t]* [)}]? [ \t]* $\n
        (?P<block>
         (?:
          ^ [ \t]* \S+ [ \t]+ \S+ [ \t]+ \S+ [ \t]* $\n?
         ){3}
        )
        """, RE_FLAGS)
    # Define re for the info contained in the block.
    atomic_species_re = re.compile(r"""
        ^ [ \t]* (\S+) [ \t]+ (\S+) [ \t]+ (\S+) [ \t]* $\n?
        """, RE_FLAGS)
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
    for match in atomic_species_re.finditer(blockstr):
        lattice_vectors.append(map(fortfloat, match.groups()))
    info_dict = dict(units=units, cell=lattice_vectors)
    return info_dict


def parse_k_points(txt):
    """
    Return a dictionary containing info from the K_POINTS card block in txt.

    .. note:: If the type of kpoints (where type = x in the card header,
           "K_POINTS x") is not present, type will be returned as 'tpiba', the
           QE default.

    :param txt: A single string containing the QE input text to be parsed.
    :type txt: str

    :returns:
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


        Examples: ::

            {'type': 'crystal',
             'points': [[0.125,  0.125,  0.0],
                        [0.125,  0.375,  0.0],
                        [0.375,  0.375,  0.0]],
             'weights': [1.0, 2.0, 1.0]}

            {'type': 'automatic',
             'points': [8, 8, 8],
             'offset': [0.0, 0.5, 0.0]}

            {'type': 'gamma'}

    :rtype: dictionary
    :raises aiida.common.exceptions.ParsingError: if there are issues
        parsing the input.
    """
    # Define re for the special-type card block.
    k_points_special_block_re = re.compile(r"""
        ^ [ \t]* K_POINTS [ \t]*
            [{(]? [ \t]* (?P<type>\S+?)? [ \t]* [)}]? [ \t]* $\n
        ^ [ \t]* \S+ [ \t]* $\n  # nks
        (?P<block>
         (?:
          ^ [ \t]* \S+ [ \t]+ \S+ [ \t]+ \S+ [ \t]+ \S+ [ \t]* $\n?
         )+
        )
        """, RE_FLAGS)
    # Define re for the info contained in the special-type block.
    k_points_special_re = re.compile(r"""
    ^ [ \t]* (\S+) [ \t]+ (\S+) [ \t]+ (\S+) [ \t]+ (\S+) [ \t]* $\n?
    """, RE_FLAGS)
    # Define re for the automatic-type card block and its line of info.
    k_points_automatic_block_re = re.compile(r"""
        ^ [ \t]* K_POINTS [ \t]* [{(]? [ \t]* automatic [ \t]* [)}]? [ \t]* $\n
        ^ [ \t]* (\S+) [ \t]+ (\S+) [ \t]+ (\S+) [ \t]+ (\S+) [ \t]+ (\S+)
            [ \t]+ (\S+) [ \t]* $\n?
        """, RE_FLAGS)
    # Define re for the gamma-type card block. (There is no block info.)
    k_points_gamma_block_re = re.compile(r"""
        ^ [ \t]* K_POINTS [ \t]* [{(]? [ \t]* gamma [ \t]* [)}]? [ \t]* $\n
        """, RE_FLAGS)
    # Try finding the card block using all three types.
    info_dict = {}
    match = k_points_special_block_re.search(txt)
    if match:
        if match.group('type') is not None:
            info_dict['type'] = match.group('type').lower()
        else:
            info_dict['type'] = 'tpiba'
        blockstr = match.group('block')
        points = []
        weights = []
        for match in k_points_special_re.finditer(blockstr):
            points.append(map(float, match.group(1, 2, 3)))
            weights.append(float(match.group(4)))
        info_dict['points'] = points
        info_dict['weights'] = weights
    else:
        match = k_points_automatic_block_re.search(txt)
        if match:
            info_dict['type'] = 'automatic'
            info_dict['points'] = map(int, match.group(1, 2, 3))
            info_dict['offset'] = [0. if x == 0 else 0.5
                                   for x in map(int, match.group(4, 5, 6))]
        else:
            match = k_points_gamma_block_re.search(txt)
            if match:
                info_dict['type'] = 'gamma'
            else:
                raise ParsingError('K_POINTS card not found in\n' + txt)
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

        Example: ::

            {'names': ['Li', 'O', 'Al', 'Si'],
             'masses': [6.941,  15.9994, 26.98154, 28.0855],
             'pseudo_file_names': ['Li.pbe-sl-rrkjus_psl.1.0.0.UPF',
                                   'O.pbe-nl-rrkjus_psl.1.0.0.UPF',
                                   'Al.pbe-nl-rrkjus_psl.1.0.0.UPF',
                                   'Si3 28.0855 Si.pbe-nl-rrkjus_psl.1.0.0.UPF']

    :rtype: dictionary
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
