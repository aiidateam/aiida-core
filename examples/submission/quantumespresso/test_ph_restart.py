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

# test phonon restart:
# do first a pw calculation (e.g. ./test_pw.py --send pw_codename)
# then use a first time this one with the previous pw calculation as parent:
# ./test_ph_restart.py --send pw_parent_calc_pk ph_codename
# and finally use it again with the first ph calculation as parent (no need to specify codename)
# ./test_ph_restart.py --send ph_parent_calc_pk

################################################################
UpfData = DataFactory('upf')
ParameterData = DataFactory('parameter')
StructureData = DataFactory('structure')
RemoteData = DataFactory('remote')
KpointsData = DataFactory('array.kpoints')

# Used to test the parent calculation
QEPwCalc = CalculationFactory('quantumespresso.pw') 
QEPhCalc = CalculationFactory('quantumespresso.ph') 

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
except IndexError:
    print >> sys.stderr, ("Must provide as second parameter the parent ID")
    sys.exit(1)


#####
# test parent

try:
    int(parent_id)
except ValueError:
    raise ValueError('Parent_id not an integer: {}'.format(parent_id))

parentcalc = Calculation.get_subclass_from_pk(parent_id)

queue = None
#queue = "P_share_queue"

#####

if isinstance(parentcalc,QEPwCalc):
    # parent is a pw calculation -> do a first phonon calculation
    try:
        codename = sys.argv[3]
    except IndexError:
        print >> sys.stderr, ("If parent is a pw calculation, must provide "
                              "as third parameter a phonon codename")
        sys.exit(1)

    code = test_and_get_code(codename, expected_code_type='quantumespresso.ph')
    
    parameters = ParameterData(dict={
                'INPUTPH': {
                    'max_seconds': 60,
                    'tr2_ph' : 1.0e-8,
                    'epsil' : True,
                    }})
    
    qpoints = KpointsData()
    qpoints.set_kpoints_mesh([2,2,2])
    
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

elif isinstance(parentcalc,QEPhCalc):

    # parent is a ph calculation -> do a restart phonon calculation
    if ( (parentcalc.get_state()=='FAILED') and
        ('Maximum CPU time exceeded' in parentcalc.res.warnings) ):
    
        calc = parentcalc.create_restart(force_restart=True)
        #calc.label = "Test QE ph.x restart"
        calc.description = "Test restart calculation with the Quantum ESPRESSO ph.x code"
    
    else:
        print >> sys.stderr, ("Parent calculation did not fail or did "
                              "not stop because of maximum CPU time limit.")
        sys.exit(1)
        

else:
    print >> sys.stderr, ("Parent calculation should be a pw.x or ph.x "
                          "calculation.")
    sys.exit(1)

######

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

