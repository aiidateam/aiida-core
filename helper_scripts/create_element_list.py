"""
This script creates a dictionary to fill the aidalib.structure element
dictionary.
"""
import ase
import numpy
import json

# Table of missing masses in ase
missing_masses={
    43 : 98.,
    61 : 145.,
    84 : 209.,
    85 : 210.,
    86 : 222.,
    87 : 223.,
    89 : 227.,
    94 : 244.,
    95 : 243.,
    96 : 247.,
    97 : 247.,
    98 : 251.,
    99 : 252.,
    100: 257.,
    101: 258.,
    102: 259.,
    103: 262.,
}


atomic_masses=ase.data.atomic_masses
# All elements from H(1) to Lr(103)
elements = {}
for Z in range(1,104):
    if numpy.isnan(atomic_masses[Z]):
        mass = missing_masses[Z]
    else:
        mass = atomic_masses[Z]

    symbol = ase.data.chemical_symbols[Z]
    name = ase.data.atomic_names[Z]
    elements[Z] = {
        'name': name,
        'symbol': symbol,
        'mass': mass,
        }

import pprint
pp=pprint.PrettyPrinter(indent=4)
pp.pprint(elements)

#_valid_symbols = tuple(i['symbol'] for i in elements.values())
#print _valid_symbols

    

