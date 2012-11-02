"""
This module defines the classes for structures and all related functions to
operate on them.
"""
import copy

_valid_symbols_list = (
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
    'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
    'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 
    'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
    'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
    'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
    'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
    'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm',
    'Md', 'No', 'Lr')

def is_valid_symbol(symbol):
    """
    Returns True if the symbol is a valid chemical symbol (with correct
    capitalization), False otherwise.

    Recognized symbols are for elements from hydrogen (Z=1) to lawrencium
    (Z=103).
    """
    return symbol in _valid_symbols_list

def is_valid_symbol_list(symbol_list):
    """
    Returns True if all symbols in the list are valid chemical symbols
    (with correct capitalization), False otherwise.

    It returns false also for a empty list.

    Refer also to the documentation of :func:is_valid_symbol
    """
    if len(symbol_list) == 0:
        return False
    else:
        return all(is_valid_symbol(sym) for sym in symbol_list)

class AidaStruct(object):
    pass

class AidaStructSite(object):
    def __init__(self, symbols,position,weights=None,mass=None):
        pass

    @property
    def symbols(self):
        """
        List of symbols for this site. If the site is a single atom,
        pass a list of one element only, or simply the string for that atom.
        For alloys, pass a list of elements.
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
        if isinstance(value,basestring):
            symbols_list = [value]
        else:
            symbols_list = value
        
        if not is_valid_symbol_list():
            raise ValueError("At least one element of the symbol list has"
                             "not been recognized.")
        if len(symbols_list) != len(_symbols):
            raise ValueError("Cannot change the number of symbols. Use the"
                             "set_symbols_and_weights function instead.")

        _symbols = copy.deepcopy(symbols_list)
        # TODO CONTINUE HERE

    def set_symbols_and_weights(self,symbols,weights):
        pass


if __name__ == "__main__":
    # TODO DEBUG PART, TO REMOVE
    print is_valid_symbol('H')
    print is_valid_symbol('He')
    print is_valid_symbol('Hsd')

    print '----------'

    print is_valid_symbol_list([])
    print is_valid_symbol_list(['H'])
    print is_valid_symbol_list(['H','HHH'])
    print is_valid_symbol_list(['H','He'])
    print is_valid_symbol_list(['Hxxx','HHH'])
