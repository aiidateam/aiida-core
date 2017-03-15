#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida import load_dbenv
load_dbenv()

from aiida.orm import Code, DataFactory
StructureData = DataFactory('structure')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')

###############################
# Set your values here
codename = 'pw-5.1@TheHive'
pseudo_family = 'lda_pslibrary'
###############################

code = Code.get_from_string(codename)

# BaTiO3 cubic structure
alat = 4. # angstrom
cell = [[alat, 0., 0.,],
        [0., alat, 0.,],
        [0., 0., alat,],
       ]
s = StructureData(cell=cell)
s.append_atom(position=(0.,0.,0.),symbols='Ba')
s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols='Ti')
s.append_atom(position=(alat/2.,alat/2.,0.),symbols='O')
s.append_atom(position=(alat/2.,0.,alat/2.),symbols='O')
s.append_atom(position=(0.,alat/2.,alat/2.),symbols='O')

parameters = ParameterData(dict={
          'CONTROL': {
              'calculation': 'scf',
              'restart_mode': 'from_scratch',
              'wf_collect': True,
              },
          'SYSTEM': {
              'ecutwfc': 30.,
              'ecutrho': 240.,
              },
          'ELECTRONS': {
              'conv_thr': 1.e-6,
              }})

kpoints = KpointsData()
kpoints.set_kpoints_mesh([4,4,4])

calc = code.new_calc(max_wallclock_seconds=3600,
    resources={"num_machines": 1})
calc.label = "A generic title"
calc.description = "A much longer description"

calc.use_structure(s)
calc.use_code(code)
calc.use_parameters(parameters)
calc.use_kpoints(kpoints)
calc.use_pseudos_from_family(pseudo_family)

calc.store_all()
print "created calculation with PK={}".format(calc.pk)
calc.submit()

