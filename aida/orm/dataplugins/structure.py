"""
This module defines the classes for structures and all related
functions to operate on them.
"""

from aida.orm import Node
import itertools
import copy

# Threshold used to check if the mass of two different Site objects is the same.
_mass_threshold = 1.e-3
# Threshold to check if the sum is one or not
_sum_threshold = 1.e-6
# Threshold used to check if the cell volume is not zero.
_volume_threshold = 1.e-6

# Element table
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

def _get_valid_cell(inputcell):
    """
    Return the cell in a valid format from a generic input.

    Raise ValueError if the format is not valid.
    """
    try:
        the_cell = tuple(tuple(float(c) for c in i) for i in inputcell)
        if len(the_cell) != 3:
            raise ValueError
        if any(len(i) != 3 for i in the_cell):
            raise ValueError
    except (IndexError,ValueError,TypeError):
        raise ValueError("Cell must be a list of the three vectors, each "
                         "defined as a list of three coordinates.") 
    
    if abs(calc_cell_volume(the_cell)) < _volume_threshold:
        raise ValueError("The cell volume is zero. Invalid cell.")

    return the_cell

def _get_valid_pbc(inputpbc):
    """
    Return a list of three booleans for the periodic boundary conditions,
    in a valid format from a generic input.

    Raise ValueError if the format is not valid.
    """
    if isinstance(inputpbc,bool):
        the_pbc = (inputpbc,inputpbc,inputpbc)
    elif (hasattr(inputpbc,'__iter__')):
        # To manage numpy lists of bools, whose elements are of type numpy.bool_
        # and for which isinstance(i,bool) return False...
        if hasattr(inputpbc,'tolist'):
            the_value = inputpbc.tolist()
        else:
            the_value = inputpbc
        if all(isinstance(i,bool) for i in the_value):
            if len(the_value) == 3:
                the_pbc = tuple(i for i in the_value)
            elif len(the_value) == 1:
                the_pbc = (the_value[0],the_value[0],the_value[0])
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
    Returns True if the ase module can be imported, False otherwise.
    """
    try:
        import ase as _
    except ImportError:
        return False
    return True


def calc_cell_volume(cell):
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

def is_ase_atoms(ase_atoms):
    """
    Check if the ase_atoms parameter is actually a ase.Atoms object.
    
    It requires that ase can be imported doing 'import ase'.
    
    TODO: Check if we want to try to import ase and do something reasonable depending on
    whether ase is there or not.
    """
    import ase
    return isinstance(ase_atoms, ase.Atoms)

class StructureData(Node):
    """
    This class contains the information about a given structure, i.e. a
    collection of sites together with a cell, the 
    boundary conditions (whether they are periodic or not) and other
    related useful information.
    """
    def __init__(self,**kwargs):
        """
        Initializes the StructureData object with a given cell.
        
        Args:
            cell: It can be:
                1. the three real-space lattice vectors, in angstrom.
                cell[i] gives the three coordinates of the i-th vector,
                with i=0,1,2.
                Default: [[1,0,0],
                          [0,1,0],
                          [0,0,1]]
            pbc: if we want periodic boundary conditions on each of the
                three real-space directions.
                Default: [True, True, True]
            ase: a ase.atoms object, using the ASE python library. If this 
            parameter is passed, the one above cannot be specified.
        """
        super(StructureData,self).__init__(**kwargs)
        # Initial values
        # self._sites = []
        # self._cell = None
        # self._pbc = None

        uuid = kwargs.pop('uuid', None)
        if uuid is not None:
            return

        cell = kwargs.pop('cell',None)
        pbc = kwargs.pop('pbc',None)
        aseatoms = kwargs.pop('ase',None)

        if kwargs:
            raise ValueError("There are unrecognized flags passed to the constructor: {}".format(
                kwargs.keys()))

        self.set_attr('sites',[])
        if aseatoms is not None:
            if cell is not None or pbc is not None:
                raise ValueError("If you pass 'ase', you cannot pass also 'cell' or 'pbc'")
            if is_ase_atoms(aseatoms):
                # Read the ase structure
                self.cell = aseatoms.cell
                self.pbc = aseatoms.pbc
                for atom in aseatoms:
                    self.append_site(Site(ase=atom),reset_type_if_needed=True)
            else:
                raise ValueError('an ase flag was passed, but the value is not a ase.Atoms object')
        else:
            if pbc is not None:
                self.pbc = pbc
            else:
                self.pbc = [True, True, True]
            if cell is not None:
                self.cell = cell
            else:
                self.cell = [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]

    def validate(self):
        from aida.common.exceptions import ValidationError
        super(StructureData,self).validate()

        try:
            _get_valid_cell(self.cell)
        except ValueError as e:
            raise ValidationError("Invalid cell: {}".format(e.message))

        try:
            _get_valid_pbc(self.pbc)
        except ValueError as e:
            raise ValidationError("Invalid periodic boundary conditions: {}".format(e.message))

        try:
            # This will try to create the sites objects
            _ = self.sites
        except ValueError as e:
            raise ValidationError("Unable to validate the sites: {}".format(e.message))

#    def get_raw(self):
#        """
#        Return the raw version of the StructureData object, mapped to a suitable
#        dictionary. 
#
#        This is the structure that is actually stored (after serialization)
#        in the DB.
#        
#        Returns:
#            a python dictionary with the sites.
#        """
#        return {
#            'cell': self.cell,
#            'pbc': self.pbc,
#            'sites': [site.get_raw() for site in self.sites],
#            }

    def get_elements(self):
        """
        Return a list of elements, as obtained by reading all sites of the
        StructureData object, keeping all duplicates.
        """
        return list(itertools.chain.from_iterable(
                site.symbols for site in self.sites))

    def get_formula(self):
        """
        Return a string with a formula for the given element.
        
        TODO: implement it better! (like Si2 instead of SiSi, Si0.4Ge0.6 instead
        of SiGe, etc.)
        """
        return "".join(self.get_elements())

    def get_ase(self):
        """
        Return a ASE object corresponding to this StructureData object. Requires to be
        able to import ase.

        Note: If any site is an alloy or has vacancies, a ValueError is raised
        (from the site.get_ase() routine).
        """
        import ase
        asecell = ase.Atoms(cell=self.cell, pbc=self.pbc)
        for site in self.sites:
            asecell.append(site.get_ase())
        return asecell

    def get_types(self):
        """
        Return a list of types. Each type is a tuple, the first element is the
        type string, the second element is a list of the indices of the sites
        referring to this type.
        
        The second element should never be an empty list! At least an element
        should be present.
        """       
        positions = {}
        types = []
        
        # * positions is a dictionary that maps each type to a list, containing the positions of the sites
        #   in the self.sites list.
        # * types keeps track of the order in which the types were found
        for i, the_type in enumerate([site.type for site in self.sites]):
            if the_type in positions:
                positions[the_type].append(i)
            else:
                positions[the_type] = [i]
                types.append(the_type)

        # I return the final object
        final_list = [(the_type, positions[the_type]) for the_type in types]

        return final_list

    def append_site(self,site,reset_type_if_needed=False):
        """
        Append a site to the StructureData. It makes a copy of the site.

        Args:
            site: the site to append, must be a Site object.
            reset_type_if_needed: if False, an exception is raised if a site with same type but different
                properties (mass, symbols, weights, ...) is found.
                If True, and an atom with same type but different properties is found, all the sites
                already present in self.sites are checked to see if there is a site with the same properties.
                Then, the same type is set. Otherwise, a new type name is chosen adding a number to the site
                name such that the type is different from the existing ones.
        """
        from aida.common.exceptions import ModificationNotAllowed
        
        if not self._to_be_stored:
            raise ModificationNotAllowed("The StructureData object cannot be modified, "
                "it has already been stored")

        new_site = Site(site=site) # So we make a copy
        
        self._set_site_type(new_site, reset_type_if_needed=reset_type_if_needed)

        # If here, no exceptions have been raised, so I store. Note that the new_site.type value may 
        # have been changed by the previous function.
        # I join two lists. Do not use .append, that would work in-place
        self.set_attr('sites',self.get_attr('sites',[]) + [new_site.get_raw()])
        #self._sites.append(new_site) 

    def _set_site_type(self, new_site, reset_type_if_needed):
        """
        Check if the site can be added (i.e., if no other sites with the same type exist, or if
        they exist, then they are equal) and possibly sets its type.
        
        Args:
            new_site: the new site to check, must be a Site object.
            reset_type_if_needed: if False, an exception is raised if a site with same type but different
                properties (mass, symbols, weights, ...) is found.
                If True, and an atom with same type but different properties is found, all the sites
                already present in self.sites are checked to see if there is a site with the same properties.
                Then, the same type is set. Otherwise, a new type name is chosen adding a number to the site
                name such that the type is different from the existing ones.
        """
        from aida.common.exceptions import ModificationNotAllowed

        if not self._to_be_stored:
            raise ModificationNotAllowed("The StructureData object cannot be modified, "
                "it has already been stored")

        type_list = self.get_types()
        if type_list:
            types, positions = zip(*type_list)
        else:
            types = []
            positions = []

        if new_site.type not in types:
            # There is no element with this type, OK to insert
            return

        # I get the index of the type, and the
        # first atom of this type (there should always be at least one!)
        type_idx = types.index(new_site.type)
        site_idx = positions[type_idx][0] 
        
        # If it is of the same type, I am happy
        is_same_type, differences_str = new_site.compare_type(self.sites[site_idx])
        if is_same_type:
            return

        # If I am here, the type string is the same, but they are actually of different type!

        if not reset_type_if_needed:
            errstr = ("The site you are trying to insert is of type '{}'. However, another site already "
                      "exists with same type, but with different properties! ({})".format(
                         new_site.type, differences_str))
            raise ValueError(errstr)

        # I check if there is a atom of the same type
        for site in self.sites:
            is_same_type, _ = new_site.compare_type(site)
            if is_same_type:
                new_site.type = site.type
                return

        # If I am here, I didn't find any existing site which is of the same type
        existing_type_names = [the_type for the_type in types if the_type.startswith(new_site.type)]

        append_int = 1
        while True:
            new_typename = "{:s}{:d}".format(new_site.type, append_int) 
            if new_typename not in existing_type_names:
                break
            append_int += 1
        new_site.type = new_typename

    def clear_sites(self):
        """
        Removes all sites for the StructureData object.
        """
        from aida.common.exceptions import ModificationNotAllowed

        if not self._to_be_stored:
            raise ModificationNotAllowed("The StructureData object cannot be modified, "
                "it has already been stored")

        self.set_attr('sites', [])
        #_sites = []

    @property
    def sites(self):
        try:
            raw_sites = self.get_attr('sites')
        except AttributeError:
            raw_sites = []
        return [Site(raw=i) for i in raw_sites]
        #return copy.deepcopy(self._sites)
    
    @property
    def cell(self):
        #return copy.deepcopy(self._cell)
        return copy.deepcopy(self.get_attr('cell'))
    
    @cell.setter
    def cell(self,value):
        from aida.common.exceptions import ModificationNotAllowed

        if not self._to_be_stored:
            raise ModificationNotAllowed("The StructureData object cannot be modified, "
                "it has already been stored")

        the_cell = _get_valid_cell(value)

        #self._cell = the_cell
        self.set_attr('cell', the_cell)

    @property
    def pbc(self):
        """
        Return a tuple of three booleans, each one tells if there are periodic
        boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        #return copy.deepcopy(self._pbc)
        return (self.get_attr('pbc1'),self.get_attr('pbc2'),self.get_attr('pbc3'))

    @pbc.setter
    def pbc(self,value):
        from aida.common.exceptions import ModificationNotAllowed

        if not self._to_be_stored:
            raise ModificationNotAllowed("The StructureData object cannot be modified, "
                "it has already been stored")
        the_pbc = _get_valid_pbc(value)

        #self._pbc = the_pbc
        self.set_attr('pbc1',the_pbc[0])
        self.set_attr('pbc2',the_pbc[1])
        self.set_attr('pbc3',the_pbc[2])

    def is_alloy(self):
        return any(s.is_alloy() for s in self.sites)

    def has_vacancies(self):
        return any(s.has_vacancies() for s in self.sites)

    def get_cell_volume(self):
        """
        Return the cell volume in angstrom^3
        """
        return calc_cell_volume(self.cell)

class Site(object):
    """
    This class contains the information about a given site of the system.

    It can be a single atom, or an alloy, or even contain vacancies.
    """
    def __init__(self, **kwargs):
        """
        Create a site.

        Args:
           One can either pass:
               raw: the raw python dictionary that will be converted to a
               Site object.
               ase: an ase Atom object
               site: a Site object (to get a copy)
           Or alternatively the following parameters:
               position: the absolute position (three floats) in angstrom
               symbols: a single string for the symbol of this site, or a list
                   of symbol strings
               weights (optional): the weights for each atomic species of this site.
                  If only a single symbol is provided, then this value is
                  optional and the weight is set to 1.
               mass (optional): the mass for this site in atomic mass units. If not provided,
                   the mass is set by the self.reset_mass() function.
               type (optional): a string that uniquely identifies the Site type. Two sites with the
                   same 'type' string are treated as the same atom type (e.g. for symmetry detection, ...)
                   By default, it is set to a string with the symbols appended one to the other, without
                   spaces, in alphabetical order; if the site has a vacancy, a X is appended at the end too.
        """
        # Internal variables
        self._mass = None
        self._symbols = None
        self._weights = None
        self._type = None

        # Logic to create the site from the raw format
        if 'raw' in kwargs:
            if len(kwargs) != 1:
                raise ValueError("If you pass 'raw', then you cannot pass "
                                 "any other parameter.")

            raw = kwargs['raw']
            try:
                self.position = raw['position']
            except KeyError:
                raise ValueError("No 'position' key in raw site data.")

            try:
                self.set_symbols_and_weights(raw['symbols'],raw['weights'])
            except KeyError:
                raise ValueError("You didn't specify either 'symbols' or "
                    "'weights' in the raw site data.")
            try:
                self.mass = raw['mass']
            except KeyError:
                raise ValueError("You didn't specify the site mass in the "
                                 "raw site data.")

            try:
                self.type = raw['type']
            except KeyError:
                raise ValueError("You didn't specify the site type in the "
                                 "raw site data.")

        elif 'site' in kwargs:
            if len(kwargs) != 1:
                raise ValueError("If you pass 'site', then you cannot pass "
                                 "any other parameter.")
            oldsite = kwargs['site']

            try:
                self.position = oldsite.position
                self.set_symbols_and_weights(oldsite.symbols,oldsite.weights)
                self.mass = oldsite.mass
                self.type = oldsite.type
            except AttributeError:
                raise ValueError("Error using the Site object. Are you sure "
                    "it is a aida.common.classes.structure.Site object? [Introspection says it is "
                    "{}]".format(str(type(oldsite))))

        elif 'ase' in kwargs:
            aseatom = kwargs['ase']
            if len(kwargs) != 1:
                raise ValueError("If you pass 'ase', then you cannot pass any other parameter.")
            
            try:
                self.position = aseatom.position
                self.set_symbols_and_weights([aseatom.symbol],[1.])
                self.mass = aseatom.mass
                self.set_automatic_type()
            except AttributeError:
                raise ValueError("Error using the aseatom object. Are you sure "
                    "it is a ase.atom.Atom object? [Introspection says it is "
                    "{}]".format(str(type(aseatom))))

        else:
            if 'position' not in kwargs or 'symbols' not in kwargs:
                raise ValueError("Both 'position' and 'symbols' need to be "
                    "specified (at least) to create a Site object. Otherwise, "
                    "pass a raw site using the 'raw' parameter.")
            self.position = kwargs['position']
            weights = kwargs.get('weights',None)
            self.set_symbols_and_weights(kwargs['symbols'],weights)
            if 'mass' not in kwargs:
                self.reset_mass()
            else:
                self.mass = kwargs['mass']
            if 'type' not in kwargs:
                self.set_automatic_type()
            else:
                self.type = kwargs['type']

    def get_raw(self):
        """
        Return the raw version of the site, mapped to a suitable dictionary. 

        This is the format that is actually used to store each site of the 
        structure in the DB.
        
        Returns:
            a python dictionary with the site.
        """
        return {
            'symbols': self.symbols,
            'weights': self.weights,
            'position': self.position,
            'mass': self.mass,
            'type': self.type,
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
        
        if abs(w_sum) < _sum_threshold:
            self._mass = None
            return
        
        normalized_weights = (i/w_sum for i in self._weights)
        element_masses = (_atomic_masses[sym] for sym in self._symbols)
        # Weighted mass
        self._mass = sum([i*j for i,j in zip(normalized_weights, element_masses)])

    @property
    def type(self):
        """
        Return the type of this site (a string).
        
        The type of a site is used to decide whether two sites are identical (same mass, symbols,
        weights, ...) or not.
        """
        return self._type

    @type.setter
    def type(self, value):
        """
        Set the type of this site (a string).
        
        Note that if the weights or the symbols are changed, the type is overwritten with the
        automatic one.
        """
        self._type = str(value)

    def set_automatic_type(self):
        """
        Set the type to a string obtained with the symbols appended one after the other, without
        spaces, in alphabetical order; if the site has a vacancy, a X is appended at the end too.
        """
        sorted_symbol_list = list(set(self.symbols))
        sorted_symbol_list.sort() # In-place sort
        type_string = "".join(sorted_symbol_list)
        if self.has_vacancies():
            type_string += "X"
        
        self.type = type_string

    def compare_type(self, other_site):
        """
        Compare with another Site object to check if they are different.
        
        Note! This does NOT check the 'type' attribute. Instead, it compares (with reasonable thresholds,
        where applicable): the mass, and the list of symbols and of weights.

        Return:
            A tuple with two elements. The first one is True if the two sites are 'equivalent' (same mass,
                symbols and weights), False otherwise. The second element of the tuple is a string, 
                which is either None (if the first element was True), or contains a 'human-readable'
                description of the first difference encountered between the two sites.
        """
        # Check length of symbols
        if len(self.symbols) != len(other_site.symbols):
            return (False, "Different length of symbols list")
        
        # Check list of symbols
        for i in range(len(self.symbols)):
            if self.symbols[i] != other_site.symbols[i]:
                return (False, "Symbol at position {:d} are different ({} vs. {})".format(
                        i+1, self.symbols[i], other_site.symbols[i]))

        # Check weights (assuming length of weights and of symbols have same length, which should
        # always be true
        for i in range(len(self.weights)):
            if self.weights[i] != other_site.weights[i]:
                return (False, "Weight at position {:d} are different ({} vs. {})".format(
                        i+1, self.weights[i], other_site.weights[i]))
            

        # Check masses
        if abs(self.mass - other_site.mass) > _mass_threshold:
            return (False, "Masses are different ({} vs. {})".format(self.mass, other_site.mass))
    
        # If we got here, the two Site objects are similar enough to be considered of the same type
        return (True, None)
        

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
        return copy.deepcopy(self._position)

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

        Note that when the weights are changed, the type is automatically regenerated.
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
        self.set_automatic_type()

    @property
    def symbols(self):
        """
        List of symbols for this site. If the site is a single atom,
        pass a list of one element only, or simply the string for that atom.
        For alloys, a list of elements.

        Note that when the symbols are changed, the type is automatically regenerated.
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
        self.set_automatic_type()

    def set_symbols_and_weights(self,symbols,weights):
        """
        Set the chemical symbols and the weights for the site.

        Note that this function also resets the type to the automatically generated one.
        """
        symbols_tuple = _create_symbols_tuple(symbols)
        weights_tuple = _create_weights_tuple(weights)
        if len(symbols_tuple) != len(weights_tuple):
            raise ValueError("The number of symbols and weights must coincide.")
        validate_symbols_tuple(symbols_tuple)
        validate_weights_tuple(weights_tuple,_sum_threshold)
        self._symbols = symbols_tuple
        self._weights = weights_tuple
        self.set_automatic_type()

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
        return not(1. - w_sum < _sum_threshold)

