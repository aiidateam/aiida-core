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

# If True, load the pseudos from the family specified below
# Otherwise, use static files provided
auto_pseudos = False

queue = None
# queue = "Q_aries_free"
settings = None
#####

code = test_and_get_code(codename, expected_code_type='quantumespresso.pw')

alat = 4.  # angstrom
cell = [[alat, 0., 0., ],
        [0., alat, 0., ],
        [0., 0., alat, ],
]

# BaTiO3 cubic structure
s = StructureData(cell=cell)
s.append_atom(position=(0., 0., 0.), symbols=['Ba'])
s.append_atom(position=(alat / 2., alat / 2., alat / 2.), symbols=['Ti'])
s.append_atom(position=(alat / 2., alat / 2., 0.), symbols=['O'])
s.append_atom(position=(alat / 2., 0., alat / 2.), symbols=['O'])
s.append_atom(position=(0., alat / 2., alat / 2.), symbols=['O'])

elements = list(s.get_symbols_set())

if auto_pseudos:
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

max_seconds = 100

parameters = ParameterData(dict={
    'CONTROL': {
        'calculation': 'vc-relax',
        'restart_mode': 'from_scratch',
        'wf_collect': True,
        'max_seconds': max_seconds,
    },
    'SYSTEM': {
        'ecutwfc': 40.,
        'ecutrho': 320.,
    },
    'ELECTRONS': {
        'conv_thr': 1.e-10,
    }})

kpoints = KpointsData()
kpoints_mesh = 4
kpoints.set_kpoints_mesh([kpoints_mesh, kpoints_mesh, kpoints_mesh])

calc = code.new_calc()
calc.label = "Test QE pw.x"
calc.description = "Test vc-relax calculation with the Quantum ESPRESSO pw.x code"
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

if auto_pseudos:
    try:
        calc.use_pseudos_from_family(pseudo_family)
        print "Pseudos successfully loaded from family {}".format(pseudo_family)
    except NotExistent:
        print ("Pseudo or pseudo family not found. You may want to load the "
               "pseudo family, or set auto_pseudos to False.")
        raise
else:
    raw_pseudos = [
        ("Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ba', 'pbesol'),
        ("Ti.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF", 'Ti', 'pbesol'),
        ("O.pbesol-n-rrkjus_psl.0.1-tested-pslib030.UPF", 'O', 'pbesol')]

    pseudos_to_use = {}
    for fname, elem, pot_type in raw_pseudos:
        absname = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                os.pardir, "data", fname))
        pseudo, created = UpfData.get_or_create(
            absname, use_first=True)
        if created:
            print "Created the pseudo for {}".format(elem)
        else:
            print "Using the pseudo for {} from DB: {}".format(elem, pseudo.pk)
        pseudos_to_use[elem] = pseudo

    for k, v in pseudos_to_use.iteritems():
        calc.use_pseudo(v, kind=k)

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

