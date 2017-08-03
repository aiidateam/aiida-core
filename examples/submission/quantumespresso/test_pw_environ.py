#!/usr/bin/env runaiida
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

from aiida.common.example_helpers import test_and_get_code

from aiida.common.exceptions import NotExistent

################################################################

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
KpointsData = DataFactory('array.kpoints')
StructureData = DataFactory('structure')
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

queue = None
# queue = "Q_aries_free"
settings = None
#####

code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')

alat =10.  # angstrom
cell = [[alat, 0., 0., ],
        [0., alat, 0., ],
        [0., 0., alat, ],
]

# H2) molecule
s = StructureData(cell=cell)
s.append_atom(position=(alat / 2. + 0.948, alat / 2. + 1.082, alat / 2. + 0.794), symbols=['O'])
s.append_atom(position=(alat / 2. + 1.822, alat / 2. + 0.647, alat / 2. + 0.794), symbols=['H'])
s.append_atom(position=(alat / 2. + 0.299, alat / 2. + 0.352, alat / 2. + 0.794), symbols=['H'])

elements = list(s.get_symbols_set())


valid_pseudo_groups = UpfData.get_upf_groups(filter_elements=elements)

try:
    pseudo_family = sys.argv[3]
except IndexError:
    print >> sys.stderr, "Error, auto_pseudos set to True. You therefore need to pass as second parameter"
    print >> sys.stderr, "the pseudo family name."
    print >> sys.stderr, "Valid UPF families are:"
    print >> sys.stderr, "\n".join("* {}".format(i.name) for i in valid_pseudo_groups)
    sys.exit(1)

try:
    UpfData.get_upf_group(pseudo_family)
except NotExistent:
    print >> sys.stderr, "auto_pseudos is set to True and pseudo_family='{}',".format(pseudo_family)
    print >> sys.stderr, "but no group with such a name found in the DB."
    print >> sys.stderr, "Valid UPF groups are:"
    print >> sys.stderr, ",".join(i.name for i in valid_pseudo_groups)
    sys.exit(1)

parameters = ParameterData(dict={
    'CONTROL': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
        'wf_collect': True,
        'tprnfor': True,
    },
    'SYSTEM': {
        'ecutwfc': 30.,
        'ecutrho': 300.,
        #'assume_isolated': 'makov-payne', # For the time-being makov-payne corrections do not work with ibrav=0
    },
    'ELECTRONS': {
        'conv_thr': 5.e-9,
        'diagonalization': 'cg',
        'electron_maxstep': 200,
    },
    })

# Add to the settings the ENVIRON input namelist
if settings is None:
   settings = {}
settings.update({'ENVIRON': { 
        'verbose': 0,
        'environ_thr': 0.1,
        'environ_type': 'water',
        'tolrhopol': 1.3e-11,
        'mixrhopol': 0.6,
        }})

kpoints = KpointsData()

# method mesh
kpoints_mesh = 1
kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])

## For remote codes, it is not necessary to manually set the computer,
## since it is set automatically by new_calc
#computer = code.get_remote_computer()
#calc = code.new_calc(computer=computer)

calc = code.new_calc()
calc.label = "Test QE pw.x interfaced with ENVIRON"
calc.description = "Test calculation with the Quantum ESPRESSO pw.x code"
calc.set_max_wallclock_seconds(5 * 60)  # 30 min
# Valid only for Slurm and PBS (using default values for the
# number_cpus_per_machine), change for SGE-like schedulers 
calc.set_resources({"num_machines": 1})
## Otherwise, to specify a given # of cpus per machine, uncomment the following:
# calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 8})

#calc.set_custom_scheduler_commands("#SBATCH --account=ch3")

if queue is not None:
    calc.set_queue_name(queue)

calc.use_structure(s)
calc.use_parameters(parameters)


try:
    calc.use_pseudos_from_family(pseudo_family)
    print "Pseudos successfully loaded from family {}".format(pseudo_family)
except NotExistent:
    print ("Pseudo or pseudo family not found. You may want to load the "
               "pseudo family.")
    raise


calc.use_kpoints(kpoints)

if settings is not None:
    calc.use_settings(ParameterData(dict=settings))
#from aiida.orm.data.remote import RemoteData
#calc.set_outdir(remotedata)


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
        calc.uuid, calc.dbnode.pk)
    calc.submit()
    print "submitted calculation; calc=Calculation(uuid='{}') # ID={}".format(
        calc.uuid, calc.dbnode.pk)

