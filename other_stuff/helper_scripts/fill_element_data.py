"""
This script fills the Elements table with the minimum data needed.
To be used for the first fill (used then to generate the initial_data
fixture), or to update data in case of errors/corrections/...

Note: to be run from ./manage.py shell
"""
from aida.djsite.main.models import Element
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
for Z in range(1,104):
    if numpy.isnan(atomic_masses[Z]):
        mass = missing_masses[Z]
    else:
        mass = atomic_masses[Z]

    title = ase.data.chemical_symbols[Z]
    description = ase.data.atomic_names[Z]
    data = json.dumps({'mass': mass})

    ## Storing data in the database
    el = Element.objects.create(title=title,description=description,
                               data=data,Z=Z)
    el.save()
    

