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

from aiida.common.exceptions import NotExistent

from aiida.common.example_helpers import test_and_get_code

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
    print >> sys.stderr, ("The second parameter is the codename")
    codename = None

queue = None
# queue = "Q_aries_free"
settings = None
#####

code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')

# Iron bcc crystal structure
from ase.lattice.spacegroup import crystal

a = 2.83265  # lattic parameter in Angstrom
Fe_ase = crystal('Fe', [(0, 0, 0)], spacegroup=229,
                 cellpar=[a, a, a, 90, 90, 90], primitive_cell=True)
s = StructureData(ase=Fe_ase).store()

elements = list(s.get_symbols_set())

valid_pseudo_groups = UpfData.get_upf_groups(filter_elements=elements)

try:
    pseudo_family = sys.argv[3]
except IndexError:
    print >> sys.stderr, "Error, you need to pass as third parameter"
    print >> sys.stderr, "the pseudo family name."
    print >> sys.stderr, "Valid UPF families are:"
    print >> sys.stderr, "\n".join("* {}".format(i.name) for i in valid_pseudo_groups)
    sys.exit(1)

try:
    UpfData.get_upf_group(pseudo_family)
except NotExistent:
    print >> sys.stderr, "pseudo_family='{}',".format(pseudo_family)
    print >> sys.stderr, "but no group with such a name found in the DB."
    print >> sys.stderr, "Valid UPF groups are:"
    print >> sys.stderr, ",".join(i.name for i in valid_pseudo_groups)
    sys.exit(1)

max_seconds = 1000

# parameters are adapted from D. Dragoni (but much less converged...)
parameters = ParameterData(dict={
    'CONTROL': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
        'wf_collect': True,
        'max_seconds': max_seconds,
        'tstress': True,
        'tprnfor': True,
    },
    'SYSTEM': {
        'ecutwfc': 50.,
        'ecutrho': 600.,
        'occupations': 'smearing',
        'smearing': 'marzari-vanderbilt',
        'degauss': 0.01,
        'nspin': 2,
        'starting_magnetization': {'Fe': 0.36},
        'nosym': True,
    },
    'ELECTRONS': {
        'electron_maxstep': 100,
        'mixing_beta': 0.2,
        'conv_thr': 1.e-10,
    }})

kpoints = KpointsData()
kpoints_mesh = 10
kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh],
                         offset=[0.5, 0.5, 0.5])

calc = code.new_calc()
calc.label = "Test QE pw.x"
calc.description = "Test calculation with the Quantum ESPRESSO pw.x code (magnetic material)"
calc.set_max_wallclock_seconds(max_seconds)
# Valid only for Slurm and PBS (using default values for the
# number_cpus_per_machine), change for SGE-like schedulers 
calc.set_resources({"num_machines": 1})
## Otherwise, to specify a given # of cpus per machine, uncomment the following:
# calc.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 8})

#calc.set_prepend_text("#SBATCH --account=ch3")

if queue is not None:
    calc.set_queue_name(queue)

calc.use_structure(s)
calc.use_parameters(parameters)

try:
    calc.use_pseudos_from_family(pseudo_family)
    print "Pseudos successfully loaded from family {}".format(pseudo_family)
except NotExistent:
    print ("Pseudo or pseudo family not found. You may want to load the "
           "pseudo family, or set auto_pseudos to False.")
    raise

calc.use_kpoints(kpoints)

if settings is not None:
    calc.use_settings(settings)
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

