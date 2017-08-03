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

UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')
RemoteData = DataFactory('remote')
KpointsData = DataFactory('array.kpoints')
# Used to make sure that the parent is a pw.x calculation
QEPwCalc = CalculationFactory('quantumespresso.pw') 
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
                     "a phonon codename")
    sys.exit(1)

queue = None
#queue = "P_share_queue"

#####

try:
    int(parent_id)
except ValueError:
    raise ValueError('Parent_id not an integer: {}'.format(parent_id))

code = test_and_get_code(codename, expected_code_type='quantumespresso.ph')

######

parameters = ParameterData(dict={
            'INPUTPH': {
                'tr2_ph' : 1.0e-8,
                #'epsil' : True,
                }})

qpoints = KpointsData()
qpoints.set_kpoints_mesh([1,1,1])
#qpoints.set_kpoints([[0.,0.,0.],[0.,0.,0.01]])
#qpoints.set_kpoints([[0.,0.1,0.]])

#    settings = ParameterData(dict={'PREPARE_FOR_D3':True})
settings=None

parentcalc = QEPwCalc.get_subclass_from_pk(parent_id)

calc = code.new_calc()
calc.label = "Test QE ph.x"
calc.description = "Test calculation with the Quantum ESPRESSO ph.x code"

calc.set_max_wallclock_seconds(30*60) # 30 min
calc.set_resources({"num_machines": 1})
if queue is not None:
    calc.set_queue_name(queue)

calc.use_parameters(parameters)
calc.use_parent_calculation(parentcalc)
calc.use_qpoints(qpoints)

if settings is not None:
    calc.use_settings(settings)

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
