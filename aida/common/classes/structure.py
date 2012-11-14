"""
This module defines the classes for structures and all related functions to
operate on them.
"""
elements = {
    1: {   'mass': 1.0079400000000001, 'name': 'Hydrogen', 'symbol': 'H'},
    2: {   'mass': 4.0026000000000002, 'name': 'Helium', 'symbol': 'He'},
    3: {   'mass': 6.9409999999999998, 'name': 'Lithium', 'symbol': 'Li'},
    4: {   'mass': 9.0121800000000007, 'name': 'Beryllium', 'symbol': 'Be'},
    5: {   'mass': 10.811, 'name': 'Boron', 'symbol': 'B'},
    6: {   'mass': 12.010999999999999, 'name': 'Carbon', 'symbol': 'C'},
    7: {   'mass': 14.0067, 'name': 'Nitrogen', 'symbol': 'N'},
    8: {   'mass': 15.9994, 'name': 'Oxygen', 'symbol': 'O'},
    9: {   'mass': 18.9984, 'name': 'Fluorine', 'symbol': 'F'},
    10: {   'mass': 20.1797, 'name': 'Neon', 'symbol': 'Ne'},
    11: {   'mass': 22.98977, 'name': 'Sodium', 'symbol': 'Na'},
    12: {   'mass': 24.305, 'name': 'Magnesium', 'symbol': 'Mg'},
    13: {   'mass': 26.981539999999999, 'name': 'Aluminium', 'symbol': 'Al'},
    14: {   'mass': 28.0855, 'name': 'Silicon', 'symbol': 'Si'},
    15: {   'mass': 30.973759999999999, 'name': 'Phosphorus', 'symbol': 'P'},
    16: {   'mass': 32.066000000000003, 'name': 'Sulfur', 'symbol': 'S'},
    17: {   'mass': 35.4527, 'name': 'Chlorine', 'symbol': 'Cl'},
    18: {   'mass': 39.948, 'name': 'Argon', 'symbol': 'Ar'},
    19: {   'mass': 39.098300000000002, 'name': 'Potassium', 'symbol': 'K'},
    20: {   'mass': 40.078000000000003, 'name': 'Calcium', 'symbol': 'Ca'},
    21: {   'mass': 44.9559, 'name': 'Scandium', 'symbol': 'Sc'},
    22: {   'mass': 47.880000000000003, 'name': 'Titanium', 'symbol': 'Ti'},
    23: {   'mass': 50.941499999999998, 'name': 'Vanadium', 'symbol': 'V'},
    24: {   'mass': 51.996000000000002, 'name': 'Chromium', 'symbol': 'Cr'},
    25: {   'mass': 54.938000000000002, 'name': 'Manganese', 'symbol': 'Mn'},
    26: {   'mass': 55.847000000000001, 'name': 'Iron', 'symbol': 'Fe'},
    27: {   'mass': 58.933199999999999, 'name': 'Cobalt', 'symbol': 'Co'},
    28: {   'mass': 58.693399999999997, 'name': 'Nickel', 'symbol': 'Ni'},
    29: {   'mass': 63.545999999999999, 'name': 'Copper', 'symbol': 'Cu'},
    30: {   'mass': 65.390000000000001, 'name': 'Zinc', 'symbol': 'Zn'},
    31: {   'mass': 69.722999999999999, 'name': 'Gallium', 'symbol': 'Ga'},
    32: {   'mass': 72.609999999999999, 'name': 'Germanium', 'symbol': 'Ge'},
    33: {   'mass': 74.921599999999998, 'name': 'Arsenic', 'symbol': 'As'},
    34: {   'mass': 78.959999999999994, 'name': 'Selenium', 'symbol': 'Se'},
    35: {   'mass': 79.903999999999996, 'name': 'Bromine', 'symbol': 'Br'},
    36: {   'mass': 83.799999999999997, 'name': 'Krypton', 'symbol': 'Kr'},
    37: {   'mass': 85.467799999999997, 'name': 'Rubidium', 'symbol': 'Rb'},
    38: {   'mass': 87.620000000000005, 'name': 'Strontium', 'symbol': 'Sr'},
    39: {   'mass': 88.905900000000003, 'name': 'Yttrium', 'symbol': 'Y'},
    40: {   'mass': 91.224000000000004, 'name': 'Zirconium', 'symbol': 'Zr'},
    41: {   'mass': 92.906400000000005, 'name': 'Niobium', 'symbol': 'Nb'},
    42: {   'mass': 95.939999999999998, 'name': 'Molybdenum', 'symbol': 'Mo'},
    43: {   'mass': 98.0, 'name': 'Technetium', 'symbol': 'Tc'},
    44: {   'mass': 101.06999999999999, 'name': 'Ruthenium', 'symbol': 'Ru'},
    45: {   'mass': 102.9055, 'name': 'Rhodium', 'symbol': 'Rh'},
    46: {   'mass': 106.42, 'name': 'Palladium', 'symbol': 'Pd'},
    47: {   'mass': 107.86799999999999, 'name': 'Silver', 'symbol': 'Ag'},
    48: {   'mass': 112.41, 'name': 'Cadmium', 'symbol': 'Cd'},
    49: {   'mass': 114.81999999999999, 'name': 'Indium', 'symbol': 'In'},
    50: {   'mass': 118.70999999999999, 'name': 'Tin', 'symbol': 'Sn'},
    51: {   'mass': 121.75700000000001, 'name': 'Antimony', 'symbol': 'Sb'},
    52: {   'mass': 127.59999999999999, 'name': 'Tellurium', 'symbol': 'Te'},
    53: {   'mass': 126.9045, 'name': 'Iodine', 'symbol': 'I'},
    54: {   'mass': 131.28999999999999, 'name': 'Xenon', 'symbol': 'Xe'},
    55: {   'mass': 132.90539999999999, 'name': 'Caesium', 'symbol': 'Cs'},
    56: {   'mass': 137.33000000000001, 'name': 'Barium', 'symbol': 'Ba'},
    57: {   'mass': 138.90549999999999, 'name': 'Lanthanum', 'symbol': 'La'},
    58: {   'mass': 140.12, 'name': 'Cerium', 'symbol': 'Ce'},
    59: {   'mass': 140.90770000000001, 'name': 'Praseodymium', 'symbol': 'Pr'},
    60: {   'mass': 144.24000000000001, 'name': 'Neodymium', 'symbol': 'Nd'},
    61: {   'mass': 145.0, 'name': 'Promethium', 'symbol': 'Pm'},
    62: {   'mass': 150.36000000000001, 'name': 'Samarium', 'symbol': 'Sm'},
    63: {   'mass': 151.965, 'name': 'Europium', 'symbol': 'Eu'},
    64: {   'mass': 157.25, 'name': 'Gadolinium', 'symbol': 'Gd'},
    65: {   'mass': 158.92529999999999, 'name': 'Terbium', 'symbol': 'Tb'},
    66: {   'mass': 162.5, 'name': 'Dysprosium', 'symbol': 'Dy'},
    67: {   'mass': 164.93029999999999, 'name': 'Holmium', 'symbol': 'Ho'},
    68: {   'mass': 167.25999999999999, 'name': 'Erbium', 'symbol': 'Er'},
    69: {   'mass': 168.9342, 'name': 'Thulium', 'symbol': 'Tm'},
    70: {   'mass': 173.03999999999999, 'name': 'Ytterbium', 'symbol': 'Yb'},
    71: {   'mass': 174.96700000000001, 'name': 'Lutetium', 'symbol': 'Lu'},
    72: {   'mass': 178.49000000000001, 'name': 'Hafnium', 'symbol': 'Hf'},
    73: {   'mass': 180.9479, 'name': 'Tantalum', 'symbol': 'Ta'},
    74: {   'mass': 183.84999999999999, 'name': 'Tungsten', 'symbol': 'W'},
    75: {   'mass': 186.20699999999999, 'name': 'Rhenium', 'symbol': 'Re'},
    76: {   'mass': 190.19999999999999, 'name': 'Osmium', 'symbol': 'Os'},
    77: {   'mass': 192.22, 'name': 'Iridium', 'symbol': 'Ir'},
    78: {   'mass': 195.08000000000001, 'name': 'Platinum', 'symbol': 'Pt'},
    79: {   'mass': 196.9665, 'name': 'Gold', 'symbol': 'Au'},
    80: {   'mass': 200.59, 'name': 'Mercury', 'symbol': 'Hg'},
    81: {   'mass': 204.38300000000001, 'name': 'Thallium', 'symbol': 'Tl'},
    82: {   'mass': 207.19999999999999, 'name': 'Lead', 'symbol': 'Pb'},
    83: {   'mass': 208.9804, 'name': 'Bismuth', 'symbol': 'Bi'},
    84: {   'mass': 209.0, 'name': 'Polonium', 'symbol': 'Po'},
    85: {   'mass': 210.0, 'name': 'Astatine', 'symbol': 'At'},
    86: {   'mass': 222.0, 'name': 'Radon', 'symbol': 'Rn'},
    87: {   'mass': 223.0, 'name': 'Francium', 'symbol': 'Fr'},
    88: {   'mass': 226.02539999999999, 'name': 'Radium', 'symbol': 'Ra'},
    89: {   'mass': 227.0, 'name': 'Actinium', 'symbol': 'Ac'},
    90: {   'mass': 232.03809999999999, 'name': 'Thorium', 'symbol': 'Th'},
    91: {   'mass': 231.0359, 'name': 'Protactinium', 'symbol': 'Pa'},
    92: {   'mass': 238.029, 'name': 'Uranium', 'symbol': 'U'},
    93: {   'mass': 237.04820000000001, 'name': 'Neptunium', 'symbol': 'Np'},
    94: {   'mass': 244.0, 'name': 'Plutonium', 'symbol': 'Pu'},
    95: {   'mass': 243.0, 'name': 'Americium', 'symbol': 'Am'},
    96: {   'mass': 247.0, 'name': 'Curium', 'symbol': 'Cm'},
    97: {   'mass': 247.0, 'name': 'Berkelium', 'symbol': 'Bk'},
    98: {   'mass': 251.0, 'name': 'Californium', 'symbol': 'Cf'},
    99: {   'mass': 252.0, 'name': 'Einsteinium', 'symbol': 'Es'},
    100: {   'mass': 257.0, 'name': 'Fermium', 'symbol': 'Fm'},
    101: {   'mass': 258.0, 'name': 'Mendelevium', 'symbol': 'Md'},
    102: {   'mass': 259.0, 'name': 'Nobelium', 'symbol': 'No'},
    103: {   'mass': 262.0, 'name': 'Lawrencium', 'symbol': 'Lr'}
    }

_valid_symbols = tuple(i['symbol'] for i in elements.values())
_atomic_masses = {el['symbol']: el['mass'] for el in elements.values()}

def _has_ase():
    """
    Returns True if the ase module can be imported, False otherwise.
    """
    try:
        import ase
    except ImportError:
        return False
    return True


def _calc_cell_volume(cell):
    """
    Calculates the volume of a cell given the three lattice vectors.

    It is calculated as cell[0] . (cell[1] x cell[2]), where . represents
    a dot product and x a cross product.

    Args:
        cell: the cell vectors; the must be a 3x3 list of lists of floats,
            no checks are done.
    
    Returns:
        the cell volume.
    """
    # returns the volume of the primitive cell: |a1.(a2xa3)|
    a1 = cell[0]
    a2 = cell[1]
    a3 = cell[2]
    a_mid_0 = a2[1]*a3[2] - a2[2]*a3[1]
    a_mid_1 = a2[2]*a3[0] - a2[0]*a3[2]
    a_mid_2 = a2[0]*a3[1] - a2[1]*a3[0]
    return abs(a1[0]*a_mid_0 + a1[1]*a_mid_1 + a1[2]*a_mid_2)


def _create_symbols_tuple(symbols):
    """
    Returns a tuple with the symbols provided. If a string is provided,
    this is converted to a tuple with one single element.
    """
    if isinstance(symbols,basestring):
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
    elif isinstance(weights,numbers.Number):
        weights_tuple = (weights,)
    else:
        weights_tuple = tuple(float(i) for i in weights)
    return weights_tuple

def validate_weights_tuple(weights_tuple,threshold):
    """
    Raises ValueError if the weights_tuple is not valid.

    Args:
        weights_tuple: the tuple to validate. It must be a
            a tuple of floats (as created by :func:_create_weights_tuple).
        threshold:
            a float number used as a threshold to check that the sum 
            of the weights is <= 1.
    
    If the sum is less than one, it means that there are vacancies.
    Each element of the list must be >= 0, and the sum must be <= 1.
    """
    w_sum = sum(weights_tuple)
    if ( any(i < 0. for i in weights_tuple) or 
         (w_sum - 1. > threshold) ):
        raise ValueError("The weight list is not valid (each element "
                         "must be positive, and the sum must be <= 1).")

def is_valid_symbol(symbol):
    """
    Returns True if the symbol is a valid chemical symbol (with correct
    capitalization), False otherwise.

    Recognized symbols are for elements from hydrogen (Z=1) to lawrencium
    (Z=103).
    """
    return symbol in _valid_symbols

def validate_symbols_tuple(symbols_tuple):
    """
    Raises a ValueError if any symbol in the tuple is not a valid chemical
    symbols (with correct capitalization).

    Refer also to the documentation of :func:is_valid_symbol
    """
    if len(symbols_tuple) == 0:
        valid = False
    else:
        valid = all(is_valid_symbol(sym) for sym in symbols_tuple)
    if not valid:
        raise ValueError("At least one element of the symbol list has "
                         "not been recognized.")

def _is_ase_atoms(ase_atoms):
    """
    Check if the ase_atoms parameter is actually a ase.Atoms object.
    
    It requires that ase can be imported doing 'import ase'.
    
    TODO: Check if we want to try to import ase and do something reasonable depending on
    whether ase is there or not.
    """
    import ase
    return isinstance(ase_atoms, ase.Atoms)

class Structure(object):
    """
    This class contains the information about the 
    """
    def __init__(self,cell,pbc=None):
        """
        Initializes the structure with a given cell.
        
        Args:
            cell: It can be:
                1. the three real-space lattice vectors, in angstrom.
                cell[i] gives the three coordinates of the i-th vector,
                with i=0,1,2.
                2. an ase.atoms object, using the ASE python library.
                3. an aida 'raw structure' dictionary as saved in the database
            pbc: if we want periodic boundary conditions on each of the
                three real-space directions.
                If this variable is set, only case 1 of cell is accepted.
                Default: [True, True, True]
        """
        # Threshold used to check if the cell volume is not zero.
        self._volume_threshold = 1.e-6

        # Initial values
        self._sites = []
        self._cell = None
        self._pbc = None

        if pbc is not None:
            self.cell = cell
            self.pbc = pbc
        elif _is_ase_atoms(cell):
            # Read the ase structure
            import ase
            self.cell = cell.cell
            self.pbc = cell.pbc
            for atom in cell:
                self.appendSite(StructureSite(ase=atom))
        elif isinstance(cell,dict):
            try:
                self.cell = cell['cell']
            except (KeyError, ValueError):
                raise ValueError("Invalid 'cell' section in raw structure cell")
            
            try:
                self.pbc = cell['pbc']
            except (KeyError, ValueError):
                raise ValueError("Invalid 'pbc' section in raw structure cell")
                
            try:
                for site in cell['sites']:
                    s = StructureSite(raw=site)
                    self.appendSite(s)
            except (KeyError, ValueError) as e:
                raise ValueError("Invalid 'sites' section in raw structure cell. Error was: "
                                 "'{}'".format(e.message))

        else:
            self.cell = cell
            self.pbc = [True,True,True]
            
    def get_raw(self):
        """
        Return the raw version of the structure, mapped to a suitable dictionary. 

        This is the structure that is actually stored (after serialization) in the DB.
        
        Returns:
            a python dictionary with the structure.
        """
        return {
            'cell': self.cell,
            'pbc': self.pbc,
            'sites': [site.get_raw() for site in self.sites],
            }

    def get_ase(self):
        """
        Return a ASE object corresponding to this structure. Requires to be able to import ase.

        Note: If any site is an alloy or has vacancies, a ValueError is raised (from the
            site.get_ase() routine).
        """
        import ase
        asecell = ase.Atoms(cell=self.cell, pbc=self.pbc)
        for site in self.sites:
            asecell.append(site.get_ase())
        return asecell

    def get_raw_json(self):
        """
        Return a JSON-serialized version of the raw structure

        Returns:
            a string that contains the JSON-serialized python dictionary as given by
            get_raw().
        """
        import json
        raw = self.get_raw()
        return json.dumps(raw)

    def appendSite(self,site):
        """
        Append a site to the structure.

        Args:
            site: the site to append, must be a StructureSite object.
        """
        if not isinstance(site,StructureSite):
            raise ValueError("Can only append StructureSite objects")
        
        self._sites.append(site)

    def clearSites(self):
        """
        Removes all sites for the structure.
        """
        self._sites = []

    @property
    def sites(self):
        return self._sites
    
    @property
    def cell(self):
        return self._cell
    
    @cell.setter
    def cell(self,value):
        try:
            the_cell = tuple(tuple(float(c) for c in i) for i in value)
            if len(the_cell) != 3:
                raise ValueError
            if any(len(i) != 3 for i in the_cell):
                raise ValueError
        except (IndexError,ValueError,TypeError):
            raise ValueError("Cell must be a list of the three vectors, each "
                             "defined as a list of three coordinates.") 
        
        if abs(_calc_cell_volume(the_cell)) < self._volume_threshold:
            raise ValueError("The cell volume is zero. Invalid cell.")

        self._cell = the_cell

    @property
    def pbc(self):
        return self._pbc

    @pbc.setter
    def pbc(self,value):
        if isinstance(value,bool):
            the_pbc = (value,value,value)
        elif (hasattr(value,'__iter__')):
            # To manage numpy lists of bools, whose elements are of type numpy.bool_
            # and for which isinstance(i,bool) return False...
            if hasattr(value,'tolist'):
                the_value = value.tolist()
            else:
                the_value = value
            if all(isinstance(i,bool) for i in the_value):
                if len(the_value) == 3:
                    the_pbc = tuple(i for i in the_value)
                elif len(value) == 1:
                    the_pbc = (the_value[0],the_value[0],the_value[0])
                else:
                    raise ValueError("pbc length must be either one or three.")
            else:
                raise ValueError("pbc elements are not booleans.")
        else:
            raise ValueError("pbc must be a boolean or a list of three "
                             "booleans.", value)
        self._pbc = the_pbc

    def is_alloy(self):
        return any(s.is_alloy() for s in self._sites)

    def has_vacancies(self):
        return any(s.has_vacancies() for s in self._sites)

class StructureSite(object):
    """
    This class contains the information about a given site of the system.

    It can be a single atom, or an alloy, or even contain vacancies.
    """
    def __init__(self, **kwargs):
        """
        Create a site.

        Args:
           One can either pass:
               raw: the raw python dictionary that will be converted to a StructureSite object.
           Or alternatively the following parameters:
               position: the absolute position (three floats) in angstrom
               symbols: a single string for the symbol of this site, or a list
                   of symbol strings
               weights (optional): the weights for each atomic species of this site.
                  If only a single symbol is provided, then this value is
                  optional and the weight is set to 1.
               mass (optional): the mass for this site in atomic mass units. If not provided,
                   the mass is set by the self.reset_mass() function.
        """
        # Threshold to check if the sum is one or not
        self._sum_threshold = 1.e-6

        # Internal variables
        self._mass = None
        self._symbols = None
        self._weights = None

        # Logic to create the structure
        if 'raw' in kwargs:
            if len(kwargs) != 1:
                raise ValueError("If you pass 'raw', then you cannot pass any other "
                                 "parameter.")

            raw = kwargs['raw']
            try:
                self.position = raw['position']
            except KeyError:
                raise ValueError("No 'position' key in raw site data.")

            try:
                self.set_symbols_and_weights(raw['symbols'],raw['weights'])
            except KeyError:
                raise ValueError("You didn't specify either 'symbols' or 'weights' in the "
                                 "raw site data.")
            try:
                self.mass = raw['mass']
            except KeyError:
                raise ValueError("You didn't specify the site mass in the raw site data.")

        elif 'ase' in kwargs:
            if len(kwargs) != 1:
                raise ValueError("If you pass 'ase', then you cannot pass any other "
                                 "parameter.")
            aseatom = kwargs['ase']
            try:
                self.position = aseatom.position
                self.set_symbols_and_weights([aseatom.symbol],[1.])
                self.mass = aseatom.mass
            except AttributeError:
                raise ValueError("Error using the aseatom object. Are you sure it is a "
                                 "ase.atom.Atom object? [Introspection says it is "
                                 "{}]".format(str(type(aseatom))))

        else:
            if 'position' not in kwargs or 'symbols' not in kwargs:
                raise ValueError("Both 'position' and 'symbols' need to be specified (at least) "
                                 "to create a StructureSite object. Otherwise, pass a raw "
                                 "structure using the 'raw' parameter.")
            self.position = kwargs['position']
            weights = kwargs.get('weights',None)
            self.set_symbols_and_weights(kwargs['symbols'],weights)
            if 'mass' not in kwargs:
                self.reset_mass()
            else:
                self.mass = kwargs['mass']

    def get_raw(self):
        """
        Return the raw version of the structure, mapped to a suitable dictionary. 

        This is the format that is actually used to store each site of the structure in the DB.
        
        Returns:
            a python dictionary with the site.
        """
        return {
            'symbols': self.symbols,
            'weights': self.weights,
            'position': self.position,
            'mass': self.mass,
            }

    def get_ase(self):
        """
        Return a ase.Atom object for this site.

        Note: If any site is an alloy or has vacancies, a ValueError is raised (from the
            site.get_ase() routine).
        """
        import ase
        if self.is_alloy() or self.has_vacancies():
            raise ValueError("Cannot convert to ASE if the site is an alloy or has vacancies.")
        aseatom = ase.Atom(position=self.position, symbol=self.symbols[0], mass=self.mass)
        return aseatom

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
        
        if abs(w_sum) < self._sum_threshold:
            self._mass = None
            return
        
        normalized_weights = (i/w_sum for i in self._weights)
        element_masses = (_atomic_masses[sym] for sym in self._symbols)
        # Weighted mass
        self._mass = sum([i*j for i,j in zip(normalized_weights, element_masses)])

    @property
    def mass(self):
        """
        The mass of this site.
        """
        return self._mass

    @mass.setter
    def mass(self, value):
        the_mass = float(value)
        if the_mass <= 0:
            raise ValueError("The mass must be positive.")
        self._mass = the_mass

    @property
    def position(self):
        """
        Return the position of this site in absolute coordinates, 
        in angstrom.
        """
        return self._position

    @position.setter
    def position(self,value):
        """
        Set the position of this site in absolute coordinates, 
        in angstrom.
        """
        try:
            internal_pos = tuple(float(i) for i in value)
            if len(internal_pos) != 3:
                raise ValueError
        # value is not iterable or elements are not floats or len != 3
        except (ValueError,TypeError), e:
            raise ValueError("Wrong format for position, must be a list of "
                             "three float numbers.")
        self._position = internal_pos

    @property
    def weights(self):
        """
        Weights for this site. Refer also to
        :func:validate_symbols_tuple for the validation rules on the weights.
        """
        return self._weights

    @weights.setter
    def weights(self, value):
        """
        If value is a number, a single weight is used. Otherwise, a list or
        tuple of numbers is expected.
        None is also accepted, corresponding to the list [1.].
        """
        weights_tuple = _create_weights_tuple(value)

        if len(weights_list) != len(self._symbols):
            raise ValueError("Cannot change the number of weights. Use the "
                             "set_symbols_and_weights function instead.")
        validate_weight_tuple(weights_tuple,self._sum_threshold)

        self._weights = weights_tuple

    @property
    def symbols(self):
        """
        List of symbols for this site. If the site is a single atom,
        pass a list of one element only, or simply the string for that atom.
        For alloys, a list of elements.
        """
        return self._symbols
    
    @symbols.setter
    def symbols(self, value):
        """
        If value is a string, a single symbol is used. Otherwise, a list or
        tuple of strings is expected.

        I set a copy of the list, so to avoid that the content changes 
        after the value is set.
        """
        symbols_tuple = _create_symbols_tuple(symbols)
       
        if len(symbols_list) != len(self._weights):
            raise ValueError("Cannot change the number of symbols. Use the "
                             "set_symbols_and_weights function instead.")
        validate_symbols_tuple(symbols_tuple)

        self._symbols = symbols_tuple

    def set_symbols_and_weights(self,symbols,weights):
        """
        Set the chemical symbols and the weights for the site.
        """
        symbols_tuple = _create_symbols_tuple(symbols)
        weights_tuple = _create_weights_tuple(weights)
        if len(symbols_tuple) != len(weights_tuple):
            raise ValueError("The number of symbols and weights must coincide.")
        validate_symbols_tuple(symbols_tuple)
        validate_weights_tuple(weights_tuple,self._sum_threshold)
        self._symbols = symbols_tuple
        self._weights = weights_tuple

    def is_alloy(self):
        """
        Returns True if the site has more than one element (i.e., 
        len(self.symbols) != 1), False otherwise.
        """
        return len(self._symbols) != 1

    def has_vacancies(self):
        """
        Returns True if the sum of the weights is less than one.

        It uses the internal variable _sum_threshold as a threshold.
        """
        w_sum = sum(self._weights)
        return not(1. - w_sum < self._sum_threshold)

if __name__ == "__main__":
    import unittest
    
    class ValidSymbols(unittest.TestCase):
        """
        Tests the symbol validation.
        """
        def test_bad_symbol(self):
            """
            Should not accept a non-existing symbol.
            """
            with self.assertRaises(ValueError):
                validate_symbols_tuple(['Hxx'])
        
        def test_empty_list(self):
            """
            Should not accept an empty list
            """
            with self.assertRaises(ValueError):
                validate_symbols_tuple([])
        
        def test_valid_list(self):
            """
            Should not raise any error.
            """
            validate_symbols_tuple(['H','He'])

    class ValidWeights(unittest.TestCase):
        """
        Tests valid weight lists.
        """        
        def test_isnot_list(self):
            """
            Should not accept a non-list, non-number weight
            """
            with self.assertRaises(ValueError):
                a = StructureSite(position=(0.,0.,0.),symbols='Ba',weights='aaa')
        
        def test_empty_list(self):
            """
            Should not accept an empty list
            """
            with self.assertRaises(ValueError):
                a = StructureSite(position=(0.,0.,0.),symbols='Ba',weights=[])

        def test_symbol_weight_mismatch(self):
            """
            Should not accept a size mismatch of the symbols and weights
            list.
            """
            with self.assertRaises(ValueError):
                a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1.])

            with self.assertRaises(ValueError):
                a = StructureSite(position=(0.,0.,0.),symbols=['Ba'],weights=[0.1,0.2])

        def test_negative_value(self):
            """
            Should not accept a negative weight
            """
            with self.assertRaises(ValueError):
                a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[-0.1,0.3])

        def test_sum_greater_one(self):
            """
            Should not accept a sum of weights larger than one
            """
            with self.assertRaises(ValueError):
                a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[0.5,0.6])

        def test_sum_one(self):
            """
            Should accept a sum equal to one
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,2./3.])

        def test_sum_less_one(self):
            """
            Should accept a sum equal less than one
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,1./3.])
        
        def test_none(self):
            """
            Should accept None.
            """
            a = StructureSite(position=(0.,0.,0.),symbols='Ba',weights=None)


    class TestSite(unittest.TestCase):
        """
        Tests the creation of StructureSite objects and their methods.
        """
        def test_sum_one(self):
            """
            Should accept a sum equal to one
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,2./3.])
            self.assertTrue(a.is_alloy())
            self.assertFalse(a.has_vacancies())

        def test_sum_less_one(self):
            """
            Should accept a sum equal less than one
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,1./3.])
            self.assertTrue(a.is_alloy())
            self.assertTrue(a.has_vacancies())
        
        def test_simple(self):
            """
            Should recognize a simple element.
            """
            a = StructureSite(position=(0.,0.,0.),symbols='Ba',weights=None)
            self.assertFalse(a.is_alloy())
            self.assertFalse(a.has_vacancies())

            b = StructureSite(position=(0.,0.,0.),symbols='Ba',weights=1.)
            self.assertFalse(b.is_alloy())
            self.assertFalse(b.has_vacancies())

    class TestMasses(unittest.TestCase):
        """
        Tests the creation of StructureSite objects and their methods.
        """
        def test_auto_mass_one(self):
            """
            mass for elements with sum one
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,2./3.])
            self.assertAlmostEqual(a.mass, 
                                   (_atomic_masses['Ba'] + 
                                    2.* _atomic_masses['C'])/3.)

        def test_sum_less_one(self):
            """
            mass for elements with sum less than one
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,1./3.])
            self.assertAlmostEqual(a.mass, 
                                   (_atomic_masses['Ba'] + 
                                    _atomic_masses['C'])/2.)

        def test_sum_less_one(self):
            """
            mass for a single element
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba'])
            self.assertAlmostEqual(a.mass, 
                                   _atomic_masses['Ba'])
            
        def test_manual_mass(self):
            """
            mass set manually
            """
            a = StructureSite(position=(0.,0.,0.),symbols=['Ba','C'],weights=[1./3.,1./3.],
                              mass = 1000.)
            self.assertAlmostEqual(a.mass, 1000.)

    class TestStructureInit(unittest.TestCase):
        """
        Tests the creation of Structure objects (cell and pbc).
        """
        def test_cell_wrong_size_1(self):
            """
            Wrong cell size (not 3x3)
            """
            with self.assertRaises(ValueError):
                a = Structure(cell=((0.,0.,0.),))

        def test_cell_wrong_size_2(self):
            """
            Wrong cell size (not 3x3)
            """
            with self.assertRaises(ValueError):
                a = Structure(cell=((0.,0.,0.),(0.,0.,0.),(0.,0.)))

        def test_cell_zero_vector(self):
            """
            Wrong cell (one vector has zero length)
            """
            with self.assertRaises(ValueError):
                a = Structure(cell=((0.,0.,0.),(0.,1.,0.),(0.,0.,1.)))

        def test_cell_zero_volume(self):
            """
            Wrong cell (volume is zero)
            """
            with self.assertRaises(ValueError):
                a = Structure(cell=((1.,0.,0.),(0.,1.,0.),(1.,1.,0.)))

        def test_cell_ok(self):
            """
            Correct cell
            """
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            a = Structure(cell=cell)
            out_cell = a.cell
            
            for i in range(3):
                for j in range(3):
                    self.assertAlmostEqual(cell[i][j],out_cell[i][j])
        
        def test_volume(self):
            """
            Check the volume calculation
            """
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            self.assertAlmostEqual(_calc_cell_volume(cell), 6.)

            cell = ((1.,0.,0.),(0.,1.,0.),(1.,1.,0.))
            self.assertAlmostEqual(_calc_cell_volume(cell), 0.)


        def test_wrong_pbc_1(self):
            """
            Wrong pbc parameter (not bool or iterable)
            """
            with self.assertRaises(ValueError):
                cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
                a = Structure(cell=cell,pbc=1)

        def test_wrong_pbc_2(self):
            """
            Wrong pbc parameter (iterable but with wrong len)
            """
            with self.assertRaises(ValueError):
                cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
                a = Structure(cell=cell,pbc=[True,True])

        def test_wrong_pbc_3(self):
            """
            Wrong pbc parameter (iterable but with wrong len)
            """
            with self.assertRaises(ValueError):
                cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
                a = Structure(cell=cell,pbc=[])

        def test_ok_pbc_1(self):
            """
            Single pbc value
            """
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            a = Structure(cell=cell,pbc=True)
            self.assertEqual(a.pbc,tuple([True,True,True]))

            a = Structure(cell=cell,pbc=False)
            self.assertEqual(a.pbc,tuple([False,False,False]))

        def test_ok_pbc_2(self):
            """
            One-element list
            """
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            a = Structure(cell=cell,pbc=[True])
            self.assertEqual(a.pbc,tuple([True,True,True]))

            a = Structure(cell=cell,pbc=[False])
            self.assertEqual(a.pbc,tuple([False,False,False]))

        def test_ok_pbc_3(self):
            """
            Three-element list
            """
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            a = Structure(cell=cell,pbc=[True,False,True])
            self.assertEqual(a.pbc,tuple([True,False,True]))
            

    class TestStructure(unittest.TestCase):
        """
        Tests the creation of Structure objects (cell and pbc).
        """

        def test_cell_ok(self):
            """
            Test the creation of a cell and the appending of sites
            """
            cell = ((2.,0.,0.),(0.,2.,0.),(0.,0.,2.))
            a = Structure(cell=cell)
            out_cell = a.cell
            
            s = StructureSite(position=(0.,0.,0.),symbols=['Ba'])
            a.appendSite(s)
            s = StructureSite(position=(1.,1.,1.),symbols=['Ti'])
            a.appendSite(s)
            self.assertFalse(a.is_alloy())
            self.assertFalse(a.has_vacancies())

            s= StructureSite(position=(0.5,1.,1.5), symbols=['O', 'C'], 
                             weights=[0.5,0.5])
            a.appendSite(s)
            self.assertTrue(a.is_alloy())
            self.assertFalse(a.has_vacancies())

            s= StructureSite(position=(0.5,1.,1.5), symbols=['O'], weights=[0.5])
            a.appendSite(s)
            self.assertTrue(a.is_alloy())
            self.assertTrue(a.has_vacancies())

            a.clearSites()
            a.appendSite(s)
            self.assertFalse(a.is_alloy())
            self.assertTrue(a.has_vacancies())


    class TestRawStructure(unittest.TestCase):
        """
        Tests the creation of Structure, converting it to a raw structure and converting it back.
        """
        def test_to_from_raw(self):
            """
            Start from a Structure object, convert to raw and then back
            """
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            a = Structure(cell=cell)
            out_cell = a.cell
            
            a.pbc = [False,True,True]

            s = StructureSite(position=(0.,0.,0.),symbols=['Ba'])
            a.appendSite(s)
            s = StructureSite(position=(1.,1.,1.),symbols=['Ti'])
            a.appendSite(s)

            raw = a.get_raw()           
            b = Structure(raw)
            
            for i in range(3):
                for j in range(3):
                    self.assertAlmostEqual(cell[i][j], b.cell[i][j])
            
            self.assertEqual(b.pbc, (False,True,True))
            self.assertEqual(len(b.sites), 2)
            self.assertEqual(b.sites[0].symbols[0], 'Ba')
            self.assertEqual(b.sites[1].symbols[0], 'Ti')
            for i in range(3):
                self.assertAlmostEqual(b.sites[1].position[i], 1.)

    class TestAseStructure(unittest.TestCase):
        """
        Tests the creation of Structure from/to a ASE object.
        """
        @unittest.skipIf(not _has_ase(),"Unable to import ase")
        def test_ase(self):
            import ase
            a = ase.Atoms('SiGe',cell=(1.,2.,3.),pbc=(True,False,False))
            a.set_positions(
                ((0.,0.,0.),
                 (0.5,0.7,0.9),)
                )
            a[1].mass = 110.2

            b = Structure(a)
            c = b.get_ase()

            self.assertEqual(a[0].symbol, c[0].symbol)
            self.assertEqual(a[1].symbol, c[1].symbol)
            for i in range(3):
                self.assertAlmostEqual(a[0].position[i], c[0].position[i])
            for i in range(3):
                for j in range(3):
                    self.assertAlmostEqual(a.cell[i][j], c.cell[i][j])
               
            self.assertAlmostEqual(c[1].mass, 110.2)

    unittest.main()
