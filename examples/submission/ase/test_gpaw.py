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
try:
    dontsend = sys.argv[1]
    if dontsend == "--dont-send":
        submit_test = True
    elif dontsend == "--send":
        submit_test = False
    else:
        raise IndexError
except IndexError:
    print >> sys.stderr, ("The first parameter can only be either "
                          "--send or --dont-send")
    sys.exit(1)
    
try:
    codename = sys.argv[2]
except IndexError:
    codename = None

expected_code_type='asecalculators.gpaw'
    
queue = None
settings = None

try:
    if codename is None:
        raise ValueError
    code = Code.get(codename)
    if code.get_input_plugin_name() != expected_code_type:
        raise ValueError
except (NotExistent, ValueError):
    valid_code_labels = [c.label for c in Code.query(
            dbattributes__key="input_plugin",
            dbattributes__tval=expected_code_type)]
    if valid_code_labels:
        print >> sys.stderr, "Pass as further parameter a valid code label."
        print >> sys.stderr, "Valid labels with a {} executable are:".format(expected_code_type)
        for l in valid_code_labels:
            print >> sys.stderr, "*", l
    else:
        print >> sys.stderr, "Code not valid, and no valid codes for {}. Configure at least one first using".format(expected_code_type)
        print >> sys.stderr, "    verdi code setup"
    sys.exit(1)
    
alat = 4. # angstrom
cell = [[alat, 0., 0.,],
        [0., alat, 0.,],
        [0., 0., alat,],
        ]
    
# BaTiO3 cubic structure
s = StructureData(cell=cell)
s.append_atom(position=(0.,0.,0.),symbols=['Ba'])
s.append_atom(position=(alat/2.,alat/2.,alat/2.),symbols=['Ti'])
s.append_atom(position=(alat/2.,alat/2.,0.),symbols=['O'])
s.append_atom(position=(alat/2.,0.,alat/2.),symbols=['O'])
s.append_atom(position=(0.,alat/2.,alat/2.),symbols=['O'])

kpoints = KpointsData()
kpoints.set_kpoints_mesh([2,2,2])

parameters = ParameterData(
    dict={"calculator": {"name":"gpaw",
                         "args":{"mode":{"@function":"PW",
                                         "args":{"ecut":300}
                         }}},
          
          'atoms_getters':["temperature"],
          
          'calculator_getters':[["potential_energy",{}]],
          
          'optimizer':{'name':'QuasiNewton',
                       'args':{},
                       'run_args':{"fmax":0.05},
                       }})

calc = code.new_calc()
calc.label = "Test Gpaw"
calc.description = "Test calculation with the Gpaw code"
calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources({"num_machines": 1,"num_mpiprocs_per_machine":1})
calc.set_withmpi(False)

calc.use_structure(s)
calc.use_parameters(parameters)
calc.use_kpoints(kpoints)

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

