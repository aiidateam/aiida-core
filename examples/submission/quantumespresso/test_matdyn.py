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

import numpy

from aiida.common.example_helpers import test_and_get_code

################################################################
ParameterData = DataFactory('parameter')
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
    parent_id = sys.argv[2]
    codename = sys.argv[3]
except IndexError:
    print >> sys.stderr, ("Must provide as further parameters the parent ID and "
                     "a matdyn codename")
    sys.exit(1)

num_machines = 1 # node numbers
queue = None

#####
try:
    parent_id = int(parent_id)
except ValueError:
    print >> sys.stderr, 'Parent_id not an integer: {}'.format(parent_id)
    sys.exit(1)

code = test_and_get_code(codename, expected_code_type='quantumespresso.matdyn')

computer = code.get_remote_computer()

parameters = ParameterData(dict={
            'INPUT': {
                'asr': 'simple',
                },
            })

# additional settings specifying that we want to retrieve also the file with
# phonon displacements
settings = ParameterData(dict={
            'additional_retrieve_list': ['phonon_displacements.dat'],
            })

parentcalc = JobCalculation.get_subclass_from_pk(parent_id)

kpoints = KpointsData()
try:
    structure = parentcalc.inp.parent_calc_folder.inp.retrieved.inp.parent_calc_folder.inp.remote_folder.inp.structure
    kpoints.set_cell_from_structure(structure)
    kpoints.set_kpoints_path()
except AttributeError:
    kpoints.set_kpoints([[i,i,0] for i in numpy.linspace(0,1,10)])

calc = code.new_calc(computer=computer)
calc.label = "Test QE matdyn.x"
calc.description = "Test calculation with the Quantum ESPRESSO matdyn.x code"
calc.set_max_wallclock_seconds(60*30) # 30 min
calc.set_resources({"num_machines":num_machines})

calc.use_parameters(parameters)
calc.use_settings(settings) # additional settings (comment if you don't want to retrieve the phonon displacements file)
calc.use_kpoints(kpoints)
calc.use_parent_calculation(parentcalc)

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
