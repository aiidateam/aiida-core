# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import sys
import os
from aiida.common.exceptions import NotExistent

################################################################

ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')
KpointsData = DataFactory('array.kpoints')

submit_test = False
codename = 'your aiida code label for serial ase'

queue = None
settings = None

code = Code.get(codename)
    
alat = 4. # angstrom
cell = [[alat, 0., 0.,],
        [0., alat, 0.,],
        [0., 0., alat,],
        ]

# a molecule of Ti and O
s = StructureData(cell=cell)
s.append_atom(position=(0.,0.,0.),symbols=['Ti'])
s.append_atom(position=(1.4, 0., 0.),symbols=['O'])

kpoints = KpointsData()
kpoints.set_kpoints_mesh([2,2,2])

parameters = ParameterData(
    dict={"calculator": {"name":"gpaw",
                         "args":{"mode":{"@function":"PW",
                                         "args":{"ecut":300},
                                     }}}, # Translates to "calculator = GPAW(mode=PW(ecut=300))"
          'atoms_getters':["temperature", # translate to "atoms.get_temperature()"
                           ["forces",{'apply_constraint':True}], # translate to "atoms.get_forces(apply_constraint=True)"
                           ["masses",{}], # translate to "atoms.get_masses()"
                           ],
          'calculator_getters':[["potential_energy",{}], # translate to "calculator.get_potential_energy()" 
                                "spin_polarized", # translate to "calculator.get_spin_polarized()"
                                ["stress",['atoms']], # translate to "calculator.get_stress(atoms)"
                                #["orbital_dos",['atoms', {'spin':0}] ], # this syntax would translate to 
                                                                         # "calculator.get_orbital_dos(atoms,spin=0)"
                                ],
          'optimizer':{'name':'QuasiNewton',    # optimizer = QuasiNewton(alpha=0.9)
                       "args": {'alpha':0.9},
                       'run_args':{"fmax":0.05} # optimizer.run(fmax=0.05)
                       },
          
          "pre_lines":["# This is a set",         # a set of lines to be placed in the executed script
                       "# of various pre-lines"], # right after the imports of modules, at the beginning
          
          "post_lines":["# This is a set",
                        "# of various post-lines"], # a set of lines to be placed in the executed script
                                                    # after the call to optimizers and calculators, before the storage of results
          
          "extra_imports":["os", # translate to "import os"
                           ["numpy","array"], # translate to "from numpy import array"
                           ["numpy","array","ar"], # translate to "from numpy import array as ar"
                           ],
          }
    )

settings = ParameterData(dict={"ADDITIONAL_RETRIEVE_LIST":["an_extra_file.txt"]})

calc = code.new_calc()
calc.label = "Test Gpaw"
calc.description = "Test calculation with the Gpaw code"
calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources({"num_machines": 1,"num_mpiprocs_per_machine":1})
calc.set_withmpi(False)

calc.use_structure(s)
calc.use_parameters(parameters)
calc.use_kpoints(kpoints)
calc.use_settings(settings)

if queue is not None:
    calc.set_queue_name(queue)

if submit_test:
    subfolder, script_filename = calc.submit_test()
    print "Test_submit for calculation (uuid='{}')".format(
        calc.uuid)
    print "Submit file in {}".format(os.path.join(
            os.path.relpath(subfolder.abspath),
            script_filename
            ))
else:
    calc.store_all()
    print "created calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid,calc.dbnode.pk)

