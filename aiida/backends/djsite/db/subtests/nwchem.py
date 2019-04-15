# -*- coding: utf-8 -*-
"""
Tests for the NWChem input plugins.
"""
import os
import tempfile

from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.orm.calculation.job.nwchem.nwcpymatgen import _prepare_pymatgen_dict
from aiida.orm.data.structure import has_ase, has_pymatgen, StructureData
from aiida.orm.data.cif import has_pycifrw
from django.utils import unittest

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."

class TestNwchem(AiidaTestCase):

    @unittest.skipIf((not has_ase()) or (not has_pymatgen()),
                      "Unable to import ASE and pymatgen")
    def test_1(self):
        from ase import Atoms

        par = {
            'directives': [
                ['set nwpw:minimizer', '2'],
                ['set nwpw:psi_nolattice', '.true.'],
                ['set includestress', '.true.']
            ],
            'geometry_options': [
                'units',
                'au',
                'center',
                'noautosym',
                'noautoz',
                'print'
            ],
            'memory_options': [],
            'symmetry_options': [],
            'tasks': [
                {
                    'alternate_directives': {
                        'driver': {'clear': '', 'maxiter': 40},
                        'nwpw': {'ewald_ncut': 8, 'simulation_cell': '\n  ngrid 16 16 16\n end'}
                    },
                    'basis_set': {},
                    'charge': 0,
                    'operation': 'optimize',
                    'spin_multiplicity': None,
                    'theory': 'pspw',
                    'theory_directives': {},
                    'title': None
                }
            ]
        }

        a = Atoms(['Si', 'Si', 'Si' ,'Si', 'C', 'C', 'C', 'C'],
                  cell=[8.277, 8.277, 8.277])
        a.set_scaled_positions([
            (-0.5, -0.5, -0.5),
            (0.0, 0.0, -0.5),
            (0.0, -0.5, 0.0),
            (-0.5, 0.0, 0.0),
            (-0.25, -0.25, -0.25),
            (0.25 ,0.25 ,-0.25),
            (0.25, -0.25, 0.25),
            (-0.25 ,0.25 ,0.25),
        ])
        s = StructureData(ase=a)

        self.assertEquals(_prepare_pymatgen_dict(par,s),
'''set nwpw:minimizer 2
set nwpw:psi_nolattice .true.
set includestress .true.
geometry units au center noautosym noautoz print
 Si -4.1385 -4.1385 -4.1385
 Si 0.0 0.0 -4.1385
 Si 0.0 -4.1385 0.0
 Si -4.1385 0.0 0.0
 C -2.06925 -2.06925 -2.06925
 C 2.06925 2.06925 -2.06925
 C 2.06925 -2.06925 2.06925
 C -2.06925 2.06925 2.06925
end

title "pspw optimize"
charge 0
basis

end
driver
 clear 
 maxiter 40
end
nwpw
 ewald_ncut 8
 simulation_cell 
  ngrid 16 16 16
 end
end
task pspw optimize
''')

        par['add_cell'] = True

        self.assertEquals(_prepare_pymatgen_dict(par,s),
'''set nwpw:minimizer 2
set nwpw:psi_nolattice .true.
set includestress .true.
geometry units au center noautosym noautoz print 
  system crystal
    lat_a 8.277
    lat_b 8.277
    lat_c 8.277
    alpha 90.0
    beta  90.0
    gamma 90.0
  end
 Si -0.5 -0.5 -0.5
 Si 0.0 0.0 -0.5
 Si 0.0 -0.5 0.0
 Si -0.5 0.0 0.0
 C -0.25 -0.25 -0.25
 C 0.25 0.25 -0.25
 C 0.25 -0.25 0.25
 C -0.25 0.25 0.25
end

title "pspw optimize"
charge 0
basis

end
driver
 clear 
 maxiter 40
end
nwpw
 ewald_ncut 8
 simulation_cell 
  ngrid 16 16 16
 end
end
task pspw optimize
''')
